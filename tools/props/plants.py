r"""Plants and garden pieces made in code (no Meshy credits): low-poly meshes built from stems,
blades, petals, canes and blobs, coloured from a small palette texture so the game draws them like
any textured prop.

    .venv\Scripts\python.exe tools/props/plants.py            # preview sheet of every plant (scratch)
    data/props.json: "source": "code:<name>"  ->  tools/props/build.py builds it like any other prop

Names: fern (PLT-02), wildflowers (PLT-03), bramble (PLT-04), reeds (PLT-07), cottage_bed (PLT-15),
lavender (PLT-16), climbing_rose (PLT-17), sunflowers (PLT-18), window_box (PLT-19).
Everything is made in metres, standing on y = 0, front toward +z; a seed gives the same plant each time.
"""
from __future__ import annotations

import math

import numpy as np
import trimesh
from PIL import Image

# palette: name -> RGB (0..255); each colour is one 8x8 cell of a 64x64 texture
PALETTE = {
    "leaf_dark": (52, 86, 38), "leaf": (78, 122, 48), "leaf_light": (112, 152, 62), "fern": (88, 132, 50),
    "stem": (92, 120, 58), "reed": (128, 140, 72), "reed_dry": (158, 146, 92), "cattail": (98, 62, 36),
    "poppy": (196, 40, 32), "cornflower": (70, 98, 196), "daisy": (236, 232, 220), "yellow": (232, 186, 40),
    "dark_centre": (40, 30, 24), "lavender": (128, 98, 176), "lavender_leaf": (120, 138, 104),
    "pink": (222, 126, 160), "rose": (180, 30, 52), "rose_pink": (226, 120, 150), "orange": (226, 128, 32),
    "foxglove": (150, 82, 160), "wood": (122, 88, 56), "wood_dark": (84, 58, 38), "stone": (128, 124, 116),
    "soil": (74, 54, 38), "berry": (36, 22, 40), "geranium": (206, 44, 48), "ivy": (56, 96, 46),
    "sunflower": (240, 190, 30), "seedhead": (82, 52, 26), "bark": (96, 72, 50),
}
NAMES = list(PALETTE)
CELL, GRID = 8, 8


