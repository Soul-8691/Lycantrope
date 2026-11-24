"""Text overlay drawn with pygame and shown through OpenGL (UIX-13, TEC-17)."""
from __future__ import annotations

import moderngl
import pygame

from lycantrope.render.shaders import ShaderLibrary, set_uniform


class TextOverlay:
    def __init__(self, ctx: moderngl.Context, shaders: ShaderLibrary, size: int = 15) -> None:
        self.ctx = ctx
        self.shaders = shaders
        pygame.font.init()
        self.font = pygame.font.SysFont("consolas,dejavusansmono,couriernew,monospace", size)
        self.texture: moderngl.Texture | None = None
        self.size = (0, 0)
        self._vao = None
        self._version = -1
        self._lines: list[str] = []

    def set_lines(self, lines: list[str]) -> None:
        if lines == self._lines:
            return
        self._lines = list(lines)
        pad, lh = 8, self.font.get_linesize()
        width = max((self.font.size(line)[0] for line in lines), default=1) + 2 * pad
        height = lh * len(lines) + 2 * pad
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        surf.fill((10, 8, 14, 165))
        for i, line in enumerate(lines):
            surf.blit(self.font.render(line, True, (235, 230, 242)), (pad, pad + i * lh))
        data = pygame.image.tobytes(surf, "RGBA", True)       # flipped: GL's rows start at the bottom
        if self.texture is None or self.size != (width, height):
            if self.texture is not None:
                self.texture.release()
            self.texture = self.ctx.texture((width, height), 4, data)
            self.texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
            self.size = (width, height)
        else:
            self.texture.write(data)

    def render(self, screen_w: int, screen_h: int, x: int = 10, y: int = 10) -> None:
        if self.texture is None:
            return
        prog = self.shaders.get("overlay")
        if self._vao is None or self._version != self.shaders.version:
            self._vao = self.ctx.vertex_array(prog, [])
            self._version = self.shaders.version
        w, h = self.size
        x0, x1 = x / screen_w * 2 - 1, (x + w) / screen_w * 2 - 1
        y1, y0 = 1 - y / screen_h * 2, 1 - (y + h) / screen_h * 2
        self.texture.use(0)
        set_uniform(prog, "u_tex", 0)
        set_uniform(prog, "u_rect", (x0, y0, x1, y1))
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self._vao.render(moderngl.TRIANGLE_STRIP, vertices=4)
        self.ctx.disable(moderngl.BLEND)
        self.ctx.enable(moderngl.DEPTH_TEST)
