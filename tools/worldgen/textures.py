#!/usr/bin/env python3
"""
Procedural ground textures (ART-08)
==================================

Generates tileable 512×512 RGBA ground materials with numpy noise, no hand
painting and no AI credits. RGB is albedo (sRGB) and A is a height value
the terrain shader uses for natural height-based blending between materials.

Writes ``assets/textures/ground/<name>.png``. Material settings (tile size,
which biome uses which material) live in ``data/world/materials.json``.

Usage::

    python tools/worldgen/textures.py            # all materials
    python tools/worldgen/textures.py grass rock # just some
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
from noise import fbm, ridged, worley  # noqa: E402

SIZE = 512
OUT = ROOT / "assets" / "textures" / "ground"


def _grid(size: int = SIZE):
    c = (np.arange(size, dtype=np.float32) + 0.5) / size
    return np.meshgrid(c, c)


U, V = _grid()


def F(scale: int, octaves: int, seed: int) -> np.ndarray:
    """Tileable fbm in [-1, 1] with `scale` features across the texture."""
    return fbm(U * scale, V * scale, octaves, seed, period=scale)


def R(scale: int, octaves: int, seed: int) -> np.ndarray:
    return ridged(U * scale, V * scale, octaves, seed, period=scale)


def c(*rgb: float) -> np.ndarray:
    return np.array(rgb, np.float32)


def lerp(a, b, t):
    t = np.asarray(t, np.float32)
    if t.ndim == 2:
        t = t[..., None]
    return a + (b - a) * t


def ss(e0: float, e1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def n01(a: np.ndarray) -> np.ndarray:
    return np.clip(a * 0.5 + 0.5, 0, 1)


# --------------------------------------------------------------------------- #
# materials: each returns (rgb HxWx3 in 0..1 sRGB, height HxW in 0..1)
# --------------------------------------------------------------------------- #

def grass():
    big, mid, fine = n01(F(3, 4, 11)), n01(F(12, 4, 12)), n01(F(96, 2, 13))
    rgb = lerp(c(0.22, 0.33, 0.10), c(0.40, 0.51, 0.17), big * 0.6 + mid * 0.4)
    rgb = lerp(rgb, c(0.52, 0.52, 0.22), ss(0.62, 0.8, n01(F(4, 3, 14))) * 0.6)   # dry patches
    f1, _, _ = worley(U, V, 20, 15)
    rgb = lerp(rgb, c(0.36, 0.28, 0.17), ss(0.12, 0.0, f1) * ss(0.55, 0.7, mid))   # bare spots
    rgb *= (0.78 + 0.44 * fine)[..., None]                                        # blades
    return rgb, 0.35 + 0.45 * fine + 0.2 * mid


def forest():
    big, fine = n01(F(4, 4, 21)), n01(F(64, 3, 22))
    rgb = lerp(c(0.13, 0.17, 0.08), c(0.25, 0.22, 0.12), big)
    f1, _, cid = worley(U, V, 48, 23)                                             # leaf litter
    leaf = ss(0.32, 0.18, f1) * (cid > 0.45)
    leaf_col = lerp(c(0.42, 0.24, 0.09), c(0.55, 0.40, 0.14), cid)
    rgb = lerp(rgb, leaf_col, leaf * 0.85)
    needles = ss(0.75, 0.95, n01(F(128, 2, 24)))
    rgb = lerp(rgb, c(0.30, 0.20, 0.10), needles * 0.5)
    rgb *= (0.8 + 0.4 * fine)[..., None]
    return rgb, 0.3 + 0.4 * fine + 0.3 * leaf


def mud():
    big, mid, fine = n01(F(3, 4, 31)), n01(F(10, 4, 32)), n01(F(80, 2, 33))
    rgb = lerp(c(0.17, 0.13, 0.09), c(0.30, 0.23, 0.15), big)
    wet = ss(0.55, 0.7, mid)
    rgb = lerp(rgb, rgb * 0.55, wet)                                              # wet hollows
    f1, _, _ = worley(U, V, 36, 34)
    stones = ss(0.22, 0.12, f1) * (1 - wet)
    rgb = lerp(rgb, c(0.36, 0.33, 0.28), stones * 0.7)
    rgb *= (0.88 + 0.24 * fine)[..., None]
    return rgb, np.clip(0.5 - 0.35 * wet + 0.4 * stones + 0.1 * fine, 0, 1)


def snow():
    big, mid, fine = n01(F(3, 4, 41)), n01(F(14, 4, 42)), n01(F(128, 2, 43))
    rgb = lerp(c(0.74, 0.80, 0.90), c(0.92, 0.94, 0.97), ss(0.25, 0.75, big * 0.6 + mid * 0.4))
    sparkle = (fine > 0.86).astype(np.float32)
    rgb = np.clip(rgb + sparkle[..., None] * 0.08, 0, 1)
    return rgb, 0.3 + 0.5 * mid + 0.2 * big


def ash():
    big, fine = n01(F(4, 4, 51)), n01(F(96, 2, 52))
    rgb = lerp(c(0.17, 0.16, 0.16), c(0.32, 0.30, 0.29), big)
    cracks = ss(0.82, 0.95, R(6, 4, 53))
    rgb = lerp(rgb, c(0.34, 0.11, 0.05), cracks * 0.8)                            # cooling cracks
    f1, _, _ = worley(U, V, 40, 54)
    cinder = ss(0.2, 0.08, f1)
    rgb = lerp(rgb, c(0.08, 0.07, 0.07), cinder * 0.8)
    rgb *= (0.85 + 0.3 * fine)[..., None]
    return rgb, np.clip(0.55 - 0.4 * cracks + 0.3 * cinder + 0.1 * fine, 0, 1)


def darkstone():
    f1, f2, cid = worley(U, V, 7, 61)                                             # flagstones
    edge = f2 - f1
    mortar = ss(0.09, 0.03, edge)
    big, fine = n01(F(5, 4, 62)), n01(F(80, 3, 63))
    tint = lerp(c(0.16, 0.14, 0.20), c(0.28, 0.25, 0.31), cid)
    rgb = tint * (0.8 + 0.35 * big)[..., None]
    rgb = lerp(rgb, c(0.07, 0.06, 0.08), mortar)
    rgb *= (0.85 + 0.3 * fine)[..., None]
    return rgb, np.clip(ss(0.0, 0.25, edge) * 0.8 + 0.2 * fine, 0, 1)


def rock():
    big, mid, fine = n01(F(3, 5, 71)), n01(F(12, 4, 72)), n01(F(96, 2, 73))
    strata = 0.5 + 0.5 * np.sin((V * 3 + F(2, 3, 74) * 0.8) * 2 * np.pi)
    rgb = lerp(c(0.22, 0.22, 0.23), c(0.40, 0.39, 0.38), big * 0.6 + mid * 0.28 + strata * 0.12)
    cracks = ss(0.86, 0.97, R(5, 5, 75))
    rgb = lerp(rgb, c(0.14, 0.13, 0.12), cracks)
    lichen = ss(0.72, 0.85, n01(F(8, 4, 76)))
    rgb = lerp(rgb, c(0.48, 0.50, 0.27), lichen * 0.5)
    rgb *= (0.82 + 0.36 * fine)[..., None]
    return rgb, np.clip(0.3 + 0.4 * mid + 0.3 * fine - 0.3 * cracks, 0, 1)


def dirt():
    big, fine = n01(F(4, 4, 81)), n01(F(96, 2, 82))
    rgb = lerp(c(0.38, 0.29, 0.19), c(0.52, 0.42, 0.28), big)
    f1, _, cid = worley(U, V, 28, 83)                                             # pebbles
    peb = ss(0.3, 0.18, f1)
    rgb = lerp(rgb, lerp(c(0.45, 0.43, 0.40), c(0.62, 0.60, 0.56), cid), peb)
    rgb *= (0.86 + 0.28 * fine)[..., None]
    return rgb, np.clip(0.3 + 0.55 * peb + 0.15 * fine, 0, 1)


def pebbles():
    """Riverbank stones: rounded pebbles of mixed colour in damp silt, with smaller gravel between."""
    silt = lerp(c(0.30, 0.27, 0.22), c(0.40, 0.36, 0.29), n01(F(6, 3, 91)))
    f1, f2, cid = worley(U, V, 22, 92)                                            # large stones
    edge = f2 - f1                                                                # 0 on the gaps
    stone = ss(0.06, 0.2, edge) * ss(0.62, 0.38, f1)
    dome = np.sqrt(np.clip(1.0 - (f1 / 0.62) ** 2, 0, 1)) * stone                 # rounded tops
    palette = [c(0.46, 0.45, 0.43), c(0.50, 0.48, 0.43), c(0.41, 0.42, 0.43),
               c(0.54, 0.53, 0.50), c(0.44, 0.40, 0.35)]
    k = np.clip((cid * len(palette)).astype(int), 0, len(palette) - 1)
    stone_col = np.stack([palette[i] for i in range(len(palette))])[k]
    g1, g2, gid = worley(U, V, 64, 93)                                             # gravel
    gravel = ss(0.03, 0.12, g2 - g1) * ss(0.7, 0.4, g1) * (1 - stone)
    gravel_col = lerp(c(0.40, 0.38, 0.35), c(0.58, 0.55, 0.50), gid)
    rgb = lerp(silt, gravel_col, gravel * 0.85)
    shade = (0.78 + 0.32 * dome)[..., None]                                       # lit tops, darker rims
    rgb = lerp(rgb, stone_col * shade, stone)
    rgb *= (0.92 + 0.16 * n01(F(48, 2, 94)))[..., None]
    return rgb, np.clip(0.15 + 0.75 * dome + 0.25 * gravel, 0, 1)


MATERIALS = {f.__name__: f for f in (grass, forest, mud, snow, ash, darkstone, rock, dirt, pebbles)}


def build(name: str, out: Path = OUT) -> Path:
    rgb, height = MATERIALS[name]()
    rgba = np.dstack([np.clip(rgb, 0, 1), np.clip(height, 0, 1)])
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{name}.png"
    Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), "RGBA").save(path, optimize=True)
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate tileable ground textures.")
    ap.add_argument("names", nargs="*", choices=[[]] + list(MATERIALS), metavar="NAME")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)
    for name in args.names or MATERIALS:
        print("wrote", build(name, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
