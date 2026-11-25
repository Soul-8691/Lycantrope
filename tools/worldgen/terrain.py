#!/usr/bin/env python3
"""
Lycantrope terrain generator (WLD-01, WLD-13, ART-08 prep)
=========================================================

Turns ``data/world/layout.json`` into a playable heightmap world. It needs no
concept art and no hand painting: biome regions, heights, roads, Waystone pads
and landmarks all come from the layout file plus seeded noise.

Pipeline
--------
1. Biome regions: noisy (domain-warped) distance to biome "sites" → soft blend weights.
2. Heights: every biome has its own noise recipe (rolling / hilly / flat swamp /
   ridged peaks / terraced badlands); recipes are blended by the weights.
3. World's Edge: a ring of ridged mountains closes the map.
4. Plateaus: e.g. the Duskhold crag.
5. Thermal erosion: softens slopes steeper than the talus angle.
6. Roads: Catmull-Rom splines carved into the terrain (smoothed, slightly sunken).
7. Pads: Waystones and landmarks are flattened (and lifted above water).

Outputs (``assets/world/``)
---------------------------
* ``height.png``  16-bit grayscale, ``h_m = value / 65535 * max_height_m``
* ``biome.png``   8-bit biome id per pixel (ids in meta.json)
* ``road.png``    8-bit road weight (255 = road center)
* ``meta.json``   scale, encoding, biomes, roads, Waystones, landmarks, stats
* ``preview.png`` top-down shaded map with labels, for approving the layout

Usage::

    python tools/worldgen/terrain.py                 # full 2048 px (1 m/px)
    python tools/worldgen/terrain.py --size 1024     # fast iteration
    python tools/worldgen/terrain.py --seed 42 --out scratch/world
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
from noise import fbm, ridged  # noqa: E402

GENERATOR_VERSION = 1
DEFAULT_LAYOUT = ROOT / "data" / "world" / "layout.json"
DEFAULT_OUT = ROOT / "assets" / "world"
WALKABLE_DEG = 38.0


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def smoothstep(e0: float, e1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return (t * t * (3.0 - 2.0 * t)).astype(np.float32)


def box_blur(a: np.ndarray, r: int, passes: int = 2) -> np.ndarray:
    """Separable box blur with edge padding (passes=2 ≈ triangle, 3 ≈ gaussian)."""
    out = a.astype(np.float32)
    if r < 1:
        return out
    k = 2 * r + 1
    for _ in range(passes):
        p = np.pad(out, ((r + 1, r), (0, 0)), mode="edge")
        cs = np.cumsum(p, axis=0, dtype=np.float64)
        out = ((cs[k:] - cs[:-k]) / k).astype(np.float32)
        p = np.pad(out, ((0, 0), (r + 1, r)), mode="edge")
        cs = np.cumsum(p, axis=1, dtype=np.float64)
        out = ((cs[:, k:] - cs[:, :-k]) / k).astype(np.float32)
    return out


def catmull_rom(points: list[list[float]], samples: int = 10) -> np.ndarray:
    """Smooth curve through the given points (endpoints duplicated)."""
    p = np.asarray(points, dtype=np.float64)
    if len(p) < 3:
        return p
    p = np.vstack([p[0], p, p[-1]])
    out = []
    t = np.linspace(0, 1, samples, endpoint=False)[:, None]
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(p[-2][None])
    return np.vstack(out)


class Grid:
    """Pixel grid in world meters. Row 0 is north (+y), column 0 is west (-x)."""

    def __init__(self, size_px: int, world_m: float) -> None:
        self.n = size_px
        self.world = world_m
        self.mpp = world_m / size_px
        self.half = world_m / 2
        c = ((np.arange(size_px, dtype=np.float32) + 0.5) * self.mpp - self.half).astype(np.float32)
        self.X, self.Y = np.meshgrid(c, -c)

    def to_px(self, x: float, y: float) -> tuple[float, float]:
        return (x + self.half) / self.mpp - 0.5, (self.half - y) / self.mpp - 0.5

    def window(self, x0: float, y0: float, x1: float, y1: float) -> tuple[slice, slice]:
        c0, r1 = self.to_px(min(x0, x1), min(y0, y1))
        c1, r0 = self.to_px(max(x0, x1), max(y0, y1))
        rs = slice(max(0, int(r0) - 1), min(self.n, int(math.ceil(r1)) + 2))
        cs = slice(max(0, int(c0) - 1), min(self.n, int(math.ceil(c1)) + 2))
        return rs, cs


def polyline_distance(grid: Grid, pts: np.ndarray, reach: float, values: np.ndarray | None = None):
    """Distance (m) from each pixel to a polyline, only computed within `reach`.

    With `values` (one per point), also returns the value interpolated at the
    nearest point of the polyline: ``(D, V)``.
    """
    D = np.full((grid.n, grid.n), np.inf, dtype=np.float32)
    V = np.zeros((grid.n, grid.n), dtype=np.float32) if values is not None else None
    for i, ((x0, y0), (x1, y1)) in enumerate(zip(pts[:-1], pts[1:])):
        rs, cs = grid.window(min(x0, x1) - reach, min(y0, y1) - reach,
                             max(x0, x1) + reach, max(y0, y1) + reach)
        if rs.start >= rs.stop or cs.start >= cs.stop:
            continue
        sx, sy = grid.X[rs, cs], grid.Y[rs, cs]
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy or 1e-9
        t = np.clip(((sx - x0) * dx + (sy - y0) * dy) / L2, 0.0, 1.0)
        d = np.hypot(sx - (x0 + t * dx), sy - (y0 + t * dy)).astype(np.float32)
        if V is not None:
            closer = d < D[rs, cs]
            V[rs, cs] = np.where(closer, values[i] + t * (values[i + 1] - values[i]), V[rs, cs])
        D[rs, cs] = np.minimum(D[rs, cs], d)
    return (D, V) if values is not None else D


def resample(pts: np.ndarray, spacing: float) -> np.ndarray:
    """Evenly spaced points along a polyline."""
    seg = np.hypot(*np.diff(pts, axis=0).T)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    t = np.arange(0.0, s[-1], spacing)
    t = np.append(t, s[-1])
    return np.column_stack([np.interp(t, s, pts[:, 0]), np.interp(t, s, pts[:, 1])])


def sample(H: np.ndarray, grid: Grid, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    """Bilinear height lookup at world coordinates."""
    c, r = grid.to_px(xs, ys)
    c = np.clip(c, 0, grid.n - 1.001)
    r = np.clip(r, 0, grid.n - 1.001)
    c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int)
    fc, fr = c - c0, r - r0
    top = H[r0, c0] * (1 - fc) + H[r0, c0 + 1] * fc
    bot = H[r0 + 1, c0] * (1 - fc) + H[r0 + 1, c0 + 1] * fc
    return top * (1 - fr) + bot * fr


def road_profile(h: np.ndarray, spacing: float, smooth_m: float, max_grade_deg: float, floor: float,
                 pinned: np.ndarray | None = None) -> np.ndarray:
    """Smooth a height profile along a road and limit its grade (cuts and fills).

    `pinned` (NaN = free) fixes the height where the road crosses a Waystone or
    landmark pad, so the road grades into the pad instead of cutting through it.
    """
    pin = np.zeros(len(h), bool) if pinned is None else ~np.isnan(pinned)
    k = max(1, int(smooth_m / spacing))
    prof = h.astype(np.float64)
    prof[pin] = pinned[pin]
    for _ in range(3):
        pad = np.pad(prof, k, mode="edge")
        cs = np.cumsum(np.concatenate([[0.0], pad]))
        prof = (cs[2 * k + 1:] - cs[:-2 * k - 1]) / (2 * k + 1)
        prof[pin] = pinned[pin]
    g = math.tan(math.radians(max_grade_deg)) * spacing
    for _ in range(2):                       # forward + backward grade limiting
        for i in range(1, len(prof)):
            if not pin[i]:
                prof[i] = min(max(prof[i], prof[i - 1] - g), prof[i - 1] + g)
        for i in range(len(prof) - 2, -1, -1):
            if not pin[i]:
                prof[i] = min(max(prof[i], prof[i + 1] - g), prof[i + 1] + g)
    return np.maximum(prof, floor).astype(np.float32)


def slope_deg(H: np.ndarray, mpp: float) -> np.ndarray:
    gy, gx = np.gradient(H, mpp)
    return np.degrees(np.arctan(np.hypot(gx, gy))).astype(np.float32)


def thermal_erosion(H: np.ndarray, mpp: float, iterations: int, talus_deg: float, rate: float) -> np.ndarray:
    """Move material downhill wherever the slope exceeds the talus angle."""
    talus = math.tan(math.radians(talus_deg)) * mpp
    H = H.astype(np.float32).copy()
    for _ in range(iterations):
        delta = np.zeros_like(H)
        for a, b in (((slice(None), slice(None, -1)), (slice(None), slice(1, None))),
                     ((slice(None, -1), slice(None)), (slice(1, None), slice(None)))):
            d = H[a] - H[b]
            move = np.where(np.abs(d) > talus, (np.abs(d) - talus) * rate * 0.5, 0.0).astype(np.float32)
            move *= np.sign(d)
            delta[a] -= move
            delta[b] += move
        H += delta
    return H


# --------------------------------------------------------------------------- #
# generation
# --------------------------------------------------------------------------- #

def generate(layout: dict, size_px: int, seed: int | None = None, log=print) -> dict:
    seed = int(layout.get("seed", 0) if seed is None else seed)
    t0 = time.perf_counter()
    grid = Grid(size_px, float(layout["world_size_m"]))
    X, Y, mpp = grid.X, grid.Y, grid.mpp
    water = float(layout["water_level_m"])
    max_h = float(layout["max_height_m"])

    def step(msg: str) -> None:
        log(f"  [{time.perf_counter() - t0:6.1f}s] {msg}")

    # 1. biome weights ---------------------------------------------------- #
    w = layout["warp"]
    ws, wa = float(w["scale_m"]), float(w["amount_m"])
    WX = X + wa * fbm(X / ws, Y / ws, 4, seed + 101)
    WY = Y + wa * fbm(X / ws + 31.7, Y / ws - 17.3, 4, seed + 202)
    names = list(layout["biomes"])
    S = np.empty((len(names), size_px, size_px), dtype=np.float32)
    for bi, name in enumerate(names):
        best = None
        for site in layout["biomes"][name]["sites"]:
            d = np.hypot(WX - site["x"], WY - site["y"]) / float(site["r"])
            best = d if best is None else np.minimum(best, d)
        S[bi] = best
    del WX, WY
    T = float(layout.get("blend_softness", 0.08))
    W = np.exp(-(S - S.min(axis=0)) / T).astype(np.float32)
    W /= W.sum(axis=0)
    biome_idx = S.argmin(axis=0)
    del S
    step("biome regions")

    # 2. shared noise fields + per-biome recipes ------------------------- #
    sc = layout["noise_scales_m"]
    F = {
        "low": fbm(X / sc["low"], Y / sc["low"], 4, seed + 1),
        "mid": fbm(X / sc["mid"], Y / sc["mid"], 5, seed + 2),
        "ridge": ridged(X / sc["ridge"], Y / sc["ridge"], 6, seed + 3),
        "detail": fbm(X / sc["detail"], Y / sc["detail"], 3, seed + 4),
    }
    step("noise fields")
    H = np.zeros((size_px, size_px), dtype=np.float32)
    for bi, name in enumerate(names):
        r = layout["biomes"][name]["height"]
        hb = (r.get("base", 0) + r.get("low", 0) * F["low"] + r.get("mid", 0) * F["mid"]
              + r.get("ridge", 0) * F["ridge"] + r.get("detail", 0) * F["detail"])
        if r.get("terrace_m"):
            s = float(r["terrace_m"])
            k = hb / s
            frac = k - np.floor(k)
            stepped = (np.floor(k) + smoothstep(0.25, 0.75, frac)) * s
            mix = float(r.get("terrace_mix", 0.55))
            hb = hb * (1 - mix) + stepped * mix
        H += W[bi] * hb
    step("biome heights")

    # 3. world's edge ----------------------------------------------------- #
    b = layout["border"]
    edge = np.minimum(grid.half - np.abs(X), grid.half - np.abs(Y))
    edge = edge + 40.0 * F["mid"]                     # irregular boundary
    border_w = smoothstep(float(b["width_m"]), 0.0, edge)
    H += border_w * float(b["height_m"]) * (0.55 + 0.6 * F["ridge"])
    step("world's edge")

    # 4. plateaus --------------------------------------------------------- #
    for p in layout.get("plateaus", []):
        d = np.hypot(X - p["x"], Y - p["y"]) + float(p.get("edge_noise_m", 25.0)) * F["mid"]
        t = np.clip((p["r"] + p["falloff_m"] - d) / p["falloff_m"], 0.0, 1.0)
        if p.get("profile") == "cliff":     # gentle foot, then a steep rock band up to the top
            foot = float(p.get("foot", 0.3))
            wgt = foot * smoothstep(0.0, 0.6, t) + (1 - foot) * smoothstep(0.62, 0.88, t)
        else:
            wgt = smoothstep(0.0, 1.0, t)
        H = H * (1 - wgt) + (p["height_m"] + 2.0 * F["detail"]) * wgt
    step("plateaus")

    # 5. erosion ---------------------------------------------------------- #
    e = layout.get("erosion", {})
    if e.get("iterations", 0):
        H = thermal_erosion(H, mpp, int(e["iterations"]), float(e["talus_deg"]), float(e["rate"]))
    step("thermal erosion")

    # 6. pads (Waystones + landmarks), before roads so roads grade into them ------------------------------------ #
    pads = [dict(p, kind="waystone") for p in layout.get("waystones", [])] + \
           [dict(p, kind="landmark") for p in layout.get("landmarks", [])]
    for p in pads:
        r = float(p["r"])
        rs, cs = grid.window(p["x"] - 3 * r, p["y"] - 3 * r, p["x"] + 3 * r, p["y"] + 3 * r)
        d = np.hypot(X[rs, cs] - p["x"], Y[rs, cs] - p["y"])
        inner = d <= r * 1.5
        target = float(H[rs, cs][inner].mean()) if inner.any() else float(H[rs, cs].mean())
        target = max(target, water + 1.0)
        wgt = smoothstep(r * 2.6, r * 1.5, d)
        H[rs, cs] = H[rs, cs] * (1 - wgt) + target * wgt
        p["height_m"] = round(target, 2)
    step("pads")

    # 7. roads ------------------------------------------------------------ #
    road_w = np.zeros_like(H)
    road_keep = np.zeros_like(H)          # roads and their shoulders: rivers don't dig here
    road_curves = []
    spacing = max(1.0, mpp)
    for road in layout.get("roads", []):
        pts = resample(catmull_rom(road["points"], samples=12), spacing)
        road_curves.append(pts)
        pinned = np.full(len(pts), np.nan)
        for pd in pads:
            near = np.hypot(pts[:, 0] - pd["x"], pts[:, 1] - pd["y"]) <= pd["r"] * 1.5
            pinned[near] = pd["height_m"]
        prof = road_profile(sample(H, grid, pts[:, 0], pts[:, 1]), spacing,
                            float(road.get("smooth_m", 30)), float(road.get("max_grade_deg", 16)),
                            water + 0.6, pinned)
        half_w = road["width_m"] / 2
        shoulder = half_w + float(road.get("shoulder_m", 10))
        D, P = polyline_distance(grid, pts, shoulder + 2 * mpp, prof)
        rw = smoothstep(shoulder, half_w, D)
        core = smoothstep(half_w, half_w * 0.4, D)
        H = H * (1 - rw) + (P - 0.15 * core) * rw
        road_w = np.maximum(road_w, smoothstep(half_w + 1.5, half_w * 0.5, D))
        road_keep = np.maximum(road_keep, smoothstep(shoulder, half_w + 1.5, D))
    step("roads")

    # 8. lakes and rivers (after roads: rivers pass under them like a culvert) -- #
    # shoreline noise: big bays plus smaller coves, so lakes aren't ovals
    shore = F["mid"] + 0.8 * fbm(X / 90.0, Y / 90.0, 3, seed + 7)
    surface, lakes_out, rivers_out = carve_water(layout, grid, H, road_keep, shore, water)
    step("lakes and rivers")

    H = np.clip(H, 0.0, max_h)

    # biome map: argmin biome, World's Edge where border dominates
    biome_ids = np.array([layout["biomes"][n]["id"] for n in names], dtype=np.uint8)
    biome = biome_ids[biome_idx]
    biome[border_w > 0.45] = layout["boundary"]["id"]

    slope = slope_deg(H, mpp)
    step("done")
    return {"grid": grid, "H": H, "W": W, "names": names, "biome": biome, "road": road_w, "border": border_w,
            "slope": slope, "pads": pads, "road_curves": road_curves, "seed": seed,
            "surface": surface, "lakes": lakes_out, "rivers": rivers_out}


def meander(pts: np.ndarray, amount: float, seed: int) -> np.ndarray:
    """Wiggle a path sideways (two sine waves along its length), keeping both ends in place."""
    if amount <= 0 or len(pts) < 3:
        return pts
    seg = np.hypot(*np.diff(pts, axis=0).T)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    L = s[-1]
    rng = np.random.default_rng(seed)
    p1, p2 = rng.uniform(0, math.tau, 2)
    off = amount * (np.sin(s / 75.0 + p1) + 0.45 * np.sin(s / 29.0 + p2))
    off *= smoothstep(0.0, 70.0, s) * smoothstep(L, L - 70.0, s)
    tang = np.gradient(pts, axis=0)
    tang /= np.maximum(np.linalg.norm(tang, axis=1, keepdims=True), 1e-9)
    nrm = np.column_stack([-tang[:, 1], tang[:, 0]])
    return resample(pts + nrm * off[:, None], max(1.0, float(seg.mean())))


def carve_water(layout: dict, grid: Grid, H: np.ndarray, road_keep: np.ndarray, noise: np.ndarray,
                sea: float) -> tuple[np.ndarray, list, list]:
    """Carve lake basins and river channels into H (in place) and return the water surface map.

    The surface map holds the water height at every pixel: sea level by default, a lake's own
    level over the lake, and a falling profile along each river. Water is wherever the
    surface is above the ground. Order: lake levels (from the untouched ground), then rivers
    (a river leaving a lake starts at its level and never runs uphill), then lake basins with
    a low rim so they can't spill.
    """
    X, Y, mpp = grid.X, grid.Y, grid.mpp
    surface = np.full(H.shape, sea, dtype=np.float32)
    lakes_out, rivers_out = [], []

    # 1. lake levels: a little below the ground they sit in
    lakes = []
    for lake in layout.get("lakes", []):
        x, y, r = float(lake["x"]), float(lake["y"]), float(lake["r"])
        rs, cs = grid.window(x - 2.2 * r, y - 2.2 * r, x + 2.2 * r, y + 2.2 * r)
        # several overlapping basins (arms and bays), seeded by the lake's name, then a wobbly shore
        rng = np.random.default_rng(sum(map(ord, lake["name"])) * 7919 + 13)
        px, py = X[rs, cs] - x, Y[rs, cs] - y
        fields = []
        main_ang = rng.uniform(0, math.pi)                     # the lake's long axis
        for i in range(int(lake.get("lobes", rng.integers(4, 8)))):
            if i == 0:
                cx, cy, lr, ang, stretch = 0.0, 0.0, 0.7, main_ang, rng.uniform(1.2, 1.8)
            else:
                a, dist = rng.uniform(0, math.tau), rng.uniform(0.3, 0.95) * r
                cx, cy = dist * math.cos(a), dist * math.sin(a)
                lr, ang, stretch = rng.uniform(0.18, 0.55), rng.uniform(0, math.pi), rng.uniform(1.0, 2.6)
            ca, sa = math.cos(ang), math.sin(ang)
            u = ((px - cx) * ca + (py - cy) * sa) / stretch       # elongated lobes: arms and inlets
            v = -(px - cx) * sa + (py - cy) * ca
            fields.append(np.hypot(u, v) / (lr * r))
        k = 0.18                                               # smooth union: no clover cusps
        dn = -k * np.log(np.sum(np.exp(-np.stack(fields) / k), axis=0))
        d = dn * r + 0.32 * r * noise[rs, cs]
        inner = d <= 0.6 * r
        ground = float(H[rs, cs][inner].mean()) if inner.any() else \
            float(sample(H, grid, np.array([x]), np.array([y]))[0])   # tiny lake on a coarse grid
        level = float(lake.get("level_m", ground - 1.0))
        lakes.append((lake, x, y, r, rs, cs, d, max(level, sea + 0.3)))

    # 2. rivers
    spacing = max(1.0, mpp)
    channel = np.zeros(H.shape, dtype=bool)
    for river in layout.get("rivers", []):
        pts = resample(catmull_rom(river["points"], samples=12), spacing)
        pts = meander(pts, float(river.get("meander_m", 0.9 * float(river.get("width_m", 8.0)) + 6.0)),
                      sum(map(ord, river["name"])))
        width = float(river.get("width_m", 8.0))
        depth = float(river.get("depth_m", 1.8))
        bank = float(river.get("bank_m", 14.0))
        tang = np.gradient(pts, axis=0)
        tang /= np.maximum(np.linalg.norm(tang, axis=1, keepdims=True), 1e-9)
        nrm = np.column_stack([-tang[:, 1], tang[:, 0]])
        across = np.stack([sample(H, grid, pts[:, 0] + nrm[:, 0] * o, pts[:, 1] + nrm[:, 1] * o)
                           for o in (-width / 2, -width / 4, 0.0, width / 4, width / 2)])
        prof = across.min(axis=0) - 0.6
        for (_l, lx, ly, lr, *_rest, level) in lakes:            # flowing out of a lake: start at its level
            inside = np.hypot(pts[:, 0] - lx, pts[:, 1] - ly) <= lr
            if inside[0]:
                prof[inside] = level
        prof = np.maximum(np.minimum.accumulate(prof), sea)        # never uphill
        # a brook that ends at a river meets it at the river's level: look around the end for
        # water already laid down, then ramp the last stretch down to it (cutting into the bank)
        ex, ey = pts[-1]
        ring = [(ex + rr * math.cos(t), ey + rr * math.sin(t)) for rr in (0.0, 6.0, 12.0, 18.0)
                for t in np.linspace(0, math.tau, 8, endpoint=False)]
        joins = float(sample(surface, grid, np.array([q[0] for q in ring]), np.array([q[1] for q in ring])).max())
        if joins > sea + 0.1:
            along = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
            prof = np.minimum(prof, joins + (along[-1] - along) * 0.06)
            prof = np.maximum(prof, joins)
        for (_l, lx, ly, lr, *_rest, level) in lakes:            # flowing into a lake: arrive at its level
            if np.hypot(pts[-1, 0] - lx, pts[-1, 1] - ly) <= lr * 1.35:
                along = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
                prof = np.maximum(np.minimum(prof, level + (along[-1] - along) * 0.06), level)
        D, S = polyline_distance(grid, pts, width / 2 + bank + 3 * mpp, prof)
        near = np.isfinite(D)
        Dn, Sn = D[near], S[near]
        hw = width / 2
        bed = Sn - depth * smoothstep(hw, 0.15 * width, Dn)
        bankside = Sn + np.maximum(Dn - hw, 0.0) * float(river.get("bank_slope", 0.35))
        target = np.where(Dn <= hw, bed, bankside)
        k = road_keep[near]                              # roads stay: the river runs under them
        Hn = H[near]
        Hn = Hn + (np.minimum(Hn, target) - Hn) * (1.0 - k)
        keep = k > 0.5
        levee = (Dn > hw) & (Dn < hw + bank) & ~keep     # low ground beside it gets a small bank
        Hn = np.where(levee, np.maximum(Hn, Sn + 0.25 * smoothstep(hw + bank, hw, Dn)), Hn)
        H[near] = Hn
        wet = Dn <= hw + 3.0
        sv = surface[near]
        surface[near] = np.where(wet, np.maximum(sv, Sn), sv)
        cm = channel[near]
        channel[near] = cm | (Dn <= hw + 2.0)
        rivers_out.append({"name": river["name"], "width_m": width,
                           "curve": [[round(float(px), 1), round(float(py), 1), round(float(sv_), 2)]
                                     for (px, py), sv_ in zip(pts[::5], prof[::5])]})

    # 3. lake basins, with a low rim (except where a river runs in or out)
    for lake, x, y, r, rs, cs, d, level in lakes:
        depth = float(lake.get("depth_m", 4.0))
        bowl = np.where(d <= r, level - depth * smoothstep(r, 0.25 * r, d),
                        level + (d - r) * float(lake.get("bank_slope", 0.3)))
        Hp = np.minimum(H[rs, cs], bowl)
        rim = (d > r) & (d < 1.35 * r) & ~channel[rs, cs]
        Hp = np.where(rim, np.maximum(Hp, level + 0.6 * smoothstep(1.35 * r, r * 1.05, d)), Hp)
        H[rs, cs] = Hp
        wet = (d <= 1.35 * r) & (Hp < level)
        try:                                           # keep only water connected to the middle
            from scipy import ndimage
            lab, _n = ndimage.label(wet)
            cr, cc = (int(v) for v in np.unravel_index(np.argmin(d), d.shape))
            if lab[cr, cc]:
                wet = lab == lab[cr, cc]
            wet = ndimage.binary_dilation(wet, iterations=3)
        except ImportError:
            pass
        patch = surface[rs, cs]
        surface[rs, cs] = np.where(wet, np.maximum(patch, level), patch)
        lakes_out.append({"name": lake["name"], "x": x, "y": y, "r": r, "level_m": round(level, 2)})
    return surface, lakes_out, rivers_out


# --------------------------------------------------------------------------- #
# stats, outputs, preview
# --------------------------------------------------------------------------- #

def compute_stats(layout: dict, res: dict) -> tuple[dict, list[str]]:
    H, biome, slope, road = res["H"], res["biome"], res["slope"], res["road"]
    water = res.get("surface", layout["water_level_m"])        # per-pixel: sea, lakes, rivers
    stats: dict = {"biomes": {}, "roads": {}}
    warnings: list[str] = []
    all_biomes = dict(layout["biomes"], boundary=layout["boundary"])
    for key, b in all_biomes.items():
        m = biome == b["id"]
        if not m.any():
            warnings.append(f"Biome {b['name']} has no area")
            continue
        stats["biomes"][key] = {
            "area_pct": round(100 * float(m.mean()), 1),
            "height_min": round(float(H[m].min()), 1),
            "height_mean": round(float(H[m].mean()), 1),
            "height_max": round(float(H[m].max()), 1),
            "water_pct": round(100 * float((H[m] < (water[m] if isinstance(water, np.ndarray) else water)).mean()), 1),
            "unwalkable_pct": round(100 * float((slope[m] > WALKABLE_DEG).mean()), 1),
        }
    grid = res["grid"]
    for road, pts in zip(layout.get("roads", []), res["road_curves"]):
        D = polyline_distance(grid, pts, road["width_m"] / 2 + grid.mpp)
        core = D <= max(road["width_m"] / 2 - 1.0, grid.mpp)
        s = slope[core]
        if s.size == 0:
            continue
        p95 = float(np.percentile(s, 95))
        wcore = water[core] if isinstance(water, np.ndarray) else water
        stats["roads"][road["name"]] = {"slope_p95_deg": round(p95, 1), "slope_max_deg": round(float(s.max()), 1),
                                        "underwater_pct": round(100 * float((H[core] < wcore).mean()), 1)}
        if p95 > WALKABLE_DEG:
            warnings.append(f"Road '{road['name']}' is too steep in places (95th pct {p95:.0f}°)")
    for p in res["pads"]:
        c, r = grid.to_px(p["x"], p["y"])
        rr = max(1, int(p["r"] / grid.mpp))
        ci, ri = int(round(c)), int(round(r))
        patch = H[max(0, ri - rr):ri + rr + 1, max(0, ci - rr):ci + rr + 1]
        if patch.size and float(patch.max() - patch.min()) > 1.5:
            warnings.append(f"{p['kind'].title()} '{p['name']}' is not flat "
                            f"({float(patch.max() - patch.min()):.1f} m variation)")
        bid = int(biome[min(grid.n - 1, max(0, ri)), min(grid.n - 1, max(0, ci))])
        if bid == layout["boundary"]["id"]:
            warnings.append(f"{p['kind'].title()} '{p['name']}' lies inside the World's Edge")
    return stats, warnings


def render_preview(layout: dict, res: dict, size: int = 1024) -> Image.Image:
    H, W, grid = res["H"], res["W"], res["grid"]
    water = float(layout["water_level_m"])
    names = res["names"]
    cols = np.array([layout["biomes"][n]["color"] for n in names], dtype=np.float32) / 255.0
    rgb = np.tensordot(W.transpose(1, 2, 0), cols, axes=([2], [0]))           # soft biome colors
    border = (res["biome"] == layout["boundary"]["id"])[..., None]
    rgb = np.where(border, np.array(layout["boundary"]["color"], np.float32) / 255.0, rgb)

    slope = res["slope"][..., None]
    rock = np.array([0.45, 0.43, 0.41], np.float32)
    rgb = rgb + (rock - rgb) * smoothstep(28.0, 45.0, slope)                   # steep = rock
    snow = smoothstep(190.0, 240.0, H)[..., None] * (1 - smoothstep(40.0, 55.0, slope))
    rgb = rgb + (np.array([0.95, 0.96, 0.98], np.float32) - rgb) * snow       # high = snow
    road = res["road"][..., None]
    rgb = rgb + (np.array([0.62, 0.52, 0.38], np.float32) - rgb) * road * 0.85

    gy, gx = np.gradient(H, grid.mpp)
    nz = 1.0 / np.sqrt(gx * gx + gy * gy + 1.0)
    light = np.array([-0.5, 0.6, 0.62], np.float32)                           # from the north-west
    light /= np.linalg.norm(light)
    shade = np.clip((-gx * nz) * light[0] + (gy * nz) * light[1] + nz * light[2], 0, 1)[..., None]
    rgb = rgb * (0.35 + 0.85 * shade)

    surf = res.get("surface", np.full_like(H, water))
    depth = np.clip((surf - H) / 6.0, 0, 1)[..., None]
    under = (H < surf)[..., None]
    wcol = np.array([0.20, 0.33, 0.38], np.float32) * (1 - 0.5 * depth) + 0.05
    rgb = np.where(under, wcol * (0.8 + 0.2 * shade), rgb)

    img = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8), "RGB")
    img = img.resize((size, size), Image.LANCZOS)
    draw = ImageDraw.Draw(img)
    f_big, f_small = _font(max(14, size // 45)), _font(max(10, size // 80))
    s = size / grid.n

    def px(x, y):
        c, r = grid.to_px(x, y)
        return c * s, r * s

    for name in names:
        site = layout["biomes"][name]["sites"][0]
        lx, ly = layout["biomes"][name].get("label_at", (site["x"], site["y"] + 70))
        x, y = px(lx, ly)
        _label(draw, (x, y), layout["biomes"][name]["name"].upper(), f_big, anchor="mm")
    for p in res["pads"]:
        x, y = px(p["x"], p["y"])
        if p["kind"] == "waystone":
            r = max(4, size // 160)
            draw.polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], fill=(90, 220, 255), outline=(0, 0, 0))
        else:
            r = max(3, size // 220)
            draw.ellipse([x - r, y - r, x + r, y + r], fill=(255, 200, 70), outline=(0, 0, 0))
        _label(draw, (x + 7, y), p["name"], f_small, anchor="lm")
    for pl in layout.get("plateaus", []):
        x, y = px(pl["x"], pl["y"])
        _label(draw, (x, y + size // 30), pl["name"], f_small, anchor="mm")

    # compass, scale bar, title
    m = size // 40
    draw.polygon([(size - 2 * m, m), (size - 2.6 * m, 2.6 * m), (size - 1.4 * m, 2.6 * m)], fill=(240, 240, 240))
    _label(draw, (size - 2 * m, 3.4 * m), "N", f_big, anchor="mm")
    bar_m = 250 if grid.world <= 2500 else 500
    bar_px = bar_m / grid.world * size
    y0 = size - 2 * m
    draw.rectangle([m, y0, m + bar_px, y0 + max(3, size // 250)], fill=(240, 240, 240), outline=(0, 0, 0))
    _label(draw, (m, y0 - 4), f"{bar_m} m", f_small, anchor="ls")
    _label(draw, (m, m), f"LYCANTROPE · Aldmoor · seed {res['seed']} · {grid.world:.0f} m", f_small, anchor="lt")
    _label(draw, (m, m + size // 45), f"cyan = Waystone   gold = landmark   blue = water below {water:.0f} m",
           f_small, anchor="lt")
    return img


def _font(px: int):
    for name in ("seguisb.ttf", "segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, px)
        except OSError:
            continue
    return ImageFont.load_default(size=px)


def _label(draw: ImageDraw.ImageDraw, xy, text: str, font, anchor: str = "la") -> None:
    draw.text(xy, text, font=font, anchor=anchor, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))


def write_outputs(layout: dict, res: dict, out: Path, preview_size: int) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    max_h = float(layout["max_height_m"])
    h16 = np.round(res["H"] / max_h * 65535).astype(np.uint16)
    Image.fromarray(h16).save(out / "height.png", optimize=True)
    Image.fromarray(res["biome"]).save(out / "biome.png", optimize=True)
    Image.fromarray((res["road"] * 255).astype(np.uint8)).save(out / "road.png", optimize=True)
    w16 = np.round(np.clip(res["surface"], 0, max_h) / max_h * 65535).astype(np.uint16)
    Image.fromarray(w16).save(out / "water.png", optimize=True)
    # soft per-biome weights for texture blending: 2 RGBA maps, channel order in meta["splat"]
    edge = smoothstep(0.3, 0.6, res["border"])
    chans = [res["W"][i] * (1 - edge) for i in range(len(res["names"]))] + [edge]
    channel_names = list(res["names"]) + ["boundary"]
    while len(chans) < 8:
        chans.append(np.zeros_like(edge))
        channel_names.append(None)
    for k, fname in enumerate(("splat_a.png", "splat_b.png")):
        rgba = np.dstack(chans[4 * k:4 * k + 4])
        Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(out / fname, optimize=True)
    render_preview(layout, res, preview_size).save(out / "preview.png", optimize=True)

    stats, warnings = compute_stats(layout, res)
    grid = res["grid"]
    biomes = {k: {"id": v["id"], "name": v["name"], "color": v["color"], "levels": v.get("levels")}
              for k, v in layout["biomes"].items()}
    biomes["boundary"] = {"id": layout["boundary"]["id"], "name": layout["boundary"]["name"],
                          "color": layout["boundary"]["color"], "levels": None}
    meta = {
        "generator": "tools/worldgen/terrain.py", "generator_version": GENERATOR_VERSION,
        "seed": res["seed"], "size_px": grid.n, "world_size_m": grid.world, "meters_per_px": grid.mpp,
        "origin": "map center; x = east, y = north; pixel row 0 = north edge, column 0 = west edge",
        "height": {"file": "height.png", "encoding": "uint16", "max_height_m": max_h,
                   "decode": "h_m = value / 65535 * max_height_m"},
        "water_level_m": layout["water_level_m"],
        "water_map": {"file": "water.png", "encoding": "uint16 water surface height, same decode as height; "
                      "water wherever it is above the ground"},
        "lakes": res["lakes"],
        "rivers": res["rivers"],
        "biome_map": {"file": "biome.png", "encoding": "uint8 biome id"},
        "road_map": {"file": "road.png", "encoding": "uint8 weight, 255 = road center"},
        "splat": {"files": ["splat_a.png", "splat_b.png"], "channels": channel_names,
                  "encoding": "RGBA uint8 biome blend weights (sum ≈ 1)"},
        "biomes": biomes,
        "roads": [{"name": r["name"], "width_m": r["width_m"],
                   "curve": [[round(float(x), 1), round(float(y), 1)] for x, y in resample(pts, 5.0)]}
                  for r, pts in zip(layout.get("roads", []), res["road_curves"])],
        "waystones": [{k: p[k] for k in ("name", "x", "y", "r", "height_m")}
                      for p in res["pads"] if p["kind"] == "waystone"],
        "landmarks": [{k: p.get(k) for k in ("name", "x", "y", "r", "height_m", "idea")}
                      for p in res["pads"] if p["kind"] == "landmark"],
        "stats": stats,
        "warnings": warnings,
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate the Lycantrope heightmap world.")
    ap.add_argument("--layout", type=Path, default=DEFAULT_LAYOUT)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--size", type=int, default=2048, help="pixels per side (2048 = 1 m/px)")
    ap.add_argument("--seed", type=int, default=None, help="override the layout's seed")
    ap.add_argument("--preview-size", type=int, default=1024)
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    layout = json.loads(args.layout.read_text(encoding="utf-8"))
    print(f"Generating {args.size}×{args.size} world from {args.layout.name} ...")
    t0 = time.perf_counter()
    res = generate(layout, args.size, args.seed)
    meta = write_outputs(layout, res, args.out, args.preview_size)
    print(f"Wrote {args.out} in {time.perf_counter() - t0:.1f}s (seed {meta['seed']})\n")
    print(f"{'biome':<14}{'area%':>7}{'min':>7}{'mean':>7}{'max':>7}{'water%':>8}{'steep%':>8}")
    for k, s in meta["stats"]["biomes"].items():
        print(f"{k:<14}{s['area_pct']:>7}{s['height_min']:>7}{s['height_mean']:>7}{s['height_max']:>7}"
              f"{s['water_pct']:>8}{s['unwalkable_pct']:>8}")
    print()
    for k, s in meta["stats"]["roads"].items():
        print(f"road {k:<16} slope p95 {s['slope_p95_deg']:>5}°  max {s['slope_max_deg']:>5}°  "
              f"underwater {s['underwater_pct']}%")
    if meta["warnings"]:
        print("\nWarnings:")
        for w in meta["warnings"]:
            print(f"  ! {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
