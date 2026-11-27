"""Loot in the world (UIX-26): a glint over every drop and closed chest within GLINT_M, and an "[E] Take ..."
label over the one Rowan can reach."""
from __future__ import annotations

import math

import pygame

from lycantrope.ui.hud import DIM, GOLD, INK, shadowed
from lycantrope.ui.overlay import TextOverlay

GLINT_M = 30.0


def describe(drop, catalog: dict) -> tuple[str, str, tuple | None]:
    """(verb, object, rarity key of the object or None) for a drop's prompt."""
    if drop.is_chest and not drop.opened:
        return "Open", drop.name or "Chest", None
    items = drop.items
    first = catalog[items[0][0]]
    name = first["name"] + (f" x{items[0][1]}" if items[0][1] > 1 else "")
    if len(items) > 1:
        name += f" and {len(items) - 1} more"
    return "Take", name, first["rarity"]


class LootView:
    def __init__(self, ctx, shaders, catalog: dict, rarity_colors: dict) -> None:
        self.catalog = catalog
        self.colors = rarity_colors
        self.glint = TextOverlay(ctx, shaders)
        g = pygame.Surface((28, 28), pygame.SRCALPHA)
        for r, a in ((13, 40), (9, 90), (5, 200)):
            pygame.draw.circle(g, (*GOLD, a), (14, 14), r)
        pygame.draw.polygon(g, (255, 246, 214, 255), [(14, 3), (17, 14), (14, 25), (11, 14)])
        pygame.draw.polygon(g, (255, 246, 214, 255), [(3, 14), (14, 11), (25, 14), (14, 17)])
        self.glint.set_surface(g)
        self.label = TextOverlay(ctx, shaders)
        self.font = pygame.font.SysFont("segoeui,georgia,dejavusans,arial", 17, bold=True)
        self._key = None

    @staticmethod
    def project(viewproj, x: float, y: float, z: float, w: int, h: int):
        clip = viewproj * _vec4(x, y, z)
        if clip.w <= 0.05:
            return None
        return (clip.x / clip.w * 0.5 + 0.5) * w, (1.0 - (clip.y / clip.w * 0.5 + 0.5)) * h

    def render(self, w: int, h: int, viewproj, drops, near, eye, t: float) -> None:
        for d in drops:
            if d.is_chest and d.opened and not d.items:
                continue
            if math.dist((d.x, d.z), (eye.x, eye.z)) > GLINT_M or d is near:
                continue
            p = self.project(viewproj, d.x, d.y + 0.4, d.z, w, h)
            if p is None:
                continue
            a = 0.55 + 0.45 * math.sin(t * 3.0 + d.x)
            gw, gh = self.glint.size
            self.glint.render(w, h, x=int(p[0] - gw / 2), y=int(p[1] - gh / 2), alpha=a)
        if near is None:
            return
        verb, obj, rarity = describe(near, self.catalog)
        if (verb, obj) != self._key:
            col = tuple(self.colors.get(rarity, INK)) if rarity else GOLD
            parts = [shadowed(self.font, "[E]", GOLD), shadowed(self.font, f"  {verb}  ", DIM if verb else INK),
                     shadowed(self.font, obj, col)]
            surf = pygame.Surface((sum(p.get_width() for p in parts) + 20, max(p.get_height() for p in parts) + 10),
                                  pygame.SRCALPHA)
            surf.fill((10, 8, 14, 170))
            x = 10
            for p in parts:
                surf.blit(p, (x, 5))
                x += p.get_width()
            self.label.set_surface(surf)
            self._key = (verb, obj)
        p = self.project(viewproj, near.x, near.y + 0.9, near.z, w, h)
        lw, lh = self.label.size
        if p is None:
            p = (w / 2, h * 0.62)
        self.label.render(w, h, x=int(p[0] - lw / 2), y=int(p[1] - lh), alpha=1.0)


def _vec4(x, y, z):
    from pyglm import glm
    return glm.vec4(x, y, z, 1.0)
