"""Rowan's Rite effect (CMB-29, ART-19 until the Meshy effect meshes exist).

While the cast animation raises his hand, light gathers in it and a rune circle glows up on the
ground around him. When the hand is highest, the light flashes, a ward ring pulses outward and the
circle flares, then everything fades. Cancelled if the cast is cut short before the release.
"""
from __future__ import annotations

import math

from pyglm import glm
import moderngl
import numpy as np

from lycantrope.render.shaders import ShaderLibrary, set_uniform

GOLD = (1.0, 0.58, 0.22)                 # warm: added light on green grass still reads as gold
GRID = 17                     # vertices per side of the draped circle
AFTER_S = 1.3                 # how long the effect lasts after the release


def smooth(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


class RiteEffect:
    ward_level = 0.0
    world_time = 0.0

    def __init__(self, ctx: moderngl.Context, shaders: ShaderLibrary, world, orb_vbo: moderngl.Buffer,
                 orb_count: int) -> None:
        self.ctx, self.shaders, self.world = ctx, shaders, world
        self.orb_vbo, self.orb_count = orb_vbo, orb_count
        self.t = -1.0                 # seconds since the cast began; < 0 when idle
        self.release_s = 0.6
        self.cancelled_at = -1.0
        self._orb_vao = self._ring_vao = None
        self._version = -1
        u = np.linspace(-1.0, 1.0, GRID)
        self.uv = np.stack(np.meshgrid(u, u), axis=-1).reshape(-1, 2).astype(np.float32)
        idx = []
        for r in range(GRID - 1):
            for c in range(GRID - 1):
                i = r * GRID + c
                idx += [i, i + 1, i + GRID, i + 1, i + GRID + 1, i + GRID]
        self.ibo = ctx.buffer(np.array(idx, np.uint32).tobytes())
        self.vbo = ctx.buffer(reserve=len(self.uv) * 5 * 4)
        self.hand = None              # last hand / feet positions, set by the character renderer
        self.feet = None
        self.ward_level = 0.0         # an active Ward's strength (0..1): a faint shell around Rowan
        self.world_time = 0.0

    @property
    def active(self) -> bool:
        return self.t >= 0.0

    def begin(self, release_s: float) -> None:
        self.t, self.release_s, self.cancelled_at = 0.0, max(0.15, release_s), -1.0

    def cancel(self) -> None:
        """The cast was interrupted: fade out quickly if the light hasn't been released yet."""
        if self.active and self.t < self.release_s and self.cancelled_at < 0:
            self.cancelled_at = self.t

    def update(self, dt: float) -> None:
        self.world_time += dt
        if not self.active:
            return
        self.t += dt
        if self.t > self.release_s + AFTER_S or (self.cancelled_at >= 0 and self.t > self.cancelled_at + 0.25):
            self.t = -1.0

    # ------------------------------------------------------------------ the look over time
    def levels(self) -> dict:
        """Sizes and brightnesses at the current time (also used by the tests)."""
        t, rel = self.t, self.release_s
        fade = 1.0 if self.cancelled_at < 0 else max(0.0, 1.0 - (t - self.cancelled_at) / 0.25)
        k = smooth(t / rel)                                    # 0..1 while gathering
        after = max(0.0, t - rel)
        out = {"orb_r": 0.03 + 0.11 * k, "orb_s": (0.4 + 1.8 * k) * (1.0 + 0.12 * math.sin(t * 40.0)),
               "flash_r": 0.0, "flash_s": 0.0, "ward_r": 0.0, "ward_s": 0.0,
               "ring_r": 1.25 + 0.15 * k, "ring_s": 0.55 * k, "rot": t * 0.9}
        if t >= rel:
            f = min(1.0, after / 0.45)
            out["orb_s"] *= max(0.0, 1.0 - after / 0.25)
            out["flash_r"], out["flash_s"] = 0.14 + 0.55 * f, 2.2 * (1.0 - f) ** 2
            w = min(1.0, after / 0.85)
            out["ward_r"], out["ward_s"] = 0.6 + 1.9 * smooth(w), 1.6 * (1.0 - w) ** 1.5
            g = after / AFTER_S
            out["ring_r"] = 1.4 + 1.1 * smooth(min(1.0, after / 0.6))
            out["ring_s"] = (0.55 + 0.9 * max(0.0, 1.0 - after / 0.3)) * (1.0 - smooth(g))
            out["rot"] = rel * 0.9 + after * 2.5
        for key in ("orb_s", "flash_s", "ward_s", "ring_s"):
            out[key] *= fade
        return out

    # ------------------------------------------------------------------ drawing
    def _drape(self, cx: float, cy: float, cz: float, radius: float) -> None:
        w = self.world
        xs = cx + self.uv[:, 0] * radius
        zs = cz + self.uv[:, 1] * radius
        c, r = (xs + w.half) / w.mpp - 0.5, (zs + w.half) / w.mpp - 0.5
        n = w.size - 1
        c, r = np.clip(c, 0, n - 1e-3), np.clip(r, 0, n - 1e-3)
        c0, r0 = c.astype(int), r.astype(int)
        fc, fr = c - c0, r - r0
        h = w.heights
        ys = (h[r0, c0] * (1 - fc) + h[r0, c0 + 1] * fc) * (1 - fr) + (h[r0 + 1, c0] * (1 - fc) + h[r0 + 1, c0 + 1] * fc) * fr
        ys = np.maximum(ys, cy - 0.6) + 0.05                   # hug the ground, but not down into a hole
        data = np.column_stack([xs, ys, zs, self.uv]).astype(np.float32)
        self.vbo.write(data.tobytes())

    def render(self, eye: glm.vec3, viewproj: glm.mat4, env: dict) -> None:
        if (not self.active and self.ward_level <= 0.0) or self.hand is None or self.feet is None:
            return
        L = self.levels() if self.active else {k: 0.0 for k in ("orb_r", "orb_s", "flash_r", "flash_s", "ward_r",
                                                              "ward_s", "ring_r", "ring_s", "rot")}
        if self.ward_level > 0.0 and L["ward_s"] < 0.3:     # the lasting Ward, after the cast's pulse has passed
            pulse = 0.85 + 0.15 * math.sin(self.world_time * 5.0)
            L["ward_r"], L["ward_s"] = 1.05, (0.18 + 0.32 * self.ward_level) * pulse
        orb = self.shaders.get("spell")
        ring = self.shaders.get("rite")
        if self._version != self.shaders.version or self._orb_vao is None:
            self._orb_vao = self.ctx.vertex_array(orb, [(self.orb_vbo, "3f", "in_pos")])
            self._ring_vao = self.ctx.vertex_array(ring, [(self.vbo, "3f 2f", "in_pos", "in_uv")],
                                                   index_buffer=self.ibo, index_element_size=4)
            self._version = self.shaders.version
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.ONE, moderngl.ONE        # additive: it glows
        self.ctx.depth_mask = False
        fx, fy, fz = self.feet
        if L["ring_s"] > 0.01:
            self._drape(fx, fy, fz, L["ring_r"])
            set_uniform(ring, "u_viewproj", viewproj)
            set_uniform(ring, "u_color", glm.vec3(*GOLD))
            set_uniform(ring, "u_strength", float(L["ring_s"]))
            set_uniform(ring, "u_rot", float(L["rot"]))
            self._ring_vao.render(moderngl.TRIANGLES)
        set_uniform(orb, "u_viewproj", viewproj)
        set_uniform(orb, "u_cam", eye)
        for k, v in env.items():
            set_uniform(orb, k, v)
        set_uniform(orb, "u_color", glm.vec3(*GOLD))
        chest = (fx, fy + 1.0, fz)
        for center, radius, strength, shell in ((self.hand, L["orb_r"], L["orb_s"], 0),
                                                (self.hand, L["orb_r"] * 2.6, L["orb_s"] * 0.25, 0),
                                                (self.hand, L["flash_r"], L["flash_s"], 0),
                                                (chest, L["ward_r"], L["ward_s"], 1)):
            if strength <= 0.01 or radius <= 0.0:
                continue
            set_uniform(orb, "u_center", glm.vec3(*(float(v) for v in center)))
            set_uniform(orb, "u_radius", float(radius))
            set_uniform(orb, "u_strength", float(strength))
            set_uniform(orb, "u_shell", shell)
            self._orb_vao.render(moderngl.TRIANGLES)
        set_uniform(orb, "u_shell", 0)
        self.ctx.depth_mask = True
        self.ctx.disable(moderngl.BLEND)
