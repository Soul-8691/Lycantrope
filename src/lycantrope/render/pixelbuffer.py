"""Low-resolution render target for the pixelated look (pixel_scale ≥ 2).

The 3D scene is rendered to a small colour+depth framebuffer, then upscaled to the
window with GL_NEAREST so every screen pixel is an exact integer multiple of an internal
pixel — a uniform, clean retro look with no blurring.

UI (HUD, text, subtitles) is rendered afterwards directly to the full-resolution screen
so it stays crisp regardless of scale.
"""
from __future__ import annotations
import numpy as np
import moderngl

_VERT = """\
#version 330
in vec2 in_pos;
out vec2 v_uv;
void main() { v_uv = in_pos * 0.5 + 0.5; gl_Position = vec4(in_pos, 0.0, 1.0); }
"""

_FRAG = """\
#version 330
uniform sampler2D u_scene;
in vec2 v_uv;
out vec4 out_color;
void main() { out_color = texture(u_scene, v_uv); }
"""


class PixelBuffer:
    def __init__(self, ctx: moderngl.Context, scale: int) -> None:
        self.ctx = ctx
        self.scale = max(2, scale)
        self._sw = self._sh = 0
        self._color: moderngl.Texture | None = None
        self._depth: moderngl.Renderbuffer | None = None
        self._fb: moderngl.Framebuffer | None = None
        prog = ctx.program(vertex_shader=_VERT, fragment_shader=_FRAG)
        prog["u_scene"] = 0
        vbo = ctx.buffer(np.array([(-1,-1),(1,-1),(1,1),(-1,-1),(1,1),(-1,1)], np.float32).tobytes())
        self.vao = ctx.vertex_array(prog, [(vbo, "2f", "in_pos")])

    def _rebuild(self, sw: int, sh: int) -> None:
        if self._fb is not None:
            self._fb.release()
            self._color.release()
            self._depth.release()
        pw, ph = max(1, sw // self.scale), max(1, sh // self.scale)
        self._color = self.ctx.texture((pw, ph), 4)
        self._color.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self._depth = self.ctx.depth_renderbuffer((pw, ph))
        self._fb = self.ctx.framebuffer([self._color], self._depth)
        self._sw, self._sh = sw, sh

    @property
    def size(self) -> tuple[int, int]:
        return self._fb.size if self._fb else (1, 1)

    def use(self, sw: int, sh: int) -> None:
        """Bind the low-res framebuffer. Call before 3D rendering."""
        if sw != self._sw or sh != self._sh:
            self._rebuild(sw, sh)
        self._fb.use()
        pw, ph = self._fb.size
        self.ctx.viewport = (0, 0, pw, ph)
        self.ctx.clear(0.0, 0.0, 0.0, 1.0, depth=1.0)

    def blit(self, sw: int, sh: int) -> None:
        """Nearest-neighbour upscale to the full window.

        Depth writes are suppressed so the screen's depth buffer (cleared to 1.0 by
        the caller before use()) stays intact for subsequent UI rendering."""
        self.ctx.screen.use()
        self.ctx.viewport = (0, 0, sw, sh)
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.depth_write = False
        self._color.use(0)
        self.vao.render(moderngl.TRIANGLES)
        self.ctx.depth_write = True
        self.ctx.enable(moderngl.DEPTH_TEST)
