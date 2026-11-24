"""The generated world on the CPU side: heights, biomes, roads, splat weights.

Coordinates in the game are OpenGL style: x = east, y = up, z = south.
The world generator uses x = east, y = north, so ``z = -north``.
Pixel row 0 is the north edge (z = -half), column 0 the west edge (x = -half).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from lycantrope.core.paths import ASSETS


@dataclass
class Place:
    name: str
    x: float
    z: float
    height: float
    radius: float


class Heightfield:
    def __init__(self, folder: Path = ASSETS / "world") -> None:
        self.folder = folder
        self.meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
        m = self.meta
        self.size = int(m["size_px"])
        self.world_size = float(m["world_size_m"])
        self.half = self.world_size / 2
        self.mpp = float(m["meters_per_px"])
        self.water_level = float(m["water_level_m"])
        max_h = float(m["height"]["max_height_m"])
        raw = np.asarray(Image.open(folder / m["height"]["file"]), dtype=np.float32)
        self.heights = raw * (max_h / 65535.0)                     # meters, float32
        self.biome = np.asarray(Image.open(folder / m["biome_map"]["file"]), dtype=np.uint8)
        self.road = np.asarray(Image.open(folder / m["road_map"]["file"]), dtype=np.uint8)
        self.splat = [np.asarray(Image.open(folder / f).convert("RGBA"), dtype=np.uint8)
                      for f in m["splat"]["files"]]
        self.biome_names = {b["id"]: b["name"] for b in m["biomes"].values()}
        self.waystones = [Place(w["name"], w["x"], -w["y"], w["height_m"], w["r"]) for w in m["waystones"]]
        self.landmarks = [Place(w["name"], w["x"], -w["y"], w["height_m"], w["r"]) for w in m["landmarks"]]

    # -- lookups ---------------------------------------------------------- #
    def _px(self, x: float, z: float) -> tuple[float, float]:
        return (x + self.half) / self.mpp - 0.5, (z + self.half) / self.mpp - 0.5

    def height_at(self, x: float, z: float) -> float:
        """Bilinear terrain height (m) at a world position; clamps at the map edge."""
        c, r = self._px(x, z)
        n = self.size - 1
        c = min(max(c, 0.0), n - 1e-3)
        r = min(max(r, 0.0), n - 1e-3)
        c0, r0 = int(c), int(r)
        fc, fr = c - c0, r - r0
        h = self.heights
        top = h[r0, c0] * (1 - fc) + h[r0, c0 + 1] * fc
        bot = h[r0 + 1, c0] * (1 - fc) + h[r0 + 1, c0 + 1] * fc
        return float(top * (1 - fr) + bot * fr)

    def biome_at(self, x: float, z: float) -> str:
        c, r = self._px(x, z)
        r = min(max(int(round(r)), 0), self.size - 1)
        c = min(max(int(round(c)), 0), self.size - 1)
        return self.biome_names.get(int(self.biome[r, c]), "?")

    def chunk_bounds(self, chunk_m: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Origins (N,2: x,z), min and max height of every square chunk."""
        k = int(round(chunk_m / self.mpp))
        n = self.size // k
        h = self.heights[: n * k, : n * k].reshape(n, k, n, k)
        # include the shared edge row/column so neighbouring chunks overlap correctly
        hmin = h.min(axis=(1, 3))
        hmax = h.max(axis=(1, 3))
        cols, rows = np.meshgrid(np.arange(n), np.arange(n))
        origins = np.column_stack([cols.ravel() * chunk_m - self.half, rows.ravel() * chunk_m - self.half])
        return origins.astype(np.float32), hmin.ravel() - 1.0, hmax.ravel() + 1.0
