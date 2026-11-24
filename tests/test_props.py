"""Prop placement math and GLB loading (no GPU needed)."""
import math

import numpy as np
import pytest

from lycantrope.world.props import PropSpec, Placer, facing_to_rotation, rotate_xz


def front_after(facing_deg: float) -> tuple[float, float]:
    """Where the model's +z front points (game x, z) after placement."""
    return rotate_xz(0.0, 1.0, facing_to_rotation(facing_deg))


@pytest.mark.parametrize("facing, expect", [(0, (0, -1)), (90, (1, 0)), (180, (0, 1)), (270, (-1, 0))])
def test_facing_is_compass_direction(facing, expect):
    x, z = front_after(facing)
    assert x == pytest.approx(expect[0], abs=1e-9) and z == pytest.approx(expect[1], abs=1e-9)


class FlatWorld:
    """Just enough of Heightfield for the placer."""
    half, size, mpp, water_level = 500.0, 1000, 1.0, 0.0
    road = np.zeros((1000, 1000), dtype=np.uint8)
    landmarks, waystones = [], []

    def height_at(self, x, z):
        return 10.0

    def _px(self, x, z):
        return x + self.half, z + self.half


def catalog():
    fence = PropSpec("F", "Fence", 1.0, (1, 1, 1), (1, 1, 1), 2.0, extents=(2.0, 1.0, 0.3))
    gate = PropSpec("G", "Gate", 1.0, (1, 1, 1), (1, 1, 1), 2.0, extents=(4.0, 1.0, 0.3))
    return {"F": fence, "G": gate}


def test_line_runs_along_segment_and_leaves_room_for_gate():
    p = Placer(FlatWorld(), catalog())
    p.line("F", (0.0, 0.0), (20.0, 0.0), gate="G", gate_at=0.5)
    fences = np.array(p.out.rows["F"])
    gates = np.array(p.out.rows["G"])
    assert len(gates) == 1 and gates[0, 0] == pytest.approx(10.0)
    assert np.all(np.abs(fences[:, 2]) < 1e-6)                  # all on the line z = 0
    assert not np.any((fences[:, 0] > 8.5) & (fences[:, 0] < 11.5))   # gap where the gate is
    # model +x lines up with the segment direction
    x, z = rotate_xz(1.0, 0.0, fences[0, 3])
    assert (x, z) == pytest.approx((1.0, 0.0), abs=1e-9)
    assert fences[0, 1] == pytest.approx(10.0 - 0.05)           # sits on the ground, slightly sunk


def test_scatter_keeps_its_distance():
    cat = catalog()
    p = Placer(FlatWorld(), cat)
    p.scatter("F", 0.0, 0.0, count=30, ring=(10.0, 60.0), seed=1, scale=(1.0, 1.0), spacing=2.0)
    pts = np.array(p.out.rows["F"])[:, [0, 2]]
    assert len(pts) == 30
    r = np.hypot(pts[:, 0], pts[:, 1])
    assert r.min() >= 10.0 - 1e-6 and r.max() <= 60.0 + 1e-6
    d = np.linalg.norm(pts[:, None] - pts[None], axis=2) + np.eye(len(pts)) * 1e9
    assert d.min() > 2.0


def test_read_glb_roundtrip(tmp_path):
    trimesh = pytest.importorskip("trimesh")
    from lycantrope.render.props import flat_mesh, read_glb
    box = trimesh.creation.box((2.0, 1.0, 3.0))
    path = tmp_path / "box.glb"
    box.export(path)
    v, f = read_glb(path)
    assert len(f) == 12
    assert np.allclose(v.max(axis=0) - v.min(axis=0), (2.0, 1.0, 3.0))
    rows = flat_mesh(v, f)
    assert rows.shape == (36, 6)
    assert np.allclose(np.linalg.norm(rows[:, 3:], axis=1), 1.0)
    assert math.isfinite(float(rows.sum()))
