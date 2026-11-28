"""CPU-side checks for the terrain renderer (no OpenGL context needed)."""
import math

from pyglm import glm
import numpy as np
import pytest

from lycantrope.core.timing import FixedStep
from lycantrope.render.camera import Camera, boxes_in_frustum, frustum_planes
from lycantrope.render.terrain import grid_mesh
from lycantrope.world.heightfield import Heightfield


@pytest.fixture(scope="module")
def world():
    return Heightfield()


def test_grid_mesh_shape():
    verts, idx = grid_mesh(8)
    n = 8 + 3
    assert verts.shape == (n * n, 3)
    assert idx.max() < len(verts) and len(idx) == (n - 1) ** 2 * 6
    assert verts[:, :2].min() == 0.0 and verts[:, :2].max() == 1.0
    assert verts[:, 2].sum() == 4 * (n - 1)            # skirt ring vertex count


def test_frustum_culls_behind_camera():
    cam = Camera(position=(0, 10, 0), yaw=0.0, pitch=0.0)     # looking north (-z)
    *_, vp = cam.matrices(16 / 9)
    planes = frustum_planes(vp)
    bmin = np.array([[-5, 0, -60], [-5, 0, 50]], np.float32)  # one ahead, one behind
    bmax = bmin + 10
    assert boxes_in_frustum(planes, bmin, bmax).tolist() == [True, False]


def test_camera_yaw_convention():
    cam = Camera(yaw=math.pi / 2)
    f = cam.forward()
    assert f.x == pytest.approx(1.0) and abs(f.z) < 1e-6      # +90° yaw looks east


def test_fixed_step():
    clock = FixedStep(60)
    assert clock.advance(1 / 30) == 2
    assert clock.advance(0.004) == 0 and 0 < clock.alpha < 1
    assert clock.advance(10.0) == clock.max_steps              # no spiral of death


def test_heightfield_matches_generator(world):
    for w in world.waystones:
        assert world.height_at(w.x, w.z) == pytest.approx(w.height, abs=0.5)
    assert world.biome_at(world.waystones[0].x, world.waystones[0].z) == "Brackenvale"


def test_chunk_bounds_cover_map(world):
    origins, hmin, hmax = world.chunk_bounds(64.0)
    assert len(origins) == (world.size // 64) ** 2
    assert (hmax > hmin).all()
    assert origins[:, 0].min() == -world.half


def test_joint_names_from_other_riggers_map_to_the_meshy_names():
    from lycantrope.render.gltf import canon_joint
    assert canon_joint("mixamorig:LeftHand") == "LeftHand"
    assert canon_joint("mixamorig:Neck") == "neck" and canon_joint("Spine1") == "Spine01"
    for meshy in ("Hips", "Spine02", "neck", "Head", "head_end", "LeftForeArm", "RightToeBase"):
        assert canon_joint(meshy) == meshy                    # Meshy rigs are untouched
    assert canon_joint(None) == ""


def test_finger_bones_fold_into_the_hand():
    from lycantrope.render.gltf import joint_remap
    names = ["Hips", "LeftHand", "LeftHandIndex1", "LeftHandThumb2", "RightHand", "RightHandPinky4", "Head"]
    keep, remap = joint_remap(names)
    assert [names[i] for i in keep] == ["Hips", "LeftHand", "RightHand", "Head"]
    assert list(remap) == [0, 1, 1, 1, 2, 2, 3]
    meshy = ["Hips", "Spine02", "LeftHand", "RightHand"]
    assert joint_remap(meshy)[0] == [0, 1, 2, 3]               # no fingers: nothing changes
