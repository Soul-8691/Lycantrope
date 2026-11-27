"""Waystones (WLD-09): E at a lit Waystone rests (full health, the flask refilled, enemies back, the game saved)
and opens the travel list of every Waystone Rowan has lit. The world waits while the list is open.

Keys: Up / Down pick · Enter travel · Esc close. Click a row to travel.
"""
from __future__ import annotations

import math

import pygame

from lycantrope.ui.hud import DIM, GOLD, INK, shadowed
from lycantrope.ui.navigation import fmt_distance
from lycantrope.ui.overlay import TextOverlay

REST_M = 3.5           # how close to the stone Rowan must stand
STAND_M = 2.4          # where travel puts him: this far from the stone, facing it
W = 520


def travel_spot(world, place) -> tuple[float, float, float]:
    """A dry spot STAND_M from the stone (south first, then around), and the heading that faces the stone."""
    for k in range(8):
        a = k * math.tau / 8
        x, z = place.x + math.sin(a) * STAND_M, place.z + math.cos(a) * STAND_M
        if world.water_depth(x, z) < 0.3:
            return x, z, math.atan2(place.x - x, place.z - z)
    return place.x, place.z + STAND_M, math.pi


class WaystoneMenu:
    def __init__(self, ctx, shaders, app) -> None:
        self.app = app
        self.view = TextOverlay(ctx, shaders)
        self.prompt = TextOverlay(ctx, shaders)
        self.f_title = pygame.font.SysFont("georgia,segoeui,dejavuserif,serif", 24)
        self.f = pygame.font.SysFont("segoeui,georgia,dejavusans,arial", 16)
        self.f_small = pygame.font.SysFont("segoeui,georgia,dejavusans,arial", 13)
        self.f_prompt = pygame.font.SysFont("segoeui,georgia,dejavusans,arial", 17, bold=True)
        self.open = False
        self.here = None
        self.rows: list = []
        self.sel = 0
        self.dirty = True
        self.hits: list[tuple[pygame.Rect, int]] = []
        self._rect = (0, 0, 1, 1)
        self._prompt_key = None

    def lit(self) -> list:
        found = self.app.chars.progress.discovered
        return [p for p in self.app.world.waystones if p.name in found]

    def in_reach(self, x: float, z: float):
        return next((p for p in self.lit() if math.hypot(p.x - x, p.z - z) <= REST_M), None)

    def show(self, here) -> None:
        self.open, self.here, self.dirty = True, here, True
        self.rows = sorted(self.lit(), key=lambda p: (p is not here, math.hypot(p.x - here.x, p.z - here.z)))
        self.sel = 1 if len(self.rows) > 1 else 0

    def key(self, k: int) -> None:
        self.dirty = True
        if k in (pygame.K_ESCAPE, pygame.K_e):
            self.open = False
        elif k in (pygame.K_UP, pygame.K_w):
            self.sel = (self.sel - 1) % len(self.rows)
        elif k in (pygame.K_DOWN, pygame.K_s):
            self.sel = (self.sel + 1) % len(self.rows)
        elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self._go(self.sel)

    def click(self, pos) -> None:
        x0, y0, sw, sh = self._rect
        px, py = (pos[0] - x0) * W / sw, (pos[1] - y0) * self._h / sh
        for rect, i in self.hits:
            if rect.collidepoint(px, py):
                self.sel = i
                self._go(i)
                self.dirty = True
                return

    def _go(self, i: int) -> None:
        dest = self.rows[i]
        self.open = False
        if dest is not self.here:
            self.app.fast_travel(dest)

    def surface(self) -> pygame.Surface:
        rows = self.rows
        h = 120 + 46 * len(rows) + 34
        self._h = h
        surf = pygame.Surface((W, h), pygame.SRCALPHA)
        surf.fill((14, 11, 16, 236))
        pygame.draw.rect(surf, (122, 98, 60), surf.get_rect(), 2)
        t = self.f_title.render(self.here.name, True, GOLD)
        surf.blit(t, ((W - t.get_width()) // 2, 14))
        s = self.f_small.render("Rested: health and flask restored, enemies returned, game saved.", True, DIM)
        surf.blit(s, ((W - s.get_width()) // 2, 50))
        surf.blit(self.f.render("Travel to", True, INK), (24, 84))
        self.hits = []
        world = self.app.world
        for i, p in enumerate(rows):
            r = pygame.Rect(16, 112 + i * 46, W - 32, 40)
            if i == self.sel:
                pygame.draw.rect(surf, (28, 23, 30), r, border_radius=4)
                pygame.draw.rect(surf, GOLD, r, 2, border_radius=4)
            here = p is self.here
            name = p.name + ("   (you are here)" if here else "")
            surf.blit(self.f.render(name, True, DIM if here else (GOLD if i == self.sel else INK)), (r.x + 12, r.y + 10))
            if not here:
                info = f"{world.biome_at(p.x, p.z)}  ·  {fmt_distance(math.hypot(p.x - self.here.x, p.z - self.here.z))}"
                img = self.f_small.render(info, True, DIM)
                surf.blit(img, (r.right - 12 - img.get_width(), r.y + 12))
            self.hits.append((r, i))
        hint = self.f_small.render("Up / Down pick   Enter travel   Esc stay", True, DIM)
        surf.blit(hint, (24, h - 26))
        return surf

    def render(self, w: int, h: int) -> None:
        if not self.open:
            return
        if self.dirty:
            self.view.set_surface(self.surface())
            self.dirty = False
        vw, vh = self.view.size
        k = min(1.0, (h - 40) / vh)
        sw, sh = int(vw * k), int(vh * k)
        self._rect = ((w - sw) // 2, (h - sh) // 2, sw, sh)
        self.view.render(w, h, x=self._rect[0], y=self._rect[1], size=(sw, sh))

    def render_prompt(self, w: int, h: int, place) -> None:
        """[E] Rest at <Waystone>, low in the middle of the screen."""
        if self._prompt_key != place.name:
            parts = [shadowed(self.f_prompt, "[E]", GOLD), shadowed(self.f_prompt, "  Rest at  ", DIM),
                     shadowed(self.f_prompt, place.name, INK)]
            surf = pygame.Surface((sum(p.get_width() for p in parts) + 20, parts[0].get_height() + 10), pygame.SRCALPHA)
            surf.fill((10, 8, 14, 170))
            x = 10
            for p in parts:
                surf.blit(p, (x, 5))
                x += p.get_width()
            self.prompt.set_surface(surf)
            self._prompt_key = place.name
        pw, ph = self.prompt.size
        self.prompt.render(w, h, x=(w - pw) // 2, y=int(h * 0.66))
