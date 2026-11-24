"""Prop placement on the CPU (WLD-12): turns data/world/placements.json into instances.

Coordinates: placements.json uses [east, north] offsets like layout.json; instances are in
game coordinates (x east, y up, z south). A prop's front faces +z in its own model space,
and 'facing' is the compass direction the front should look toward after placement.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from lycantrope.core.paths import DATA
from lycantrope.world.heightfield import Heightfield


@dataclass
class PropSpec:
    key: str
    name: str
    height: float
    color: tuple[float, float, float]
    top_color: tuple[float, float, float]
    top_from: float
    extents: tuple[float, float, float] = (1.0, 1.0, 1.0)   # filled in once the mesh is loaded


@dataclass
class Instances:
    """Per prop key: rows of (x, y, z, rotation_rad, scale, shade)."""
    rows: dict[str, list[tuple[float, ...]]] = field(default_factory=dict)

    def add(self, key: str, x: float, y: float, z: float, rot: float, scale: float, shade: float) -> None:
        self.rows.setdefault(key, []).append((x, y, z, rot, scale, shade))

    def arrays(self) -> dict[str, np.ndarray]:
        return {k: np.asarray(v, dtype=np.float32) for k, v in self.rows.items()}

    @property
    def count(self) -> int:
        return sum(len(v) for v in self.rows.values())


def load_catalog(path: Path = DATA / "props.json") -> dict[str, PropSpec]:
    raw = json.loads(path.read_text(encoding="utf-8"))["props"]
    out = {}
    for key, p in raw.items():
        color = tuple(p["color"])
        out[key] = PropSpec(key, p["name"], float(p["height_m"]), color,
                            tuple(p.get("top_color", color)), float(p.get("top_from", 2.0)))
    return out


def facing_to_rotation(facing_deg: float) -> float:
    """Model rotation about +y so that the model's +z front looks toward compass 'facing_deg'."""
    return math.pi - math.radians(facing_deg)


def rotate_xz(x: float, z: float, rot: float) -> tuple[float, float]:
    """Rotate a model-space (x, z) offset the same way the vertex shader does."""
    c, s = math.cos(rot), math.sin(rot)
    return x * c + z * s, -x * s + z * c