def palette_image() -> Image.Image:
    img = Image.new("RGB", (CELL * GRID, CELL * GRID), (255, 0, 255))
    for i, name in enumerate(NAMES):
        x, y = (i % GRID) * CELL, (i // GRID) * CELL
        img.paste(PALETTE[name], (x, y, x + CELL, y + CELL))
    return img


def uv_of(name: str) -> tuple[float, float]:
    i = NAMES.index(name)
    u = ((i % GRID) + 0.5) / GRID
    v = 1.0 - ((i // GRID) + 0.5) / GRID              # glTF: v = 0 at the top of the image
    return u, v


class Builder:
    """Collects triangles, each vertex carrying the UV of its palette colour."""

    def __init__(self, seed: int = 1) -> None:
        self.v: list[np.ndarray] = []
        self.f: list[np.ndarray] = []
        self.uv: list[np.ndarray] = []
        self.n = 0
        self.rng = np.random.default_rng(seed)

    def add(self, verts, faces, color: str) -> None:
        verts = np.asarray(verts, float).reshape(-1, 3)
        self.v.append(verts)
        self.f.append(np.asarray(faces, int).reshape(-1, 3) + self.n)
        self.uv.append(np.tile(uv_of(color), (len(verts), 1)))
        self.n += len(verts)

    # -------------------------------------------------------------- shapes
    def strip(self, points, widths, side, color: str) -> None:
        """A flat ribbon along a polyline (blades, fronds, leaves); side = its width direction."""
        pts = np.asarray(points, float)
        side = np.asarray(side, float)
        side = side / (np.linalg.norm(side) + 1e-9)
        verts = []
        for p, w in zip(pts, widths):
            verts += [p - side * w / 2, p + side * w / 2]
        faces = []
        for i in range(len(pts) - 1):
            a, b, c, d = 2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3
            faces += [(a, b, d), (a, d, c)]
        self.add(verts, faces, color)

    def tube(self, points, radius, color: str, sides: int = 4, taper: float = 1.0) -> None:
        """A thin tube along a polyline (stems, canes)."""
        pts = np.asarray(points, float)
        verts, faces = [], []
        for i, p in enumerate(pts):
            d = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
            d /= np.linalg.norm(d) + 1e-9
            a = np.cross(d, [0.0, 0.0, 1.0] if abs(d[2]) < 0.9 else [1.0, 0.0, 0.0])
            a /= np.linalg.norm(a)
            b = np.cross(d, a)
            r = radius * (1.0 - (1.0 - taper) * i / max(1, len(pts) - 1))
            for k in range(sides):
                t = math.tau * k / sides
                verts.append(p + (a * math.cos(t) + b * math.sin(t)) * r)
        for i in range(len(pts) - 1):
            for k in range(sides):
                a0, a1 = i * sides + k, i * sides + (k + 1) % sides
                b0, b1 = a0 + sides, a1 + sides
                faces += [(a0, a1, b1), (a0, b1, b0)]
        self.add(verts, faces, color)

    def blob(self, centre, radius, color: str, squash=(1.0, 1.0, 1.0), detail: int = 0) -> None:
        """A rough low-poly lump (leaf clumps, berries, rose heads)."""
        ico = trimesh.creation.icosphere(subdivisions=detail)
        v = ico.vertices * radius * np.asarray(squash)
        v *= 1.0 + self.rng.uniform(-0.12, 0.12, (len(v), 1))
        self.add(v + np.asarray(centre, float), ico.faces, color)

    def flower(self, centre, normal, radius, petals: int, color: str, centre_color: str | None = None,
               inner: float = 0.35) -> None:
        """A flat star of petals facing `normal`, with an optional raised centre."""
        c = np.asarray(centre, float)
        n = np.asarray(normal, float)
        n /= np.linalg.norm(n)
        a = np.cross(n, [0.0, 1.0, 0.0] if abs(n[1]) < 0.9 else [1.0, 0.0, 0.0])
        a /= np.linalg.norm(a)
        b = np.cross(n, a)
        rot = self.rng.uniform(0, math.tau)
        verts = [c + n * radius * 0.08]
        for k in range(petals * 2):
            t = rot + math.pi * k / petals
            r = radius if k % 2 == 0 else radius * inner
            verts.append(c + (a * math.cos(t) + b * math.sin(t)) * r)
        m = petals * 2
        faces = [(0, 1 + k, 1 + (k + 1) % m) for k in range(m)]
        self.add(verts, faces, color)
        if centre_color:
            self.cone(c, c + n * radius * 0.25, radius * 0.32, centre_color, sides=4)

    def box(self, centre, size, color: str) -> None:
        bx = trimesh.creation.box(extents=size)
        self.add(bx.vertices + np.asarray(centre, float), bx.faces, color)

    def cone(self, base, tip, radius, color: str, sides: int = 5) -> None:
        base, tip = np.asarray(base, float), np.asarray(tip, float)
        d = tip - base
        d /= np.linalg.norm(d) + 1e-9
        a = np.cross(d, [0.0, 0.0, 1.0] if abs(d[2]) < 0.9 else [1.0, 0.0, 0.0])
        a /= np.linalg.norm(a)
        b = np.cross(d, a)
        verts = [tip] + [base + (a * math.cos(math.tau * k / sides) + b * math.sin(math.tau * k / sides)) * radius
                         for k in range(sides)]
        faces = [(0, 1 + k, 1 + (k + 1) % sides) for k in range(sides)]
        self.add(verts, faces, color)

    # -------------------------------------------------------------- helpers
    def arc(self, base, direction, length, rise, droop, steps=6):
        """Points of an arching stem: up and out from base, then bending down by droop."""
        base, d = np.asarray(base, float), np.asarray(direction, float)
        d = d / (np.linalg.norm(d) + 1e-9)
        pts = []
        for i in range(steps + 1):
            t = i / steps
            pts.append(base + d * length * t + np.array([0.0, rise * math.sin(math.pi * 0.5 * t * 1.4) - droop * t * t, 0.0]))
        return np.array(pts)

    def mesh(self) -> trimesh.Trimesh:
        mat = trimesh.visual.material.PBRMaterial(baseColorTexture=palette_image(), metallicFactor=0.0,
                                                  roughnessFactor=1.0)
        vis = trimesh.visual.TextureVisuals(uv=np.vstack(self.uv), material=mat)
        return trimesh.Trimesh(np.vstack(self.v), np.vstack(self.f), visual=vis, process=False)


def _around(rng, n, radius):
    """n points scattered on a disc, a little clumped toward the middle."""
    a = rng.uniform(0, math.tau, n)
    r = radius * np.sqrt(rng.uniform(0, 1, n)) * rng.uniform(0.6, 1.0, n)
    return np.stack([r * np.cos(a), np.zeros(n), r * np.sin(a)], axis=1)


# ------------------------------------------------------------------ plants
def fern(seed=2) -> trimesh.Trimesh:
    """PLT-02 Bracken fern clump: arching fronds with paired leaflets."""
    b = Builder(seed)
    for k in range(9):
        ang = math.tau * k / 9 + b.rng.uniform(-0.25, 0.25)
        d = np.array([math.cos(ang), 0.0, math.sin(ang)])
        L = b.rng.uniform(0.55, 0.85)
        spine = b.arc(b.rng.uniform(-0.04, 0.04, 3) * [1, 0, 1], d, L * 0.8, rise=b.rng.uniform(0.75, 1.0), droop=0.35, steps=7)
        side = np.cross(d, [0.0, 1.0, 0.0])
        b.strip(spine, np.linspace(0.025, 0.006, len(spine)), side, "stem")
        for i in range(1, len(spine) - 1):
            p = spine[i]
            leaf = 0.17 * (1.0 - i / len(spine)) + 0.04
            for s in (-1, 1):
                tip = p + side * s * leaf + np.array([0.0, -0.03, 0.0]) + d * 0.03
                b.add([p - d * 0.025, p + d * 0.035, tip], [(0, 1, 2)], "fern" if k % 2 else "leaf")
    return b.mesh()


def wildflowers(seed=3) -> trimesh.Trimesh:
    """PLT-03 Wildflower patch: poppies, cornflowers and daisies among grass."""
    b = Builder(seed)
    kinds = [("poppy", 5, 0.075, "dark_centre"), ("cornflower", 8, 0.055, None), ("daisy", 10, 0.06, "yellow")]
    for p in _around(b.rng, 30, 0.5):                         # heads big enough to read above the grass
        kind, petals, r, cc = kinds[int(b.rng.integers(0, 3))]
        h = b.rng.uniform(0.35, 0.65)
        top = p + np.array([b.rng.uniform(-0.05, 0.05), h, b.rng.uniform(-0.05, 0.05)])
        b.strip([p, (p + top) / 2, top], [0.012, 0.009, 0.006], [1.0, 0.0, 0.3], "stem")
        normal = np.array([b.rng.uniform(-0.4, 0.4), 1.0, b.rng.uniform(-0.4, 0.4)])
        b.flower(top, normal, r, petals, kind, cc)
    for p in _around(b.rng, 22, 0.55):                         # grass between them
        h = b.rng.uniform(0.15, 0.32)
        lean = np.array([b.rng.uniform(-0.08, 0.08), h, b.rng.uniform(-0.08, 0.08)])
        b.strip([p, p + lean * 0.5, p + lean], [0.025, 0.015, 0.0], [1.0, 0.0, b.rng.uniform(-1, 1)], "leaf_light")
    return b.mesh()


def bramble(seed=4) -> trimesh.Trimesh:
    """PLT-04 Bramble thicket: arching thorny canes, leaf clumps and blackberries."""
    b = Builder(seed)
    clumps = []
    for k in range(9):
        ang = math.tau * k / 9 + b.rng.uniform(-0.3, 0.3)
        d = np.array([math.cos(ang), 0.0, math.sin(ang)])
        cane = b.arc(b.rng.uniform(-0.15, 0.15, 3) * [1, 0, 1], d, b.rng.uniform(0.7, 1.0), rise=b.rng.uniform(0.7, 1.0),
                     droop=0.8, steps=6)
        b.tube(cane, 0.022, "bark", sides=4, taper=0.5)
        for i in (1, 2, 3, 4):
            clumps.append(cane[i] * [1.0, 0.75, 1.0])
            for _ in range(2):                                   # thorns
                tp = cane[i] + b.rng.uniform(-1, 1, 3) * 0.02
                b.cone(tp, tp + b.rng.normal(0, 1, 3) * 0.04, 0.008, "bark", sides=3)
    for c in clumps:
        b.blob(c + [0.0, 0.04, 0.0], b.rng.uniform(0.16, 0.26), "leaf_dark" if b.rng.random() < 0.6 else "leaf",
               squash=(1.2, 0.85, 1.2))
    for p in _around(b.rng, 7, 0.45):                            # the heart of the thicket
        b.blob(p + [0.0, b.rng.uniform(0.2, 0.45), 0.0], b.rng.uniform(0.25, 0.35), "leaf_dark", squash=(1.2, 0.9, 1.2))
    for c in clumps[::2]:                                       # blackberry clusters on the outside
        out = c + np.array([c[0], 0.0, c[2]]) / (np.hypot(c[0], c[2]) + 1e-6) * 0.17
        for _ in range(3):
            b.blob(out + b.rng.uniform(-0.03, 0.03, 3), 0.022, "berry")
    return b.mesh()


def reeds(seed=5) -> trimesh.Trimesh:
    """PLT-07 Reeds and cattails: tall tapered blades with a few brown seed heads."""
    b = Builder(seed)
    for p in _around(b.rng, 28, 0.35):
        h = b.rng.uniform(0.9, 1.6)
        bend = np.array([b.rng.uniform(-0.25, 0.25), 0.0, b.rng.uniform(-0.25, 0.25)])
        pts = [p + np.array([0.0, h * t, 0.0]) + bend * t * t for t in np.linspace(0, 1, 5)]
        b.strip(pts, np.linspace(0.035, 0.0, 5), [1.0, 0.0, b.rng.uniform(-1, 1)],
                "reed" if b.rng.random() < 0.75 else "reed_dry")
    for p in _around(b.rng, 6, 0.25):
        h = b.rng.uniform(1.2, 1.7)
        top = p + np.array([b.rng.uniform(-0.06, 0.06), h, b.rng.uniform(-0.06, 0.06)])
        b.tube([p, top], 0.008, "stem", sides=3)
        b.tube([top - [0, 0.2, 0], top - [0, 0.04, 0]], 0.028, "cattail", sides=6)
    return b.mesh()


def lavender(seed=6, radius=0.4) -> trimesh.Trimesh:
    """PLT-16 Lavender bush: a grey-green mound with purple flower spikes."""
    b = Builder(seed)
    b.blob([0.0, radius * 0.3, 0.0], radius * 0.75, "lavender_leaf", squash=(1.0, 0.6, 1.0), detail=1)
    for p in _around(b.rng, 70, radius * 0.75):
        base = p + [0.0, radius * 0.35, 0.0]
        out = np.array([p[0], 0.0, p[2]]) * 0.6
        top = base + out + [0.0, b.rng.uniform(0.22, 0.38), 0.0]
        b.strip([base, top], [0.008, 0.005], [1.0, 0.0, 0.5], "stem")
        b.cone(top - (top - base) * 0.25, top + (top - base) * 0.12, 0.018, "lavender", sides=4)
    return b.mesh()


def cottage_bed(seed=7) -> trimesh.Trimesh:
    """PLT-15 Cottage garden bed: stone edging, hollyhocks at the back, foxgloves, marigolds in front."""
    b = Builder(seed)
    W, D = 1.8, 0.6
    b.box([0.0, 0.04, 0.0], [W, 0.08, D], "soil")
    for i in range(9):                                         # stone edging along the front and sides
        x = -W / 2 + W * (i + 0.5) / 9
        b.box([x, 0.07, D / 2 + 0.04], [W / 9 * 0.92, 0.14, 0.09], "stone")
    for s in (-1, 1):
        b.box([s * (W / 2 + 0.04), 0.07, 0.0], [0.09, 0.14, D + 0.17], "stone")
    for x in np.linspace(-0.7, 0.7, 4):                         # hollyhocks: tall spikes of pink discs
        base = np.array([x + b.rng.uniform(-0.08, 0.08), 0.08, -D * 0.3])
        h = b.rng.uniform(1.2, 1.6)
        b.tube([base, base + [0, h, 0]], 0.012, "stem", sides=3)
        for t in np.linspace(0.45, 0.95, 6):
            b.flower(base + [0, h * t, 0.03], [0.0, 0.2, 1.0], 0.1 * (1.15 - t * 0.5), 5, "pink", "yellow", inner=0.6)
        b.blob(base + [0, 0.2, 0], 0.12, "leaf", squash=(1.2, 0.7, 1.0))
    for x in np.linspace(-0.55, 0.55, 3):                       # foxgloves: purple bells down a spike
        base = np.array([x, 0.08, 0.0])
        h = b.rng.uniform(0.75, 0.95)
        b.tube([base, base + [0, h, 0]], 0.01, "stem", sides=3)
        for t in np.linspace(0.45, 0.95, 7):
            p = base + [0.0, h * t, 0.025]
            b.cone(p + [0, 0.03, 0], p + [0, -0.07, 0.03], 0.034, "foxglove", sides=5)
    for x in np.linspace(-0.75, 0.75, 7):                       # marigolds in front
        p = np.array([x + b.rng.uniform(-0.05, 0.05), 0.2, D * 0.25])
        b.blob(p - [0, 0.07, 0], 0.1, "leaf_light", squash=(1.2, 0.7, 1.2))
        for dx in (-0.05, 0.05):
            b.flower(p + [dx, 0.02, 0.0], [0.0, 1.0, 0.4], 0.07, 8, "orange", "yellow", inner=0.65)
    return b.mesh()


def climbing_rose(seed=8) -> trimesh.Trimesh:
    """PLT-17 Climbing rose on a wooden trellis (stands against a wall, front toward +z)."""
    b = Builder(seed)
    W, H = 1.2, 1.9
    for x in np.linspace(-W / 2, W / 2, 4):                     # trellis uprights and rails
        b.box([x, H / 2, 0.0], [0.04, H, 0.03], "wood")
    for y in np.linspace(0.3, H - 0.05, 5):
        b.box([0.0, y, 0.0], [W + 0.04, 0.035, 0.03], "wood")
    for _ in range(22):                                          # foliage climbing it, thicker low down
        y = H * (b.rng.uniform(0, 1) ** 0.8)
        x = b.rng.uniform(-W / 2, W / 2) * (0.6 + 0.4 * (y / H))
        b.blob([x, y, 0.06], b.rng.uniform(0.1, 0.17), "leaf_dark" if b.rng.random() < 0.5 else "leaf",
               squash=(1.1, 0.9, 0.6))
    for _ in range(26):                                          # roses on the outside of the foliage
        y = H * b.rng.uniform(0.15, 1.0)
        x = b.rng.uniform(-W / 2, W / 2) * 0.95
        b.blob([x, y, 0.15], b.rng.uniform(0.035, 0.05), "rose" if b.rng.random() < 0.6 else "rose_pink",
               detail=1)
    return b.mesh()


def sunflowers(seed=9) -> trimesh.Trimesh:
    """PLT-18 Sunflower row: five tall sunflowers in a line, heads turned to the front (+z)."""
    b = Builder(seed)
    for i, x in enumerate(np.linspace(-1.0, 1.0, 5)):
        h = b.rng.uniform(1.6, 2.1)
        base = np.array([x, 0.0, b.rng.uniform(-0.08, 0.08)])
        top = base + [b.rng.uniform(-0.05, 0.05), h, 0.0]
        b.tube([base, (base + top) / 2, top], 0.025, "stem", sides=5, taper=0.6)
        for t in (0.3, 0.5, 0.7):                                  # big leaves
            p = base + (top - base) * t
            for s in (-1, 1):
                tip = p + [s * 0.32, -0.04, 0.05]
                b.add([p, p + [s * 0.12, 0.09, 0.03], tip, p + [s * 0.12, -0.08, 0.02]], [(0, 1, 2), (0, 2, 3)], "leaf")
        face = top + [0.0, 0.0, 0.04]
        normal = [0.0, -0.25, 1.0]
        b.flower(face, normal, 0.2, 14, "sunflower", None, inner=0.6)
        b.blob(face + [0.0, 0.0, 0.03], 0.1, "seedhead", squash=(1.0, 1.0, 0.35))
    return b.mesh()


def window_box(seed=10) -> trimesh.Trimesh:
    """PLT-19 Window flower box: a planter on two posts (stands under a window), red geraniums, ivy."""
    b = Builder(seed)
    W, top = 0.95, 0.85
    for s in (-1, 1):
        b.box([s * (W / 2 - 0.08), top / 2, 0.0], [0.06, top, 0.06], "wood_dark")
    b.box([0.0, top + 0.1, 0.0], [W, 0.2, 0.24], "wood")
    b.box([0.0, top + 0.2, 0.0], [W - 0.06, 0.02, 0.18], "soil")
    for x in np.linspace(-0.35, 0.35, 5):
        p = np.array([x, top + 0.3, b.rng.uniform(-0.04, 0.04)])
        b.blob(p, 0.1, "leaf", squash=(1.2, 0.8, 1.0))
        for _ in range(3):
            b.blob(p + b.rng.uniform(-0.06, 0.06, 3) + [0, 0.08, 0], 0.035, "geranium", detail=1)
    for x in np.linspace(-0.4, 0.4, 6):                          # ivy trailing over the front
        start = np.array([x, top + 0.2, 0.12])
        L = b.rng.uniform(0.2, 0.45)
        pts = [start + [b.rng.uniform(-0.02, 0.02), -L * t, 0.02 * math.sin(t * 3)] for t in np.linspace(0, 1, 5)]
        b.strip(pts, np.linspace(0.06, 0.03, 5), [1.0, 0.0, 0.0], "ivy")
    return b.mesh()


PLANTS = {"fern": fern, "wildflowers": wildflowers, "bramble": bramble, "reeds": reeds, "cottage_bed": cottage_bed,
          "lavender": lavender, "climbing_rose": climbing_rose, "sunflowers": sunflowers, "window_box": window_box}


def make(name: str) -> trimesh.Trimesh:
    if name not in PLANTS:
        raise KeyError(f"no plant called '{name}' (have: {', '.join(PLANTS)})")
    return PLANTS[name]()


if __name__ == "__main__":
    for name, fn in PLANTS.items():
        m = fn()
        print(f"  {name:<14} {len(m.faces):>5} tris   {m.extents[0]:.2f} x {m.extents[1]:.2f} x {m.extents[2]:.2f} m")
