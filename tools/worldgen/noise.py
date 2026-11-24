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


def perlin(x: np.ndarray, y: np.ndarray, seed: int = 0) -> np.ndarray:
    """Gradient noise, roughly in [-1, 1]."""
    perm = _perm(seed)
    x = np.asarray(x, dtype=np.float32)
    y = np.asarray(y, dtype=np.float32)
    x0 = np.floor(x)
    y0 = np.floor(y)
    xf = x - x0
    yf = y - y0
    xi = x0.astype(np.int64) & 255
    yi = y0.astype(np.int64) & 255

    def corner(ix, iy, dx, dy):
        h = perm[perm[ix] + iy] & 7
        return _GX[h] * dx + _GY[h] * dy

    n00 = corner(xi, yi, xf, yf)
    n10 = corner(xi + 1, yi, xf - 1, yf)
    n01 = corner(xi, yi + 1, xf, yf - 1)
    n11 = corner(xi + 1, yi + 1, xf - 1, yf - 1)
    u = xf * xf * xf * (xf * (xf * 6 - 15) + 10)
    v = yf * yf * yf * (yf * (yf * 6 - 15) + 10)
    nx0 = n00 + u * (n10 - n00)
    nx1 = n01 + u * (n11 - n01)
    return ((nx0 + v * (nx1 - nx0)) * 1.4142).astype(np.float32)


def fbm(x, y, octaves: int = 5, seed: int = 0, lacunarity: float = 2.0, gain: float = 0.5) -> np.ndarray:
    """Fractal Brownian motion, roughly in [-1, 1]."""
    total = np.zeros(np.shape(x), dtype=np.float32)
    amp, freq, norm = 1.0, 1.0, 0.0
    for i in range(octaves):
        # offset each octave so lattice points don't line up
        total += amp * perlin(x * freq + 17.13 * i, y * freq - 9.71 * i, seed + i * 7919)
        norm += amp
        amp *= gain
        freq *= lacunarity
    return total / norm


def ridged(x, y, octaves: int = 6, seed: int = 0, lacunarity: float = 2.0, gain: float = 0.5) -> np.ndarray:
    """Ridged multifractal, in [0, 1]. Sharp crests: good for mountains."""
    total = np.zeros(np.shape(x), dtype=np.float32)
    weight = np.ones(np.shape(x), dtype=np.float32)
    amp, freq, norm = 1.0, 1.0, 0.0
    for i in range(octaves):
        n = 1.0 - np.abs(perlin(x * freq + 31.7 * i, y * freq + 5.3 * i, seed + i * 104729))
        n = n * n * weight
        weight = np.clip(n * 2.0, 0.0, 1.0)
        total += amp * n
        norm += amp
        amp *= gain
        freq *= lacunarity
    return total / norm
