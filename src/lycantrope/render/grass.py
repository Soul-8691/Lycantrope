"""Grass (ART-10): instanced tufts around the camera, placed and shaped entirely on the GPU.

Every instance is a cell in a grid that follows the camera (snapped to whole cells, so tufts
don't swim). The vertex shader hashes the cell's world position for jitter, turn and size,
reads the terrain height, biome weights, slope, water and road maps, and scales the tuft to
nothing where grass shouldn't grow. Height comes from a large "tall grass" noise field, so
meadows have short lawns and knee- to waist-high patches. Wind bends the tips.
"""
from __future__ import annotations

import math

from pyglm import glm
import moderngl
import numpy as np

from lycantrope.render.shaders import ShaderLibrary, set_uniform

CELL_M = 1.2            # one tuft per cell
RADIUS_M = 50.0         # grass is drawn this far from the camera
NEAR_M = 24.0           # full clumps inside this; simpler, wider ones beyond
# how much each biome grows (splat channel order from meta.json; unknown names get 0)
BIOME_GRASS = {"brackenvale": 1.0, "wolfwood": 0.75, "blackmire": 0.55, "frostfang": 0.12,
               "ashen": 0.0, "duskhold": 0.08, "boundary": 0.0}


def tuft_mesh(blades: int = 14, segments: int = 3, seed: int = 3) -> np.ndarray:
    """A clump of tapered, slightly curved blades, 1 m tall. Rows: x y z, t (0 base .. 1 tip)."""
    rng = np.random.default_rng(seed)
    tris = []
    for _ in range(blades):
        ang = rng.uniform(0, math.tau)
        lean = rng.uniform(0.06, 0.25)
        h = rng.uniform(0.6, 1.0)
        off = rng.uniform(-0.38, 0.38, 2)
        w0 = rng.uniform(0.035, 0.06)
        d = np.array([math.cos(ang), math.sin(ang)])          # lean direction
        side = np.array([-d[1], d[0]])                        # blade width direction
        rows = []
        for k in range(segments + 1):
            t = k / segments
            bend = lean * t * t * h
            c = np.array([off[0] + d[0] * bend, t * h, off[1] + d[1] * bend])
            w = w0 * (1.0 - t * 0.9)
            rows.append((c + np.array([side[0], 0, side[1]]) * w, c - np.array([side[0], 0, side[1]]) * w, t))
        for k in range(segments):
            (a0, b0, t0), (a1, b1, t1) = rows[k], rows[k + 1]
            tris += [(*a0, t0), (*b0, t0), (*a1, t1), (*b0, t0), (*b1, t1), (*a1, t1)]
    return np.array(tris, dtype=np.float32)


class Grass:
    def __init__(self, ctx: moderngl.Context, shaders: ShaderLibrary, world, terrain) -> None:
        self.ctx = ctx
        self.shaders = shaders
        self.world = world
        self.terrain = terrain
        near_mesh, far_mesh = tuft_mesh(), tuft_mesh(blades=6, segments=2, seed=5)
        self.parts = []
        n = int(RADIUS_M / CELL_M)
        i = np.arange(-n, n + 1)
        gx, gz = np.meshgrid(i, i)
        keep = np.hypot(gx, gz) * CELL_M <= RADIUS_M
        cells = np.column_stack([gx[keep], gz[keep]]).astype(np.float32)
        # draw nearest first so the depth test throws away hidden tufts early
        cells = cells[np.argsort(np.hypot(cells[:, 0], cells[:, 1]))]
        near = np.hypot(cells[:, 0], cells[:, 1]) * CELL_M <= NEAR_M
        for mesh, sel in ((near_mesh, near), (far_mesh, ~near)):
            self.parts.append({"vbo": ctx.buffer(mesh.tobytes()), "inst": ctx.buffer(cells[sel].tobytes()),
                               "count": int(sel.sum()), "tris": len(mesh) // 3, "vao": None})
        self.count = len(cells)
        chans = world.meta["splat"]["channels"]
        self.biome_w = tuple(BIOME_GRASS.get(c, 0.0) if c else 0.0 for c in chans) + (0.0,) * (8 - len(chans))
        village = next((p for p in world.landmarks if p.name == "Brackenvale Village"), None)
        self.clear_at = (village.x, village.z, village.radius) if village else (0.0, 0.0, 0.0)
        self.enabled = True
        self._version = -1

    def render(self, eye: glm.vec3, viewproj: glm.mat4, env: dict, time_s: float) -> None:
        if not self.enabled:
            return
        prog = self.shaders.get("grass")
        if self._version != self.shaders.version:
            for part in self.parts:
                part["vao"] = self.ctx.vertex_array(prog, [(part["vbo"], "3f 1f", "in_pos", "in_t"),
                                                           (part["inst"], "2f/i", "in_cell")])
            self._version = self.shaders.version
        t = self.terrain
        t.tex_height.use(0)
        t.tex_splat[0].use(1)
        t.tex_splat[1].use(2)
        t.tex_road.use(3)
        t.tex_water.use(4)
        t.tex_patch_a.use(5)
        t.tex_patch_b.use(6)
        t.tex_bank.use(7)
        t.tex_paint.use(8)
        for name, unit in (("u_height", 0), ("u_splat_a", 1), ("u_splat_b", 2), ("u_road", 3), ("u_water_tex", 4),
                           ("u_patch_a", 5), ("u_patch_b", 6), ("u_bank", 7), ("u_paint", 8)):
            set_uniform(prog, name, unit)
        set_uniform(prog, "u_viewproj", viewproj)
        set_uniform(prog, "u_cam", eye)
        set_uniform(prog, "u_world_size", self.world.world_size)
        set_uniform(prog, "u_cell", CELL_M)
        set_uniform(prog, "u_radius", RADIUS_M)
        set_uniform(prog, "u_origin", glm.vec2(math.floor(eye.x / CELL_M), math.floor(eye.z / CELL_M)))
        set_uniform(prog, "u_time", time_s)
        set_uniform(prog, "u_biome_grass", self.biome_w)
        set_uniform(prog, "u_clearing", glm.vec3(*self.clear_at))
        for k, v in env.items():
            set_uniform(prog, k, v)
        for part in self.parts:
            part["vao"].render(moderngl.TRIANGLES, instances=part["count"])
