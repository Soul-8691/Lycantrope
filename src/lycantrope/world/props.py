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
    """Per prop key: rows of (x, y, z, rotation_rad, scale, shade, stretch).

    stretch multiplies the height only, so one model also comes out taller/slimmer or squatter."""
    rows: dict[str, list[tuple[float, ...]]] = field(default_factory=dict)

    def add(self, key: str, x: float, y: float, z: float, rot: float, scale: float, shade: float,
            stretch: float = 1.0) -> None:
        self.rows.setdefault(key, []).append((x, y, z, rot, scale, shade, stretch))

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


GRID_M = 16.0           # cell size for the "is this spot taken?" lookup


PATH_CORE = 110         # road map value (0-255) counted as "on the path"


class Placer:
    def __init__(self, world: Heightfield, catalog: dict[str, PropSpec]) -> None:
        self.world = world
        self.catalog = catalog
        self.out = Instances()
        self.taken: list[tuple[float, float, float]] = []      # (x, z, radius) of placed props
        self._grid: dict[tuple[int, int], list[tuple[float, float, float]]] = {}   # the same, by 16 m cell
        self._max_r = 0.0
        self.anchors = {p.name: p for p in world.landmarks + world.waystones}
        self.missing: set[str] = set()
        self.blocked_by_path: list[tuple[str, float, float]] = []

    # ------------------------------------------------------------------ #
    def footprint(self, key: str, scale: float) -> float:
        """Radius of what actually sits on the ground: a trunk for trees, the base for the rest."""
        ex, _ey, ez = self.catalog[key].extents
        k = 0.1 if key.startswith("TRE") else 0.35
        return max(ex, ez) * scale * k

    def on_path(self, x: float, z: float, r: float) -> bool:
        """Does a circle of radius r at (x, z) touch a path or road (its well-trodden middle)?"""
        w = self.world
        if not hasattr(w, "road"):
            return False
        for dx, dz in ((0, 0), (r, 0), (-r, 0), (0, r), (0, -r), (0.7 * r, 0.7 * r), (-0.7 * r, 0.7 * r),
                       (0.7 * r, -0.7 * r), (-0.7 * r, -0.7 * r)):
            c, rr = w._px(x + dx, z + dz)
            ci, ri = int(round(c)), int(round(rr))
            if 0 <= ci < w.size and 0 <= ri < w.size and w.road[ri, ci] > PATH_CORE:
                return True
        return False

    def place(self, key: str, x: float, z: float, rot: float, scale: float = 1.0,
              shade: float = 1.0, sink: float = 0.05, stretch: float = 1.0, path_ok: bool = False) -> bool:
        """Place a prop; returns False (and places nothing) if it would sit on a path."""
        if not path_ok and self.on_path(x, z, self.footprint(key, scale)):
            self.blocked_by_path.append((key, round(x, 1), round(z, 1)))
            return False
        spec = self.catalog[key]
        ex, _ey, ez = spec.extents
        y = ground_y(self.world, x, z, rot, ex * scale / 2, ez * scale / 2) - sink * scale
        self.out.add(key, x, y, z, rot, scale, shade, stretch)
        r = max(ex, ez) * scale / 2
        self.taken.append((x, z, r))
        self._grid.setdefault((int(x // GRID_M), int(z // GRID_M)), []).append((x, z, r))
        self._max_r = max(self._max_r, r)
        return True

    def blocked(self, x: float, z: float, rad: float, spacing: float) -> bool:
        """Is there already a prop within rad + its radius + spacing/2 of (x, z)?"""
        reach = rad + self._max_r + spacing * 0.5
        n = int(reach // GRID_M) + 1
        cx, cz = int(x // GRID_M), int(z // GRID_M)
        for gx in range(cx - n, cx + n + 1):
            for gz in range(cz - n, cz + n + 1):
                for tx, tz, tr in self._grid.get((gx, gz), ()):
                    if (x - tx) ** 2 + (z - tz) ** 2 < (rad + tr + spacing * 0.5) ** 2:
                        return True
        return False

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
            self.place(gate, a[0] + dx * (g0 + g1) / 2 / length, a[1] + dz * (g0 + g1) / 2 / length, rot,
                       path_ok=True)
            spans = [(0.0, g0), (g1, length)]
        for s0, s1 in spans:
            n = max(1, round((s1 - s0) / seg)) if s1 - s0 > seg * 0.5 else 0
            if n == 0:
                continue
            for i in range(n):              # pieces overlap a little (seg is 97% of the length)
                t = (s0 + (i + 0.5) * (s1 - s0) / n) / length
                self.place(key, a[0] + dx * t, a[1] + dz * t, rot, shade=1.0 - 0.06 * (i % 2))

    def scatter(self, key: str | list[str], cx: float, cz: float, count: int, ring: tuple[float, float],
                seed: int, scale: tuple[float, float], spacing: float,
                groves: tuple[int, float] | None = None,
                stretch: tuple[float, float] = (1.0, 1.0)) -> None:
        """Random placement in a ring. With groves=(n, radius), props cluster around n
        random grove centers in the ring instead of spreading evenly. A list of keys mixes
        those props (each placement picks one at random)."""
        keys = [k for k in ([key] if isinstance(key, str) else key) if k in self.catalog]
        if not keys:
            return
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
            if h0 < getattr(w, "water_at", lambda _x, _z: w.water_level)(x, z) + 0.5:
                continue                                # not in the sea, lakes or rivers
            slope = max(abs(w.height_at(x + 2, z) - h0), abs(w.height_at(x, z + 2) - h0)) / 2
            if slope > 0.45:
                continue
            s = float(rng.uniform(*scale))
            key = keys[int(rng.integers(len(keys)))]
            rad = max(self.catalog[key].extents[0], self.catalog[key].extents[2]) * s / 2
            if self.blocked(x, z, rad, spacing):
                continue
            if self.on_path(x, z, self.footprint(key, s)):
                continue
            self.place(key, x, z, float(rng.uniform(0, math.tau)), s, float(rng.uniform(0.85, 1.1)), sink=0.15,
                       stretch=float(rng.uniform(*stretch)))
            placed += 1

    def shore(self, key: str | list[str], cx: float, cz: float, radius: float, count: int, seed: int,
              scale: tuple[float, float], spacing: float, stretch: tuple[float, float] = (1.0, 1.0),
              reach_m: float = 4.0) -> None:
        """Scatter props along rivers and lakes: dry ground within reach_m of the water, plus the
        shallows (under 0.4 m deep). Sea shores are skipped."""
        keys = [k for k in ([key] if isinstance(key, str) else key) if k in self.catalog]
        w = self.world
        if not keys or not hasattr(w, "water_surface"):
            return
        mpp, half = w.mpp, w.half
        c0, c1 = (max(0, int((v + half) / mpp)) for v in (cx - radius, cx + radius))
        r0, r1 = (max(0, int((v + half) / mpp)) for v in (cz - radius, cz + radius))
        c1, r1 = min(c1, w.size), min(r1, w.size)
        surf, ground = w.water_surface[r0:r1, c0:c1], w.heights[r0:r1, c0:c1]
        depth = surf - ground
        inland = surf > w.water_level + 0.3                  # rivers and lakes, not the sea
        wet = (depth > 0.1) & inland
        k = max(1, int(round(reach_m / mpp)))
        near = wet.copy()                                     # grow the water outward by reach_m
        for d in range(1, k + 1):
            near[d:] |= wet[:-d]
            near[:-d] |= wet[d:]
        grown = near.copy()
        for d in range(1, k + 1):
            near[:, d:] |= grown[:, :-d]
            near[:, :-d] |= grown[:, d:]
        cand = near & ((depth < 0.4) | ~wet)
        rows, cols = np.nonzero(cand)
        if len(rows) == 0:
            return
        xs = (cols + c0 + 0.5) * mpp - half
        zs = (rows + r0 + 0.5) * mpp - half
        inside = np.hypot(xs - cx, zs - cz) <= radius
        xs, zs = xs[inside], zs[inside]
        rng = np.random.default_rng(seed)
        order = rng.permutation(len(xs))
        placed = 0
        for i in order:
            if placed >= count:
                break
            x, z = float(xs[i] + rng.uniform(-0.5, 0.5) * mpp), float(zs[i] + rng.uniform(-0.5, 0.5) * mpp)
            s = float(rng.uniform(*scale))
            kk = keys[int(rng.integers(len(keys)))]
            rad = max(self.catalog[kk].extents[0], self.catalog[kk].extents[2]) * s / 2
            if self.blocked(x, z, rad, spacing):
                continue
            if self.on_path(x, z, self.footprint(kk, s)):
                continue
            self.place(kk, x, z, float(rng.uniform(0, math.tau)), s, float(rng.uniform(0.85, 1.1)),
                       sink=0.2, stretch=float(rng.uniform(*stretch)))
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
            for it in sorted(items, key=lambda i: "scatter" in i or "shore" in i):
                ref = it.get("id") or it.get("line")
                if ref is not None and ref not in self.catalog:
                    self.missing.add(ref)               # not generated/built yet: skip quietly
                    continue
                if "gate" in it and it["gate"] not in self.catalog:
                    self.missing.add(it["gate"])
                    it = {k: v for k, v in it.items() if k != "gate"}
                if "shore" in it:
                    self.shore(it["shore"], ax, az, float(it["radius"]), int(it["count"]), int(it.get("seed", 0)),
                               tuple(it.get("scale", (1.0, 1.0))), float(it.get("spacing", 2.0)),
                               tuple(it.get("stretch", (1.0, 1.0))), float(it.get("reach_m", 4.0)))
                    continue
                if "scatter" in it:
                    wanted = [it["scatter"]] if isinstance(it["scatter"], str) else it["scatter"]
                    self.missing.update(k for k in wanted if k not in self.catalog)
                if "id" in it:
                    x, z = pos(it["at"])
                    self.place(it["id"], x, z, facing_to_rotation(it.get("facing", 180)),
                               float(it.get("scale", 1.0)), path_ok=bool(it.get("path_ok", False)))
                elif "line" in it:
                    self.line(it["line"], pos(it["from"]), pos(it["to"]), it.get("gate"),
                              float(it.get("gate_at", 0.5)))
                elif "scatter" in it:
                    self.scatter(it["scatter"], ax, az, int(it["count"]), tuple(it["ring"]),
                                 int(it.get("seed", 0)), tuple(it.get("scale", (1.0, 1.0))),
                                 float(it.get("spacing", 2.0)),
                                 tuple(it["groves"]) if "groves" in it else None,
                                 tuple(it.get("stretch", (1.0, 1.0))))
        if self.missing:
            print(f"placements: skipped props that aren't built yet: {', '.join(sorted(self.missing))}")
        hand = [b for b in self.blocked_by_path if not b[0].startswith(("STR-01", "STR-02"))]
        if hand:
            print(f"placements: left out {len(hand)} props that would stand on a path: {hand[:6]}")
        return self.out


PLACEMENTS = DATA / "world" / "placements.json"


def load_placements(path: Path = PLACEMENTS) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def place_props(world: Heightfield, catalog: dict[str, PropSpec], placements: dict | None = None) -> Instances:
    return Placer(world, catalog).run(placements or load_placements())


# ---------------------------------------------------------------------------- #
# Footpaths: painted into the road map at load time, so the terrain shader draws
# them with the road material and scatter keeps off them.

def smooth_polyline(pts: np.ndarray, iterations: int = 3) -> np.ndarray:
    """Chaikin corner cutting; keeps both end points."""
    for _ in range(iterations):
        if len(pts) < 3:
            break
        a, b = pts[:-1], pts[1:]
        mid = np.empty((2 * len(a), 2))
        mid[0::2] = 0.75 * a + 0.25 * b
        mid[1::2] = 0.25 * a + 0.75 * b
        pts = np.vstack([pts[:1], mid[1:-1], pts[-1:]])
    return pts


def _smoothstep(e0: float, e1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def paint_paths(world: Heightfield, placements: dict | None = None) -> int:
    """Paint every group's 'paths' (polylines) and 'plazas' (circles) into world.road."""
    placements = placements or load_placements()
    anchors = {p.name: p for p in world.landmarks + world.waystones}
    road = world.road.copy()
    count = 0
    for group in placements["groups"]:
        anchor = anchors.get(group["anchor"])
        if anchor is None:
            continue
        shapes = []
        for p in group.get("paths", []):
            pts = np.array([[anchor.x + e, anchor.z - n] for e, n in p["points"]], dtype=np.float64)
            shapes.append((smooth_polyline(pts), float(p.get("width", 2.5)) / 2))
        for p in group.get("plazas", []):
            e, n = p["at"]
            shapes.append((np.array([[anchor.x + e, anchor.z - n]]), float(p["r"])))
        for pts, hw in shapes:
            reach = hw + 2.5
            lo, hi = pts.min(axis=0) - reach, pts.max(axis=0) + reach
            c0, r0 = (int(v) for v in world._px(lo[0], lo[1]))
            c1, r1 = (int(v) + 2 for v in world._px(hi[0], hi[1]))
            c0, r0 = max(c0, 0), max(r0, 0)
            c1, r1 = min(c1, world.size), min(r1, world.size)
            if c0 >= c1 or r0 >= r1:
                continue
            xs = (np.arange(c0, c1) + 0.5) * world.mpp - world.half
            zs = (np.arange(r0, r1) + 0.5) * world.mpp - world.half
            X, Z = np.meshgrid(xs, zs)
            D = np.full(X.shape, np.inf)
            segs = list(zip(pts[:-1], pts[1:])) or [(pts[0], pts[0])]
            for (x0, z0), (x1, z1) in segs:
                dx, dz = x1 - x0, z1 - z0
                t = np.clip(((X - x0) * dx + (Z - z0) * dz) / (dx * dx + dz * dz or 1e-9), 0.0, 1.0)
                D = np.minimum(D, np.hypot(X - (x0 + t * dx), Z - (z0 + t * dz)))
            wobble = 0.35 * np.sin(0.9 * X + 1.3 * Z) + 0.25 * np.sin(1.7 * Z - 0.6 * X)  # ragged edges
            w = _smoothstep(hw + 1.0, hw * 0.35, D + wobble)
            patch = road[r0:r1, c0:c1]
            road[r0:r1, c0:c1] = np.maximum(patch, (w * 255).astype(np.uint8))
            count += 1
    world.road = road
    return count


def paint_ground(world: Heightfield, placements: dict | None = None) -> np.ndarray:
    """Paint the groups' 'ground' patches (loose hay, for now) into a uint8 map, ragged at the edges.

    Each patch: {"material": "hay", "at": [east, north], "r": metres}. Returns the hay map
    (same size as the heightmap, 255 = fully covered) and stores it as world.hay.
    """
    placements = placements or load_placements()
    anchors = {p.name: p for p in world.landmarks + world.waystones}
    hay = np.zeros((world.size, world.size), dtype=np.float32)
    for group in placements["groups"]:
        anchor = anchors.get(group["anchor"])
        if anchor is None:
            continue
        for patch in group.get("ground", []):
            if patch.get("material", "hay") != "hay":
                continue
            x, z, r = anchor.x + patch["at"][0], anchor.z - patch["at"][1], float(patch["r"])
            reach = r * 1.5 + 2
            c0, r0 = (max(0, int(v)) for v in world._px(x - reach, z - reach))
            c1, r1 = (min(world.size, int(v) + 2) for v in world._px(x + reach, z + reach))
            if c0 >= c1 or r0 >= r1:
                continue
            X, Z = np.meshgrid((np.arange(c0, c1) + 0.5) * world.mpp - world.half,
                               (np.arange(r0, r1) + 0.5) * world.mpp - world.half)
            ang = np.arctan2(Z - z, X - x)
            wob = 0.22 * np.sin(3 * ang + x) + 0.15 * np.sin(5 * ang - z) + 0.1 * np.sin(0.9 * X + 1.3 * Z)
            d = np.hypot(X - x, Z - z) / (r * (1.0 + wob))
            w = _smoothstep(1.15, 0.6, d) * float(patch.get("strength", 1.0))
            hay[r0:r1, c0:c1] = np.maximum(hay[r0:r1, c0:c1], w)
    world.hay = (np.clip(hay, 0, 1) * 255 + 0.5).astype(np.uint8)
    return world.hay