def ground_y(world: Heightfield, x: float, z: float, rot: float, half_x: float, half_z: float) -> float:
    """Lowest terrain height under a rotated footprint, so props never float."""
    hs = [world.height_at(x, z)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            dx, dz = rotate_xz(sx * half_x, sz * half_z, rot)
            hs.append(world.height_at(x + dx, z + dz))
    return min(hs)


class Placer:
    def __init__(self, world: Heightfield, catalog: dict[str, PropSpec]) -> None:
        self.world = world
        self.catalog = catalog
        self.out = Instances()
        self.taken: list[tuple[float, float, float]] = []      # (x, z, radius) of placed props
        self.anchors = {p.name: p for p in world.landmarks + world.waystones}

    # ------------------------------------------------------------------ #
    def place(self, key: str, x: float, z: float, rot: float, scale: float = 1.0,
              shade: float = 1.0, sink: float = 0.05) -> None:
        spec = self.catalog[key]
        ex, _ey, ez = spec.extents
        y = ground_y(self.world, x, z, rot, ex * scale / 2, ez * scale / 2) - sink * scale
        self.out.add(key, x, y, z, rot, scale, shade)
        self.taken.append((x, z, max(ex, ez) * scale / 2))

    def line(self, key: str, a: tuple[float, float], b: tuple[float, float],
             gate: str | None = None, gate_at: float = 0.5) -> None:
        """Repeat a prop (its length runs along model x) end to end from a to b (game x, z)."""
        dx, dz = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dz)
        if length < 1e-3:
            return
        rot = math.atan2(-dz, dx)                 # model +x -> direction a->b
        seg = self.catalog[key].extents[0] * 0.97
        spans = [(0.0, length)]
        if gate:
            g = self.catalog[gate].extents[0]
            mid = gate_at * length
            g0, g1 = max(0.0, mid - g / 2), min(length, mid + g / 2)
            self.place(gate, a[0] + dx * (g0 + g1) / 2 / length, a[1] + dz * (g0 + g1) / 2 / length, rot)
            spans = [(0.0, g0), (g1, length)]
        for s0, s1 in spans:
            n = max(1, round((s1 - s0) / seg)) if s1 - s0 > seg * 0.5 else 0
            if n == 0:
                continue
            for i in range(n):              # pieces overlap a little (seg is 97% of the length)
                t = (s0 + (i + 0.5) * (s1 - s0) / n) / length
                self.place(key, a[0] + dx * t, a[1] + dz * t, rot, shade=1.0 - 0.06 * (i % 2))

    def scatter(self, key: str, cx: float, cz: float, count: int, ring: tuple[float, float],
                seed: int, scale: tuple[float, float], spacing: float,
                groves: tuple[int, float] | None = None) -> None:
        """Random placement in a ring. With groves=(n, radius), props cluster around n
        random grove centers in the ring instead of spreading evenly."""
        rng = np.random.default_rng(seed)
        w = self.world

        def ring_point() -> tuple[float, float]:
            ang = rng.uniform(0, math.tau)
            r = math.sqrt(rng.uniform(ring[0] ** 2, ring[1] ** 2))
            return cx + r * math.cos(ang), cz + r * math.sin(ang)

        centers = [ring_point() for _ in range(int(groves[0]))] if groves else []
        placed, tries = 0, 0
        while placed < count and tries < count * 40:
            tries += 1
            if centers:
                gx, gz = centers[int(rng.integers(len(centers)))]
                x, z = gx + rng.normal(0, groves[1] / 2), gz + rng.normal(0, groves[1] / 2)
                if math.hypot(x - cx, z - cz) < ring[0]:
                    continue
            else:
                x, z = ring_point()
            if abs(x) > w.half - 5 or abs(z) > w.half - 5:
                continue
            c, rr = w._px(x, z)
            ci, ri = int(round(c)), int(round(rr))
            if not (0 <= ci < w.size and 0 <= ri < w.size) or w.road[ri, ci] > 20:
                continue
            h0 = w.height_at(x, z)
            if h0 < w.water_level + 0.5:
                continue
            slope = max(abs(w.height_at(x + 2, z) - h0), abs(w.height_at(x, z + 2) - h0)) / 2
            if slope > 0.45:
                continue
            s = float(rng.uniform(*scale))
            rad = max(self.catalog[key].extents[0], self.catalog[key].extents[2]) * s / 2
            if any((x - tx) ** 2 + (z - tz) ** 2 < (rad + tr + spacing * 0.5) ** 2 for tx, tz, tr in self.taken):
                continue
            self.place(key, x, z, float(rng.uniform(0, math.tau)), s, float(rng.uniform(0.85, 1.1)), sink=0.15)
            placed += 1

    # ------------------------------------------------------------------ #
    def run(self, placements: dict) -> Instances:
        for group in placements["groups"]:
            anchor = self.anchors.get(group["anchor"])
            if anchor is None:
                print(f"placements: unknown anchor {group['anchor']!r}")
                continue
            ax, az = anchor.x, anchor.z

            def pos(at):                                # [east, north] -> game (x, z)
                return ax + at[0], az - at[1]

            items = group["items"]
            # fixed items and lines first, so scatter keeps clear of them
            for it in sorted(items, key=lambda i: "scatter" in i):
                if "id" in it:
                    x, z = pos(it["at"])
                    self.place(it["id"], x, z, facing_to_rotation(it.get("facing", 180)),
                               float(it.get("scale", 1.0)))
                elif "line" in it:
                    self.line(it["line"], pos(it["from"]), pos(it["to"]), it.get("gate"),
                              float(it.get("gate_at", 0.5)))
                elif "scatter" in it:
                    self.scatter(it["scatter"], ax, az, int(it["count"]), tuple(it["ring"]),
                                 int(it.get("seed", 0)), tuple(it.get("scale", (1.0, 1.0))),
                                 float(it.get("spacing", 2.0)),
                                 tuple(it["groves"]) if "groves" in it else None)
        return self.out


def place_props(world: Heightfield, catalog: dict[str, PropSpec],
                path: Path = DATA / "world" / "placements.json") -> Instances:
    return Placer(world, catalog).run(json.loads(path.read_text(encoding="utf-8")))
