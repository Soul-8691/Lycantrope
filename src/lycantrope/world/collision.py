"""Solid props: characters can't walk through houses, trunks, fences, walls, rocks and clutter.

Every placed prop whose catalog entry has a 'collide' shape becomes a 2D collider on the ground
plane, stored in a grid of GRID_M cells (each collider is filed in every cell it can touch, plus
a margin for the widest character), so a lookup only reads one cell:

    {"box": k}     the prop's footprint (its x/z extents x k), turned with the prop
    {"circle": r}  a circle of radius r m (trunks, posts, barrels), scaled with the prop
    {"top": f}     optional: how high it blocks, as a fraction of the prop's height (trees: the
                   trunk only), for the third-person camera; characters are blocked at any height

`push_out` moves a character's circle out of anything it overlaps (sliding along walls);
`clear_distance` shortens the camera so it doesn't end up inside a house or a trunk.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

GRID_M = 8.0
MARGIN_M = 1.2           # widest character radius we expect


@dataclass
class Colliders:
    # boxes: cx, cz, cos, sin, half_x, half_z, top_y   circles: cx, cz, r, top_y
    boxes: np.ndarray = field(default_factory=lambda: np.zeros((0, 7)))
    circles: np.ndarray = field(default_factory=lambda: np.zeros((0, 4)))
    grid: dict[tuple[int, int], tuple[list[int], list[int]]] = field(default_factory=dict)

    # ------------------------------------------------------------------ build
    @classmethod
    def from_instances(cls, instances: dict[str, np.ndarray], catalog: dict) -> "Colliders":
        """instances: per prop key, rows of (x, y, z, rot, scale, shade, stretch) as placed."""
        boxes, circles = [], []
        for key, rows in instances.items():
            spec = catalog.get(key)
            shape = getattr(spec, "collide", None) if spec is not None else None
            if not shape:
                continue
            ex, ey, ez = spec.extents
            top_frac = float(shape.get("top", 1.0))
            for x, y, z, rot, scale, _shade, stretch in rows:
                top = y + ey * scale * stretch * top_frac
                if "box" in shape:
                    k = float(shape["box"]) * scale
                    boxes.append((x, z, math.cos(rot), math.sin(rot), ex * k / 2, ez * k / 2, top))
                elif "circle" in shape:
                    circles.append((x, z, float(shape["circle"]) * scale, top))
        c = cls(np.array(boxes, float).reshape(-1, 7), np.array(circles, float).reshape(-1, 4))
        c._index()
        return c

    def _index(self) -> None:
        self.grid = {}

        def file(i: int, x: float, z: float, reach: float, which: int) -> None:
            for gx in range(int(math.floor((x - reach) / GRID_M)), int(math.floor((x + reach) / GRID_M)) + 1):
                for gz in range(int(math.floor((z - reach) / GRID_M)), int(math.floor((z + reach) / GRID_M)) + 1):
                    self.grid.setdefault((gx, gz), ([], []))[which].append(i)
        for i, (x, z, _c, _s, hx, hz, _t) in enumerate(self.boxes):
            file(i, x, z, math.hypot(hx, hz) + MARGIN_M, 0)
        for i, (x, z, r, _t) in enumerate(self.circles):
            file(i, x, z, r + MARGIN_M, 1)

    @property
    def count(self) -> int:
        return len(self.boxes) + len(self.circles)

    def _cell(self, x: float, z: float) -> tuple[list[int], list[int]]:
        return self.grid.get((int(math.floor(x / GRID_M)), int(math.floor(z / GRID_M))), ([], []))

    # ------------------------------------------------------------------ queries
    def push_out(self, x: float, z: float, r: float, passes: int = 2) -> tuple[float, float, bool]:
        """Move a circle (x, z, radius r) out of every collider it overlaps. Returns (x, z, hit)."""
        hit = False
        for _ in range(passes):
            moved = False
            bi, ci = self._cell(x, z)
            for i in ci:
                cx, cz, cr, _t = self.circles[i]
                dx, dz = x - cx, z - cz
                d = math.hypot(dx, dz)
                if d < cr + r:
                    if d < 1e-6:
                        dx, dz, d = 1.0, 0.0, 1.0
                    push = cr + r - d
                    x += dx / d * push
                    z += dz / d * push
                    moved = True
            for i in bi:
                cx, cz, c, s, hx, hz, _t = self.boxes[i]
                dx, dz = x - cx, z - cz
                lx, lz = dx * c - dz * s, dx * s + dz * c          # into the box's own axes
                qx, qz = min(max(lx, -hx), hx), min(max(lz, -hz), hz)
                ox, oz = lx - qx, lz - qz
                d = math.hypot(ox, oz)
                if d >= r:
                    continue
                if d > 1e-6:                                       # outside: push along the normal
                    nx, nz, push = ox / d, oz / d, r - d
                else:                                              # centre inside: leave by the near side
                    px, pz = hx - abs(lx), hz - abs(lz)
                    if px < pz:
                        nx, nz, push = math.copysign(1.0, lx), 0.0, px + r
                    else:
                        nx, nz, push = 0.0, math.copysign(1.0, lz), pz + r
                wx, wz = nx * c + nz * s, -nx * s + nz * c         # back to world axes
                x += wx * push
                z += wz * push
                moved = True
            if not moved:
                break
            hit = True
        return x, z, hit

    def blocked(self, x: float, z: float, r: float = 0.0, y: float | None = None) -> bool:
        """Does a circle at (x, z) overlap anything? With y, only colliders that reach above y count."""
        bi, ci = self._cell(x, z)
        for i in ci:
            cx, cz, cr, top = self.circles[i]
            if (y is None or y < top) and math.hypot(x - cx, z - cz) < cr + r:
                return True
        for i in bi:
            cx, cz, c, s, hx, hz, top = self.boxes[i]
            if y is not None and y >= top:
                continue
            dx, dz = x - cx, z - cz
            lx, lz = dx * c - dz * s, dx * s + dz * c
            d = math.hypot(lx - min(max(lx, -hx), hx), lz - min(max(lz, -hz), hz))
            if d <= 0.0 or d < r:                              # inside, or within r of an edge
                return True
        return False

    def clear_distance(self, start: tuple[float, float, float], end: tuple[float, float, float],
                       pad: float = 0.35, step: float = 0.25) -> float:
        """How far from start toward end (a fraction 0..1) before the line enters a collider."""
        sx, sy, sz = start
        ex, ey, ez = end
        length = math.dist(start, end)
        n = max(1, int(length / step))
        for k in range(1, n + 1):
            t = k / n
            if self.blocked(sx + (ex - sx) * t, sz + (ez - sz) * t, pad, sy + (ey - sy) * t):
                return max(0.0, (k - 1) / n)
        return 1.0
