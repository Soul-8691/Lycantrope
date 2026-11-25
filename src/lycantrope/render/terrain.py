"""Terrain rendering (WLD-01, TEC-10, ART-08).

The whole heightmap lives on the GPU as a float texture. The CPU only decides
which 64 m chunks are visible and how detailed each one should be; every chunk
of a given detail level shares one grid mesh, so the terrain is drawn with one
instanced draw call per level of detail (5 calls in total).
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from pyglm import glm
import moderngl
import numpy as np
from PIL import Image

from lycantrope.core.paths import ASSETS, DATA
from lycantrope.render.camera import boxes_in_frustum, frustum_planes
from lycantrope.render.shaders import ShaderLibrary, set_uniform
from lycantrope.world.heightfield import Heightfield

CHUNK_M = 64.0
LOD_QUADS = (64, 32, 16, 8, 4)     # quads per chunk side at LOD 0..4
SKIRT_DEPTH_M = 6.0


def grid_mesh(quads: int) -> tuple[np.ndarray, np.ndarray]:
    """A (quads+1)² grid in [0,1]², plus a skirt ring hanging below its edge."""
    n = quads + 3                                       # +2 for the skirt ring
    i = np.arange(n)
    gx, gz = np.meshgrid(i, i)
    u = np.clip((gx - 1) / quads, 0.0, 1.0)
    v = np.clip((gz - 1) / quads, 0.0, 1.0)
    skirt = ((gx == 0) | (gx == n - 1) | (gz == 0) | (gz == n - 1)).astype(np.float32)
    verts = np.column_stack([u.ravel(), v.ravel(), skirt.ravel()]).astype(np.float32)
    a = (gz[:-1, :-1] * n + gx[:-1, :-1]).ravel()
    b, c, d = a + 1, a + n, a + n + 1
    idx = np.column_stack([a, c, b, b, c, d]).ravel().astype(np.uint32)
    return verts, idx


@dataclass
class TerrainStats:
    chunks_total: int = 0
    per_lod: tuple[int, ...] = (0, 0, 0, 0, 0)
    triangles: int = 0


class TerrainRenderer:
    def __init__(self, ctx: moderngl.Context, shaders: ShaderLibrary, world: Heightfield) -> None:
        self.ctx = ctx
        self.shaders = shaders
        self.world = world
        self.stats = TerrainStats()
        self.debug_view = 0

        # --- textures --------------------------------------------------------
        h = world.heights.astype(np.float32)
        self.tex_height = ctx.texture((world.size, world.size), 1, h.tobytes(), dtype="f4")
        self.tex_height.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.tex_height.repeat_x = self.tex_height.repeat_y = False
        self.tex_splat = []
        for arr in world.splat:
            t = ctx.texture((world.size, world.size), 4, np.ascontiguousarray(arr).tobytes())
            t.filter = (moderngl.LINEAR, moderngl.LINEAR)
            t.repeat_x = t.repeat_y = False
            self.tex_splat.append(t)
        from lycantrope.world.banks import river_bank_map
        world.bank = river_bank_map(world)
        self.tex_bank = ctx.texture((world.size, world.size), 1, np.ascontiguousarray(world.bank).tobytes())
        self.tex_bank.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.tex_bank.repeat_x = self.tex_bank.repeat_y = False
        self.tex_water = ctx.texture((world.size, world.size), 1,
                                     world.water_surface.astype(np.float32).tobytes(), dtype="f4")
        self.tex_water.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.tex_water.repeat_x = self.tex_water.repeat_y = False
        self.tex_patch_a, self.tex_patch_b = self.bake_patches(ctx, shaders, world.world_size)
        self.tex_road = ctx.texture((world.size, world.size), 1, np.ascontiguousarray(world.road).tobytes())
        self.tex_road.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.tex_road.repeat_x = self.tex_road.repeat_y = False

        self.materials = json.loads((DATA / "world" / "materials.json").read_text(encoding="utf-8"))
        layers = self.materials["layers"]
        self.layer_index = {m["name"]: i for i, m in enumerate(layers)}
        imgs = [np.asarray(Image.open(ASSETS / m["file"]).convert("RGBA"), dtype=np.uint8) for m in layers]
        size = imgs[0].shape[0]
        self.tex_ground = ctx.texture_array((size, size, len(imgs)), 4, np.stack(imgs).tobytes())
        self.tex_ground.build_mipmaps()
        self.tex_ground.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        self.tex_ground.anisotropy = 8.0
        self.tiles = tuple(float(m["tile_m"]) for m in layers) + (1.0,) * (9 - len(layers))
        chans = world.meta["splat"]["channels"]
        bl = self.materials["biome_layers"]
        self.splat_layer = tuple(self.layer_index[bl[c]] if c in bl else -1 for c in chans)

        # --- chunks and meshes ------------------------------------------------
        self.origins, hmin, hmax = world.chunk_bounds(CHUNK_M)
        o = self.origins
        self.bmin = np.column_stack([o[:, 0], hmin - SKIRT_DEPTH_M, o[:, 1]]).astype(np.float32)
        self.bmax = np.column_stack([o[:, 0] + CHUNK_M, hmax, o[:, 1] + CHUNK_M]).astype(np.float32)
        self.stats.chunks_total = len(o)
        self.lods = []
        for quads in LOD_QUADS:
            verts, idx = grid_mesh(quads)
            self.lods.append({
                "vbo": ctx.buffer(verts.tobytes()),
                "ibo": ctx.buffer(idx.tobytes()),
                "inst": ctx.buffer(reserve=len(o) * 8, dynamic=True),
                "tris": len(idx) // 3,
                "vao": None,
            })
        self._vao_version = -1

    # ------------------------------------------------------------------------ #
    PATCH_PX = 2048                     # 2 m per pixel over the 4 km world

    @staticmethod
    def bake_patches(ctx: moderngl.Context, shaders: ShaderLibrary, world_size: float):
        """Draw the meadow colour, dirt, soil colour and tall-grass fields into two textures once."""
        n = TerrainRenderer.PATCH_PX
        texs = [ctx.texture((n, n), 4) for _ in range(2)]
        fbo = ctx.framebuffer(color_attachments=texs)
        prog = shaders.get("patches")
        set_uniform(prog, "u_world_size", world_size)
        vao = ctx.vertex_array(prog, [])
        prev_viewport = ctx.viewport
        fbo.use()
        ctx.viewport = (0, 0, n, n)
        ctx.disable(moderngl.DEPTH_TEST)
        vao.render(moderngl.TRIANGLES, vertices=3)
        ctx.enable(moderngl.DEPTH_TEST)
        ctx.screen.use()
        ctx.viewport = prev_viewport
        vao.release()
        fbo.release()
        for t in texs:
            t.filter = (moderngl.LINEAR, moderngl.LINEAR)
            t.repeat_x = t.repeat_y = False
        return texs

    def _vaos(self) -> moderngl.Program:
        prog = self.shaders.get("terrain")
        if self._vao_version != self.shaders.version or self.lods[0]["vao"] is None:
            for lod in self.lods:
                lod["vao"] = self.ctx.vertex_array(
                    prog, [(lod["vbo"], "2f 1f", "in_grid", "in_skirt"), (lod["inst"], "2f/i", "in_chunk")],
                    index_buffer=lod["ibo"], index_element_size=4)
            self._vao_version = self.shaders.version
        return prog

    def select_chunks(self, eye: glm.vec3, viewproj: glm.mat4, lod_distances) -> list[np.ndarray]:
        planes = frustum_planes(viewproj)
        vis = boxes_in_frustum(planes, self.bmin, self.bmax)
        e = np.array([eye.x, eye.y, eye.z], dtype=np.float32)
        nearest = np.clip(e, self.bmin, self.bmax)
        dist = np.linalg.norm(nearest - e, axis=1)
        lod = np.searchsorted(np.asarray(lod_distances, dtype=np.float32), dist)
        return [self.origins[vis & (lod == k)] for k in range(len(self.lods))]

    def render(self, eye: glm.vec3, viewproj: glm.mat4, env: dict, lod_distances) -> None:
        prog = self._vaos()
        world = self.world
        self.tex_height.use(0)
        self.tex_splat[0].use(1)
        self.tex_splat[1].use(2)
        self.tex_road.use(3)
        self.tex_ground.use(4)
        self.tex_water.use(5)
        self.tex_patch_a.use(6)
        self.tex_patch_b.use(7)
        self.tex_bank.use(8)
        for name, unit in (("u_height", 0), ("u_splat_a", 1), ("u_splat_b", 2), ("u_road", 3), ("u_ground", 4),
                           ("u_water_tex", 5), ("u_patch_a", 6), ("u_patch_b", 7), ("u_bank", 8)):
            set_uniform(prog, name, unit)
        set_uniform(prog, "u_viewproj", viewproj)
        set_uniform(prog, "u_world_size", world.world_size)
        set_uniform(prog, "u_chunk_size", CHUNK_M)
        set_uniform(prog, "u_skirt_depth", SKIRT_DEPTH_M)
        set_uniform(prog, "u_mpp", world.mpp)
        set_uniform(prog, "u_cam", eye)
        set_uniform(prog, "u_water", world.water_level)
        set_uniform(prog, "u_snowline", float(self.materials.get("snowline_m", 215)))
        set_uniform(prog, "u_tile", self.tiles)
        set_uniform(prog, "u_splat_layer", self.splat_layer)
        set_uniform(prog, "u_rock_layer", self.layer_index[self.materials["steep_layer"]])
        set_uniform(prog, "u_road_layer", self.layer_index[self.materials["road_layer"]])
        set_uniform(prog, "u_snow_layer", self.layer_index[self.materials["snow_layer"]])
        set_uniform(prog, "u_mud_layer", self.layer_index[self.materials["underwater_layer"]])
        set_uniform(prog, "u_bank_layer", self.layer_index[self.materials.get("bank_layer", self.materials["underwater_layer"])])
        set_uniform(prog, "u_debug_view", self.debug_view)
        for k, v in env.items():
            set_uniform(prog, k, v)

        groups = self.select_chunks(eye, viewproj, lod_distances)
        counts, tris = [], 0
        for lod, origins in zip(self.lods, groups):
            n = len(origins)
            counts.append(n)
            if n == 0:
                continue
            lod["inst"].write(np.ascontiguousarray(origins, dtype=np.float32).tobytes())
            lod["vao"].render(moderngl.TRIANGLES, instances=n)
            tris += n * lod["tris"]
        self.stats.per_lod = tuple(counts)
        self.stats.triangles = tris
