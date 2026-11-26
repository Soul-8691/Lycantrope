"""Text overlay drawn with pygame and shown through OpenGL (UIX-13, TEC-17)."""
from __future__ import annotations

import moderngl
import pygame

from lycantrope.render.shaders import ShaderLibrary, set_uniform


class TextOverlay:
    def __init__(self, ctx: moderngl.Context, shaders: ShaderLibrary, size: int = 15, mono: bool = True) -> None:
        self.ctx = ctx
        self.shaders = shaders
        pygame.font.init()
        faces = "consolas,dejavusansmono,couriernew,monospace" if mono else "segoeui,georgia,dejavusans,arial"
        self.font = pygame.font.SysFont(faces, size)
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

    def set_surface(self, surf: pygame.Surface) -> None:
        """Show an image instead of text (the lock-on reticle)."""
        self._lines = []
        width, height = surf.get_size()
        data = pygame.image.tobytes(surf, "RGBA", True)
        if self.texture is None or self.size != (width, height):
            if self.texture is not None:
                self.texture.release()
            self.texture = self.ctx.texture((width, height), 4, data)
            self.texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
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


class Subtitles:
    """What NPCs say, centred near the bottom of the screen (UIX-10): "Name: line", the newest two
    lines at once, each for as long as it's being spoken plus a moment to finish reading. Lines wrap
    at width_frac of the screen width (measured in pixels with the subtitle font)."""

    def __init__(self, text: TextOverlay | None, keep: int = 2, width_frac: float = 0.66) -> None:
        self.text = text
        self.keep = keep
        self.width_frac = width_frac
        self.lines: list[list] = []           # [label, seconds left]

    def say(self, who: str, line: str, seconds: float) -> None:
        label = f"{who}: {line}" if who else line
        self.lines = [entry for entry in self.lines if entry[0] != label] + [[label, max(2.5, seconds)]]
        self.lines = self.lines[-self.keep:]

    def update(self, dt: float) -> None:
        for entry in self.lines:
            entry[1] -= dt
        self.lines = [entry for entry in self.lines if entry[1] > 0]

    def shown(self, max_px: int | None = None) -> list[str]:
        out: list[str] = []
        for label, _ in self.lines:
            out += self._wrap(label, max_px) if max_px else [label]
        return out

    def _wrap(self, label: str, max_px: int) -> list[str]:
        font = self.text.font
        lines, cur = [], ""
        for word in label.split():
            trial = f"{cur} {word}".strip()
            if cur and font.size(trial)[0] > max_px:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        return lines + ([cur] if cur else [])

    def render(self, screen_w: int, screen_h: int) -> None:
        if not self.lines:
            return
        self.text.set_lines(self.shown(int(screen_w * self.width_frac)))
        w, h = self.text.size
        self.text.render(screen_w, screen_h, x=max(0, (screen_w - w) // 2), y=max(0, screen_h - h - int(screen_h * 0.07)))


class LockReticle:
    """The lock-on marker (UIX-04): a ring with a dot and four ticks on the target, and the target's
    name in a small plate above it. Health bars come once enemies have health."""

    def __init__(self, ctx, shaders) -> None:
        self.ring = TextOverlay(ctx, shaders)
        self.plate = TextOverlay(ctx, shaders, size=14, mono=False)
        size = 48
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        gold, dark = (255, 214, 120, 235), (20, 14, 8, 170)
        pygame.draw.circle(surf, dark, (c, c), 15, 4)
        pygame.draw.circle(surf, gold, (c, c), 15, 2)
        pygame.draw.circle(surf, dark, (c, c), 4)
        pygame.draw.circle(surf, gold, (c, c), 3)
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            a = (c + dx * 18, c + dy * 18)
            b = (c + dx * 23, c + dy * 23)
            pygame.draw.line(surf, dark, a, b, 4)
            pygame.draw.line(surf, gold, a, b, 2)
        self.ring.set_surface(surf)
        self._name = None

    def render(self, screen_w: int, screen_h: int, x: float, y: float, name: str) -> None:
        w, h = self.ring.size
        self.ring.render(screen_w, screen_h, x=int(x - w / 2), y=int(y - h / 2))
        if name:
            if name != self._name:
                self.plate.set_lines([name])
                self._name = name
            pw, ph = self.plate.size
            self.plate.render(screen_w, screen_h, x=int(x - pw / 2), y=int(y - h / 2 - ph - 4))
