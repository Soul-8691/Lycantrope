"""Spell projectiles (no damage yet): glowing orbs that fly from a caster to a target and
burst where they land. Drawn additively as a bright core plus a soft halo, one draw each."""
from __future__ import annotations

import math
from dataclasses import dataclass

from pyglm import glm
import moderngl
import numpy as np

from lycantrope.render.shaders import ShaderLibrary, set_uniform


def icosphere(subdiv: int = 2) -> np.ndarray:
    t = (1 + 5 ** 0.5) / 2
    v = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
         (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    f = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
         (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10),
         (8, 6, 7), (9, 8, 1)]
    verts = [np.array(p, float) / np.linalg.norm(p) for p in v]
    for _ in range(subdiv):
        cache, nf = {}, []
        def mid(a, b):
            key = (min(a, b), max(a, b))
            if key not in cache:
                m = verts[a] + verts[b]
                verts.append(m / np.linalg.norm(m))
                cache[key] = len(verts) - 1
            return cache[key]
        for a, b, c in f:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        f = nf
    V = np.array(verts, np.float32)
    return np.ascontiguousarray(V[np.array(f).ravel()], dtype=np.float32)


@dataclass
class Spell:
    pos: np.ndarray
    vel: np.ndarray
    life: float
    radius: float
    color: tuple[float, float, float]
    burst: float = -1.0          # >= 0 while bursting (seconds since impact)
    prev: np.ndarray | None = None
    damage: dict | None = None   # per damage type, if it hurts Rowan when it reaches him
    origin: tuple[float, float] | None = None   # where it was cast from (x, z): blocking and the hit arc


class Spells:
    BURST_S = 0.45

    def __init__(self, ctx: moderngl.Context, shaders: ShaderLibrary, world) -> None:
        self.ctx = ctx
        self.shaders = shaders
        self.world = world
        self.vbo = ctx.buffer(icosphere(2).tobytes())
        self.count = len(icosphere(2))
        self.items: list[Spell] = []
        self._vao = None
        self._version = -1

    def cast(self, start, target, speed: float, radius: float, color, damage: dict | None = None) -> None:
        start, target = np.asarray(start, float), np.asarray(target, float)
        d = target - start
        dist = float(np.linalg.norm(d)) or 1.0
        self.items.append(Spell(start.copy(), d / dist * speed, dist / speed + 0.4, radius, tuple(color),
                                prev=start.copy(), damage=damage, origin=(float(start[0]), float(start[2]))))

    def update(self, dt: float) -> None:
        keep = []
        for s in self.items:
            s.prev = s.pos.copy()
            if s.burst >= 0:
                s.burst += dt
                if s.burst < self.BURST_S:
                    keep.append(s)
                continue
            s.pos = s.pos + s.vel * dt
            s.life -= dt
            ground = self.world.height_at(float(s.pos[0]), float(s.pos[2]))
            if s.life <= 0 or s.pos[1] <= ground + 0.1:
                s.burst = 0.0
            keep.append(s)
        self.items = keep

    def render(self, eye: glm.vec3, viewproj: glm.mat4, env: dict, alpha: float) -> None:
        if not self.items:
            return
        prog = self.shaders.get("spell")
        if self._vao is None or self._version != self.shaders.version:
            self._vao = self.ctx.vertex_array(prog, [(self.vbo, "3f", "in_pos")])
            self._version = self.shaders.version
        set_uniform(prog, "u_viewproj", viewproj)
        set_uniform(prog, "u_cam", eye)
        for k, v in env.items():
            set_uniform(prog, k, v)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.ONE, moderngl.ONE          # additive: it glows
        self.ctx.depth_mask = False
        for s in self.items:
            p = s.prev + (s.pos - s.prev) * alpha if s.burst < 0 else s.pos
            set_uniform(prog, "u_color", glm.vec3(*s.color))
            set_uniform(prog, "u_center", glm.vec3(*(float(v) for v in p)))
            if s.burst < 0:
                layers = ((s.radius, 2.2), (s.radius * 2.6, 0.45))           # bright core, soft halo
            else:
                k = s.burst / self.BURST_S                                   # expanding, fading burst
                layers = ((s.radius * (1.0 + 5.0 * k), 1.6 * (1.0 - k) ** 2),)
            for radius, strength in layers:
                set_uniform(prog, "u_radius", float(radius))
                set_uniform(prog, "u_strength", float(strength))
                self._vao.render(moderngl.TRIANGLES)
        self.ctx.depth_mask = True
        self.ctx.disable(moderngl.BLEND)
