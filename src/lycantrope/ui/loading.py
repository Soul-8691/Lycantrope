"""Loading screen: a simple progress bar shown while App initialises."""
from __future__ import annotations
import numpy as np
import pygame
import moderngl


# flat-colour quads only need position; UV is absent so the linker won't
# optimise out in_uv from a shared vertex shader and confuse moderngl.
_VERT_FLAT = """\
#version 330
in vec2 in_pos;
void main() { gl_Position = vec4(in_pos, 0.0, 1.0); }
"""

_VERT_TEX = """\
#version 330
in vec2 in_pos;
in vec2 in_uv;
out vec2 v_uv;
void main() { v_uv = in_uv; gl_Position = vec4(in_pos, 0.0, 1.0); }
"""

_FRAG_FLAT = """\
#version 330
uniform vec4 u_color;
out vec4 out_color;
void main() { out_color = u_color; }
"""

_FRAG_TEX = """\
#version 330
uniform sampler2D u_tex;
in vec2 v_uv;
out vec4 out_color;
void main() { out_color = texture(u_tex, v_uv); }
"""


class LoadingScreen:
    def __init__(self, ctx: moderngl.Context, width: int, height: int) -> None:
        self.ctx = ctx
        self.w, self.h = width, height
        # two separate programs + VBOs so each VAO only declares the attributes it uses
        self.flat = ctx.program(vertex_shader=_VERT_FLAT, fragment_shader=_FRAG_FLAT)
        self.flat_vbo = ctx.buffer(reserve=6 * 2 * 4)      # 6 verts × 2 floats × 4 bytes
        self.vao_flat = ctx.vertex_array(self.flat, [(self.flat_vbo, "2f", "in_pos")])
        self.tex_prog = ctx.program(vertex_shader=_VERT_TEX, fragment_shader=_FRAG_TEX)
        self.tex_prog["u_tex"] = 0
        self.tex_vbo = ctx.buffer(reserve=6 * 4 * 4)       # 6 verts × (x,y,u,v) × 4 bytes
        self.vao_tex = ctx.vertex_array(self.tex_prog, [(self.tex_vbo, "2f 2f", "in_pos", "in_uv")])
        pygame.font.init()
        self._font_sm = pygame.font.SysFont("segoeui,arial,sans", 14)
        self._font_lg = pygame.font.SysFont("segoeui,arial,sans", 34, bold=True)
        self._title_tex = self._make_tex(self._font_lg, "LYCANTROPE", (220, 195, 130))
        self._label_tex: moderngl.Texture | None = None
        self._last_label = ""

    # -- helpers --

    def _make_tex(self, font, text: str, color) -> moderngl.Texture | None:
        try:
            surf = font.render(text, True, color)
            raw = pygame.image.tostring(surf, "RGBA", False)
            tex = self.ctx.texture(surf.get_size(), 4, raw)
            tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
            return tex
        except Exception:
            return None

    def _quad_pos(self, x0: float, y0: float, x1: float, y1: float) -> bytes:
        nx0 = 2 * x0 / self.w - 1;  ny0 = 1 - 2 * y0 / self.h
        nx1 = 2 * x1 / self.w - 1;  ny1 = 1 - 2 * y1 / self.h
        verts = [(nx0, ny0), (nx1, ny0), (nx1, ny1),
                 (nx0, ny0), (nx1, ny1), (nx0, ny1)]
        return np.array(verts, dtype=np.float32).tobytes()

    def _quad_tex(self, x0: float, y0: float, x1: float, y1: float) -> bytes:
        nx0 = 2 * x0 / self.w - 1;  ny0 = 1 - 2 * y0 / self.h
        nx1 = 2 * x1 / self.w - 1;  ny1 = 1 - 2 * y1 / self.h
        verts = [(nx0, ny0, 0.0, 0.0), (nx1, ny0, 1.0, 0.0), (nx1, ny1, 1.0, 1.0),
                 (nx0, ny0, 0.0, 0.0), (nx1, ny1, 1.0, 1.0), (nx0, ny1, 0.0, 1.0)]
        return np.array(verts, dtype=np.float32).tobytes()

    def _draw_flat(self, x0, y0, x1, y1, r, g, b, a=1.0) -> None:
        self.flat["u_color"].value = (r, g, b, a)
        self.flat_vbo.write(self._quad_pos(x0, y0, x1, y1))
        self.vao_flat.render(moderngl.TRIANGLES)

    def _draw_tex(self, tex: moderngl.Texture, cx: float, cy: float) -> None:
        tw, th = tex.size
        x0, y0 = cx - tw // 2, cy - th // 2
        tex.use(0)
        self.tex_vbo.write(self._quad_tex(x0, y0, x0 + tw, y0 + th))
        self.vao_tex.render(moderngl.TRIANGLES)

    # -- public --

    def draw(self, fraction: float, label: str = "") -> None:
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self.ctx.clear(0.07, 0.07, 0.09)

        cx = self.w / 2
        cy = self.h / 2

        if self._title_tex is not None:
            self._draw_tex(self._title_tex, cx, cy - 44)

        bw = max(240, int(self.w * 0.50))
        bh = 10
        bx0 = cx - bw / 2
        by0 = cy + 2

        self._draw_flat(bx0, by0, bx0 + bw, by0 + bh, 0.16, 0.16, 0.20)   # track
        fill = int(bw * max(0.0, min(1.0, fraction)))
        if fill > 0:
            self._draw_flat(bx0, by0, bx0 + fill, by0 + bh, 0.72, 0.55, 0.20)  # gold fill

        pct = int(fraction * 100)
        label_str = f"{pct}%  {label}" if label else f"{pct}%"
        if label_str != self._last_label:
            if self._label_tex is not None:
                self._label_tex.release()
            self._label_tex = self._make_tex(self._font_sm, label_str, (180, 160, 120))
            self._last_label = label_str
        if self._label_tex is not None:
            self._draw_tex(self._label_tex, cx, by0 + bh + 14)

        self.ctx.disable(moderngl.BLEND)
        self.ctx.enable(moderngl.DEPTH_TEST)
        pygame.display.flip()
        pygame.event.pump()

    def release(self) -> None:
        if self._title_tex is not None:
            self._title_tex.release()
        if self._label_tex is not None:
            self._label_tex.release()
        self.vao_flat.release()
        self.vao_tex.release()
        self.flat_vbo.release()
        self.tex_vbo.release()
        self.flat.release()
        self.tex_prog.release()
