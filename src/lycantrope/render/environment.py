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
    """One big plane at the water level; the shader discards it above ground."""

    def __init__(self, ctx: moderngl.Context, shaders: ShaderLibrary, world: Heightfield, height_tex) -> None:
        self.ctx = ctx
        self.shaders = shaders
        self.world = world
        self.height_tex = height_tex
        h = world.half
        quad = np.array([[-h, -h], [h, -h], [-h, h], [h, h]], dtype=np.float32)
        self.vbo = ctx.buffer(quad.tobytes())
        self._vao = None
        self._version = -1

    def render(self, eye: glm.vec3, viewproj: glm.mat4, env: dict, time_s: float) -> None:
        prog = self.shaders.get("water")
        if self._vao is None or self._version != self.shaders.version:
            self._vao = self.ctx.vertex_array(prog, [(self.vbo, "2f", "in_xz")])
            self._version = self.shaders.version
        self.height_tex.use(0)
        set_uniform(prog, "u_height", 0)
        set_uniform(prog, "u_viewproj", viewproj)
        set_uniform(prog, "u_world_size", self.world.world_size)
        set_uniform(prog, "u_water", self.world.water_level)
        set_uniform(prog, "u_cam", eye)
        set_uniform(prog, "u_time", time_s)
        for k, v in env.items():
            set_uniform(prog, k, v)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self.ctx.depth_mask = False
        self._vao.render(moderngl.TRIANGLE_STRIP)
        self.ctx.depth_mask = True
        self.ctx.disable(moderngl.BLEND)
