"""Procedural sky (ART-09), water surface, and the shared lighting settings."""
from __future__ import annotations

import json
import math
from functools import lru_cache

from pyglm import glm
import moderngl
import numpy as np

from lycantrope.core.paths import DATA
from lycantrope.render.shaders import ShaderLibrary, set_uniform
from lycantrope.world.heightfield import Heightfield


@lru_cache(maxsize=1)
def sky_config() -> dict:
    return json.loads((DATA / "world" / "sky.json").read_text(encoding="utf-8"))


def default_environment(fog: bool = True) -> dict:
    """Lighting/fog uniforms shared by sky, terrain and water (from data/world/sky.json)."""
    cfg = sky_config()
    elevation, azimuth = math.radians(cfg["sun"]["elevation_deg"]), math.radians(cfg["sun"]["azimuth_deg"])
    sun = glm.normalize(glm.vec3(math.sin(azimuth) * math.cos(elevation), math.sin(elevation),
                                 -math.cos(azimuth) * math.cos(elevation)))
    return {
        "u_sun_dir": sun,
        "u_sun_color": glm.vec3(*cfg["sun"]["color"]),
        "u_zenith_color": glm.vec3(*cfg["zenith_color"]),
        "u_horizon_color": glm.vec3(*cfg["horizon_color"]),
        "u_ambient_sky": glm.vec3(*cfg["ambient_sky"]),
        "u_ambient_ground": glm.vec3(*cfg["ambient_ground"]),
        "u_fog_density": 0.00055,
        "u_fog_falloff": 0.006,
        "u_fog_enabled": 1 if fog else 0,
    }


class Sky:
    def __init__(self, ctx: moderngl.Context, shaders: ShaderLibrary) -> None:
        self.ctx = ctx
        self.shaders = shaders
        self._vao = None
        self._version = -1

    def render(self, eye: glm.vec3, viewproj: glm.mat4, env: dict) -> None:
        prog = self.shaders.get("sky")
        if self._vao is None or self._version != self.shaders.version:
            self._vao = self.ctx.vertex_array(prog, [])
            self._version = self.shaders.version
        set_uniform(prog, "u_inv_viewproj", glm.inverse(viewproj))
        set_uniform(prog, "u_cam", eye)
        for k, v in env.items():
            set_uniform(prog, k, v)
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.depth_mask = False
        self._vao.render(moderngl.TRIANGLES, vertices=3)
        self.ctx.depth_mask = True
        self.ctx.enable(moderngl.DEPTH_TEST)


class Water:
    """Sea, lakes and rivers: a grid over every 64 m chunk that holds water, lifted to the
    water-surface map (so lakes sit at their own level and rivers slope downhill). The
    shader discards it wherever the ground is above the water."""

    CHUNK = 64.0
    NEAR_QUADS, FAR_QUADS, LOD_M = 32, 8, 320.0

    def __init__(self, ctx: moderngl.Context, shaders: ShaderLibrary, world: Heightfield, height_tex,
                 water_tex) -> None:
        self.ctx = ctx
        self.shaders = shaders
        self.world = world
        self.height_tex = height_tex
        self.water_tex = water_tex
        k = int(round(self.CHUNK / world.mpp))
        n = world.size // k
        wet = (world.water_surface - world.heights > 0.0)[: n * k, : n * k].reshape(n, k, n, k).any(axis=(1, 3))
        surf = world.water_surface[: n * k, : n * k].reshape(n, k, n, k)
        rows, cols = np.nonzero(wet)
        self.origins = np.column_stack([cols * self.CHUNK - world.half, rows * self.CHUNK - world.half]).astype(np.float32)
        lo = surf.min(axis=(1, 3))[rows, cols] - 1.0
        hi = surf.max(axis=(1, 3))[rows, cols] + 1.0
        o = self.origins
        self.bmin = np.column_stack([o[:, 0], lo, o[:, 1]]).astype(np.float32)
        self.bmax = np.column_stack([o[:, 0] + self.CHUNK, hi, o[:, 1] + self.CHUNK]).astype(np.float32)
        self.lods = []
        for quads in (self.NEAR_QUADS, self.FAR_QUADS):
            i = np.arange(quads + 1)
            gx, gz = np.meshgrid(i, i)
            verts = np.column_stack([gx.ravel() / quads, gz.ravel() / quads]).astype(np.float32)
            a = (gz[:-1, :-1] * (quads + 1) + gx[:-1, :-1]).ravel()
            idx = np.column_stack([a, a + quads + 1, a + 1, a + 1, a + quads + 1, a + quads + 2]).ravel().astype(np.uint32)
            self.lods.append({"vbo": ctx.buffer(verts.tobytes()), "ibo": ctx.buffer(idx.tobytes()),
                              "inst": ctx.buffer(reserve=max(1, len(o)) * 8, dynamic=True), "vao": None})
        self._version = -1
        self.chunks_drawn = 0

    def render(self, eye: glm.vec3, viewproj: glm.mat4, env: dict, time_s: float) -> None:
        if len(self.origins) == 0:
            return
        from lycantrope.render.camera import boxes_in_frustum, frustum_planes
        prog = self.shaders.get("water")
        if self._version != self.shaders.version or self.lods[0]["vao"] is None:
            for lod in self.lods:
                lod["vao"] = self.ctx.vertex_array(prog, [(lod["vbo"], "2f", "in_grid"), (lod["inst"], "2f/i", "in_chunk")],
                                                   index_buffer=lod["ibo"], index_element_size=4)
            self._version = self.shaders.version
        vis = boxes_in_frustum(frustum_planes(viewproj), self.bmin, self.bmax)
        if not vis.any():
            self.chunks_drawn = 0
            return
        e = np.array([eye.x, eye.y, eye.z], dtype=np.float32)
        dist = np.linalg.norm(np.clip(e, self.bmin, self.bmax) - e, axis=1)
        self.height_tex.use(0)
        self.water_tex.use(1)
        set_uniform(prog, "u_height", 0)
        set_uniform(prog, "u_water_tex", 1)
        set_uniform(prog, "u_viewproj", viewproj)
        set_uniform(prog, "u_world_size", self.world.world_size)
        set_uniform(prog, "u_chunk_size", self.CHUNK)
        set_uniform(prog, "u_cam", eye)
        set_uniform(prog, "u_time", time_s)
        for k, v in env.items():
            set_uniform(prog, k, v)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self.ctx.depth_mask = False
        drawn = 0
        for lod, mask in zip(self.lods, (vis & (dist < self.LOD_M), vis & (dist >= self.LOD_M))):
            n = int(mask.sum())
            if n:
                lod["inst"].write(np.ascontiguousarray(self.origins[mask]).tobytes())
                lod["vao"].render(moderngl.TRIANGLES, instances=n)
                drawn += n
        self.ctx.depth_mask = True
        self.ctx.disable(moderngl.BLEND)
        self.chunks_drawn = drawn
