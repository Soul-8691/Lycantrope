"""Vectorized 2D gradient (Perlin) noise for the terrain generator.

Pure numpy, deterministic for a given seed, works on whole grids at once.
All functions take coordinate arrays (already divided by the feature scale)
and return float32 arrays of the same shape.
"""
from __future__ import annotations

import numpy as np

_G = np.array([[1, 1], [-1, 1], [1, -1], [-1, -1], [1, 0], [-1, 0], [0, 1], [0, -1]], dtype=np.float32)
_G /= np.linalg.norm(_G, axis=1, keepdims=True)
_GX, _GY = _G[:, 0].copy(), _G[:, 1].copy()


def _perm(seed: int) -> np.ndarray:
    p = np.random.default_rng(seed).permutation(256).astype(np.int32)
    return np.concatenate([p, p])


def perlin(x: np.ndarray, y: np.ndarray, seed: int = 0, period: int | None = None) -> np.ndarray:
    """Gradient noise, roughly in [-1, 1]. With `period`, it tiles every `period` units."""
    perm = _perm(seed)
    x = np.asarray(x, dtype=np.float32)
    y = np.asarray(y, dtype=np.float32)
    x0 = np.floor(x)
    y0 = np.floor(y)
    xf = x - x0
    yf = y - y0
    xi = x0.astype(np.int64)
    yi = y0.astype(np.int64)
    if period:
        xa, xb = xi % period, (xi + 1) % period
        ya, yb = yi % period, (yi + 1) % period
    else:
        xa, xb, ya, yb = xi, xi + 1, yi, yi + 1
    xa, xb, ya, yb = xa & 255, xb & 255, ya & 255, yb & 255

    def corner(ix, iy, dx, dy):
        h = perm[perm[ix] + iy] & 7
        return _GX[h] * dx + _GY[h] * dy

    n00 = corner(xa, ya, xf, yf)
    n10 = corner(xb, ya, xf - 1, yf)
    n01 = corner(xa, yb, xf, yf - 1)
    n11 = corner(xb, yb, xf - 1, yf - 1)
    u = xf * xf * xf * (xf * (xf * 6 - 15) + 10)
    v = yf * yf * yf * (yf * (yf * 6 - 15) + 10)
    nx0 = n00 + u * (n10 - n00)
    nx1 = n01 + u * (n11 - n01)
    return ((nx0 + v * (nx1 - nx0)) * 1.4142).astype(np.float32)


def fbm(x, y, octaves: int = 5, seed: int = 0, lacunarity: float = 2.0, gain: float = 0.5,
        period: int | None = None) -> np.ndarray:
    """Fractal Brownian motion, roughly in [-1, 1]. `period` (with lacunarity 2) makes it tile."""
    total = np.zeros(np.shape(x), dtype=np.float32)
    amp, freq, norm = 1.0, 1.0, 0.0
    for i in range(octaves):
        # offset each octave so lattice points don't line up
        p = int(round(period * freq)) if period else None
        total += amp * perlin(x * freq + 17.13 * i, y * freq - 9.71 * i, seed + i * 7919, p)
        norm += amp
        amp *= gain
        freq *= lacunarity
    return total / norm


def ridged(x, y, octaves: int = 6, seed: int = 0, lacunarity: float = 2.0, gain: float = 0.5,
           period: int | None = None) -> np.ndarray:
    """Ridged multifractal, in [0, 1]. Sharp crests: good for mountains and cracks."""
    total = np.zeros(np.shape(x), dtype=np.float32)
    weight = np.ones(np.shape(x), dtype=np.float32)
    amp, freq, norm = 1.0, 1.0, 0.0
    for i in range(octaves):
        p = int(round(period * freq)) if period else None
        n = 1.0 - np.abs(perlin(x * freq + 31.7 * i, y * freq + 5.3 * i, seed + i * 104729, p))
        n = n * n * weight
        weight = np.clip(n * 2.0, 0.0, 1.0)
        total += amp * n
        norm += amp
        amp *= gain
        freq *= lacunarity
    return total / norm


def worley(u: np.ndarray, v: np.ndarray, cells: int, seed: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Tileable cellular noise on the unit square.

    Returns (F1, F2, cell_id): distances (in cell units) to the nearest and
    second-nearest feature points, and a random value in [0, 1) per nearest cell.
    """
    rng = np.random.default_rng(seed)
    pts = rng.random((cells, cells, 2)).astype(np.float32)
    ids = rng.random((cells, cells)).astype(np.float32)
    px, py = u * cells, v * cells
    cx, cy = np.floor(px).astype(np.int64), np.floor(py).astype(np.int64)
    fx, fy = (px - cx).astype(np.float32), (py - cy).astype(np.float32)
    f1 = np.full(np.shape(u), np.inf, np.float32)
    f2 = np.full(np.shape(u), np.inf, np.float32)
    cid = np.zeros(np.shape(u), np.float32)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            nx, ny = (cx + ox) % cells, (cy + oy) % cells
            d = np.hypot(ox + pts[ny, nx, 0] - fx, oy + pts[ny, nx, 1] - fy)
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d))
            cid = np.where(closer, ids[ny, nx], cid)
            f1 = np.where(closer, d, f1)
    return f1, f2, cid
