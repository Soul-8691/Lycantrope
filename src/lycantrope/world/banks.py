"""River banks: where the ground turns to pebbles, computed at load from the river curves.

meta.json stores each river's course (points every ~5 m, layout coordinates: y = north) and
width. The bank band covers the bed and a few meters of bank on each side, with a slightly
ragged edge. The result is a uint8 map the same size as the heightmap (255 = full pebbles).
"""
from __future__ import annotations

import numpy as np

BANK_M = 4.0          # pebbles this far past the water's edge


def river_bank_map(world) -> np.ndarray:
    out = np.zeros((world.size, world.size), dtype=np.float32)
    mpp, half = world.mpp, world.half
    for river in getattr(world, "rivers", []):
        pts = np.array([[p[0], -p[1]] for p in river["curve"]], dtype=np.float64)   # game x, z
        if len(pts) < 2:
            continue
        hw = float(river["width_m"]) / 2
        reach = hw + BANK_M + 3.0
        for (x0, z0), (x1, z1) in zip(pts[:-1], pts[1:]):
            c0 = int((min(x0, x1) - reach + half) / mpp)
            c1 = int((max(x0, x1) + reach + half) / mpp) + 2
            r0 = int((min(z0, z1) - reach + half) / mpp)
            r1 = int((max(z0, z1) + reach + half) / mpp) + 2
            c0, r0 = max(c0, 0), max(r0, 0)
            c1, r1 = min(c1, world.size), min(r1, world.size)
            if c0 >= c1 or r0 >= r1:
                continue
            X, Z = np.meshgrid((np.arange(c0, c1) + 0.5) * mpp - half, (np.arange(r0, r1) + 0.5) * mpp - half)
            dx, dz = x1 - x0, z1 - z0
            t = np.clip(((X - x0) * dx + (Z - z0) * dz) / (dx * dx + dz * dz or 1e-9), 0.0, 1.0)
            d = np.hypot(X - (x0 + t * dx), Z - (z0 + t * dz))
            ragged = 0.9 * np.sin(0.7 * X + 1.1 * Z) + 0.6 * np.sin(1.9 * Z - 0.8 * X)
            e0, e1 = hw + BANK_M + 1.2, hw + 0.8
            w = np.clip((d + ragged - e0) / (e1 - e0), 0.0, 1.0)
            w = w * w * (3 - 2 * w)
            out[r0:r1, c0:c1] = np.maximum(out[r0:r1, c0:c1], w)
    return (out * 255 + 0.5).astype(np.uint8)
