"""Finding your way: the compass bar (UIX-02), region names on screen, and the world map (UIX-07).

- The compass runs across the top: N/E/S/W, Duskhold always (it's the compass of the whole world, WLD-08),
  discovered Waystones and landmarks nearby, and a hollow mark for anything undiscovered close by. The
  marker straight ahead gets its name and distance under the bar.
- Entering a new region (biome) shows its name for a few seconds, once Rowan has stayed in it a moment.
- M opens the map: drawn once from the heightfield (biome colours, hill shading, contours, water, roads)
  in a parchment tint, with Rowan's arrow and the places he has discovered.

Coordinates: x = east, z = south. Bearings are radians clockwise from north (yaw convention of Camera).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pygame

from lycantrope.ui.hud import DIM, GOLD, INK, shadowed
from lycantrope.ui.overlay import TextOverlay

DUSKHOLD = "Duskhold Citadel"
NEAR_M = 1500.0          # discovered places show on the compass within this
HINT_M = 300.0           # undiscovered places show as a hollow mark within this
WAYSTONE_C = (120, 178, 240)
DUSK_C = (200, 50, 60)
HINT_C = (190, 184, 196)
BIOME_COLORS = {          # map colours per biome id in the biome map
    1: (128, 156, 82),    # Brackenvale
    2: (58, 96, 64),      # The Wolfwood
    3: (92, 98, 72),      # The Blackmire
    4: (206, 210, 214),   # Frostfang Peaks
    5: (122, 98, 84),     # The Ashen Reach
    6: (70, 58, 70),      # Duskhold
    7: (100, 100, 106),   # World's Edge
}
WATER_C = (84, 122, 146)
ROAD_C = (150, 116, 80)
PARCHMENT = (224, 206, 162)


def wrap(a: float) -> float:
    """Angle into -pi..pi."""
    return (a + math.pi) % math.tau - math.pi


def bearing(frm: tuple[float, float], to: tuple[float, float]) -> float:
    """Direction from frm to to (x, z): 0 = north, +pi/2 = east."""
    return math.atan2(to[0] - frm[0], -(to[1] - frm[1]))


def fmt_distance(m: float) -> str:
    return f"{m / 1000:.1f} km" if m >= 1000 else f"{m:.0f} m"


@dataclass
class Marker:
    name: str
    x: float
    z: float
    kind: str            # "waystone", "landmark", "duskhold" or "hint" (not discovered yet)
    dist: float = 0.0


def compass_markers(world, discovered: set[str], pos: tuple[float, float]) -> list[Marker]:
    """What the compass shows from pos. A place you're standing in has no marker."""
    out = []
    for kind, places in (("landmark", world.landmarks), ("waystone", world.waystones)):
        for p in places:
            d = math.hypot(p.x - pos[0], p.z - pos[1])
            if d <= p.radius:
                continue
            if p.name == DUSKHOLD:
                out.append(Marker(p.name, p.x, p.z, "duskhold", d))
            elif p.name in discovered:
                if d <= NEAR_M:
                    out.append(Marker(p.name, p.x, p.z, kind, d))
            elif d <= HINT_M + p.radius:
                out.append(Marker(p.name, p.x, p.z, "hint", d))
    return out


class RegionTracker:
    """Which region Rowan is in; a new one only counts once he has stayed in it SETTLE_S seconds."""

    SETTLE_S = 1.0

    def __init__(self) -> None:
        self.current: str | None = None
        self._cand: str | None = None
        self._t = 0.0

    def update(self, dt: float, region: str) -> str | None:
        """Returns the region's name when Rowan has just entered it (also the very first one)."""
        if self.current is None:
            self.current = region
            return region
        if region == self.current:
            self._cand, self._t = None, 0.0
            return None
        if region != self._cand:
            self._cand, self._t = region, 0.0
        self._t += dt
        if self._t >= self.SETTLE_S:
            self.current, self._cand, self._t = region, None, 0.0
            return region
        return None


def map_image(world, px: int = 1024) -> np.ndarray:
    """(n, n, 3) uint8 map of the whole world, row 0 = north edge, column 0 = west edge."""
    step = max(1, world.size // px)
    n = world.size // step

    def pool(a: np.ndarray, how) -> np.ndarray:
        return how(a[: n * step, : n * step].reshape(n, step, n, step), axis=(1, 3))

    h = pool(world.heights, np.mean)
    water = pool(world.water_surface, np.mean) - h > 0.3
    road = pool(world.road, np.max) > 110
    biome = world.biome[: n * step: step, : n * step: step]
    gz, gx = np.gradient(h, world.mpp * step)                  # rows run south (z), columns east (x)
    light = np.array([-0.55, 0.75, -0.55]) / np.linalg.norm([-0.55, 0.75, -0.55])   # from the north-west
    shade = np.clip((-gx * light[0] + light[1] - gz * light[2]) / np.sqrt(gx * gx + 1.0 + gz * gz), 0.0, 1.0)
    pal = np.full((256, 3), 110.0)
    for i, c in BIOME_COLORS.items():
        pal[i] = c
    col = pal[biome] * (0.45 + 0.75 * shade)[..., None]
    band = np.floor(h / 50.0)                                   # a contour line every 50 m
    contour = (band != np.roll(band, 1, axis=0)) | (band != np.roll(band, 1, axis=1))
    col[contour] *= 0.82
    col[road & ~water] = ROAD_C
    col[water] = np.array(WATER_C) * (0.9 + 0.2 * shade[water, None])
    col = col * 0.78 + np.array(PARCHMENT) * 0.22
    return np.clip(col, 0, 255).astype(np.uint8)


def _icon(surf: pygame.Surface, kind: str, x: float, y: float, a: int = 255, s: float = 1.0) -> None:
    x, y = int(x), int(y)
    if kind == "waystone":
        r = int(6 * s)
        pts = [(x, y - r), (x + r, y), (x, y + r), (x - r, y)]
        pygame.draw.polygon(surf, (10, 10, 16, a), [(px + (px > x) - (px < x), py + (py > y) - (py < y))
                                                    for px, py in pts])
        pygame.draw.polygon(surf, (*WAYSTONE_C, a), pts)
    elif kind == "landmark":
        pygame.draw.circle(surf, (10, 10, 16, a), (x, y), int(6 * s))
        pygame.draw.circle(surf, (*GOLD, a), (x, y), int(5 * s))
    elif kind == "duskhold":                                    # a dark spire
        r = int(8 * s)
        pts = [(x, y - r - 2), (x + r * 0.55, y + r), (x - r * 0.55, y + r)]
        pygame.draw.polygon(surf, (10, 6, 10, a), [(px, py + 1) for px, py in pts])
        pygame.draw.polygon(surf, (*DUSK_C, a), pts)
    else:                                                       # undiscovered: hollow ring
        pygame.draw.circle(surf, (*HINT_C, a), (x, y), int(5 * s), 2)


# ---------------------------------------------------------------------------- compass (UIX-02)
class Compass:
    SPAN = math.pi             # degrees of view across the bar
    W, H = 540, 40

    def __init__(self, ctx, shaders, world) -> None:
        self.world = world
        self.view = TextOverlay(ctx, shaders)
        self.label = TextOverlay(ctx, shaders)
        big = pygame.font.SysFont("georgia,segoeui,dejavuserif,serif", 17, bold=True)
        small = pygame.font.SysFont("segoeui,georgia,dejavusans,arial", 11, bold=True)
        self.label_font = pygame.font.SysFont("segoeui,georgia,dejavusans,arial", 14)
        self.letters = {t: shadowed(big, t, GOLD if t == "N" else INK) for t in "NESW"}
        self.letters.update({t: shadowed(small, t, DIM) for t in ("NE", "SE", "SW", "NW")})
        self.bg = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for x in range(self.W):                                     # band fading out at both ends
            f = 1.0 - (abs(x - self.W / 2) / (self.W / 2)) ** 4
            pygame.draw.line(self.bg, (10, 8, 14, int(150 * f)), (x, 8), (x, 32))
            self.bg.set_at((x, 8), (*GOLD, int(120 * f)))
            self.bg.set_at((x, 32), (*GOLD, int(120 * f)))
        self._key = self._label_key = None

    def _x(self, rel: float) -> float:
        return self.W / 2 + rel / (self.SPAN / 2) * (self.W / 2 - 14)

    @staticmethod
    def _fade(rel: float) -> int:
        return int(255 * max(0.0, min(1.0, (1.0 - abs(rel) / (math.pi / 2)) * 4.0)))

    def surface(self, yaw: float, pos: tuple[float, float], markers: list[Marker]) -> pygame.Surface:
        surf = self.bg.copy()
        for deg in range(0, 360, 15):
            rel = wrap(math.radians(deg) - yaw)
            if abs(rel) > self.SPAN / 2:
                continue
            x, a = self._x(rel), self._fade(rel)
            name = {0: "N", 90: "E", 180: "S", 270: "W", 45: "NE", 135: "SE", 225: "SW", 315: "NW"}.get(deg)
            if name:
                img = self.letters[name]
                img.set_alpha(a)
                surf.blit(img, (int(x - img.get_width() / 2), 20 - img.get_height() // 2))
            else:
                pygame.draw.line(surf, (*DIM, a), (int(x), 15), (int(x), 25))
        for m in sorted(markers, key=lambda m: -m.dist):             # nearer marks on top
            rel = wrap(bearing(pos, (m.x, m.z)) - yaw)
            if abs(rel) <= self.SPAN / 2:
                _icon(surf, m.kind, self._x(rel), 20, self._fade(rel), 1.0 if m.kind != "hint" else 0.9)
        return surf

    def render(self, w: int, h: int, yaw: float, pos: tuple[float, float], discovered: set[str],
               alpha: float = 1.0) -> None:
        markers = compass_markers(self.world, discovered, pos)
        key = (round(math.degrees(yaw) * 2), round(pos[0] / 3), round(pos[1] / 3), len(discovered))
        if key != self._key:
            self.view.set_surface(self.surface(yaw, pos, markers))
            self._key = key
        self.view.render(w, h, x=(w - self.W) // 2, y=10, alpha=alpha)
        ahead = [m for m in markers if abs(wrap(bearing(pos, (m.x, m.z)) - yaw)) < math.radians(5)]
        if not ahead:
            return
        m = min(ahead, key=lambda m: abs(wrap(bearing(pos, (m.x, m.z)) - yaw)))
        text = f"{'Unexplored' if m.kind == 'hint' else m.name}  ·  {fmt_distance(m.dist)}"
        if text != self._label_key:
            self.label.set_surface(shadowed(self.label_font, text, HINT_C if m.kind == "hint" else INK))
            self._label_key = text
        lw, _ = self.label.size
        self.label.render(w, h, x=(w - lw) // 2, y=10 + self.H, alpha=alpha)


# ---------------------------------------------------------------------------- region name
class RegionBanner:
    """A region's name, fading in and out near the top of the screen when Rowan enters it."""

    SHOW_S = 4.5

    def __init__(self, ctx, shaders) -> None:
        self.tracker = RegionTracker()
        self.view = TextOverlay(ctx, shaders)
        self.font = pygame.font.SysFont("georgia,segoeui,dejavuserif,serif", 36)
        self.t = 0.0

    def update(self, dt: float, region: str) -> None:
        entered = self.tracker.update(dt, region)
        if entered:
            self.view.set_surface(shadowed(self.font, entered, (232, 214, 170)))
            self.t = self.SHOW_S
        self.t = max(0.0, self.t - dt)

    def render(self, w: int, h: int) -> None:
        if self.t <= 0:
            return
        shown = self.SHOW_S - self.t
        a = min(1.0, shown / 0.8, self.t / 1.2)
        vw, vh = self.view.size
        self.view.render(w, h, x=(w - vw) // 2, y=int(h * 0.17), alpha=a)


# ---------------------------------------------------------------------------- world map
class WorldMap:
    """M: the whole world on parchment. Wheel or +/- zoom, WASD/arrows pan, C centres on Rowan, M/Esc close."""

    MIN_SPAN = 400.0

    def __init__(self, ctx, shaders, world) -> None:
        self.world = world
        img = map_image(world)
        self.base = pygame.surfarray.make_surface(img.swapaxes(0, 1))
        self.m_per_px = world.world_size / img.shape[0]
        self.view = TextOverlay(ctx, shaders)
        self.dim = TextOverlay(ctx, shaders)
        black = pygame.Surface((2, 2))
        black.fill((0, 0, 0))
        self.dim.set_surface(black)
        self.title_font = pygame.font.SysFont("georgia,segoeui,dejavuserif,serif", 26)
        self.label_font = pygame.font.SysFont("segoeui,georgia,dejavusans,arial", 13, bold=True)
        self.hint_font = pygame.font.SysFont("segoeui,georgia,dejavusans,arial", 13)
        self.open = False
        self.center = (0.0, 0.0)
        self.span = 1600.0
        self._key = None

    # -- control -------------------------------------------------------------
    def toggle(self, pos: tuple[float, float]) -> None:
        self.open = not self.open
        if self.open:
            self.center = pos
            self._clamp()

    def zoom(self, steps: float) -> None:
        self.span = min(self.world.world_size, max(self.MIN_SPAN, self.span * 0.85 ** steps))
        self._clamp()

    def key(self, k: int, pos: tuple[float, float]) -> None:
        if k in (pygame.K_m, pygame.K_ESCAPE):
            self.open = False
        elif k in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self.zoom(1)
        elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.zoom(-1)
        elif k == pygame.K_c:
            self.center = pos
            self._clamp()

    def update(self, dt: float, keys) -> None:
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dz = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        if dx or dz:
            v = self.span * 0.7 * dt
            self.center = (self.center[0] + dx * v, self.center[1] + dz * v)
            self._clamp()

    def _clamp(self) -> None:
        lim = max(0.0, self.world.half - self.span / 2)
        self.center = (min(lim, max(-lim, self.center[0])), min(lim, max(-lim, self.center[1])))

    # -- drawing -------------------------------------------------------------
    def surface(self, side: int, pos: tuple[float, float], heading: float, discovered: set[str],
                region: str) -> pygame.Surface:
        x0, z0 = self.center[0] - self.span / 2, self.center[1] - self.span / 2
        bw = self.base.get_width()
        px0 = (x0 + self.world.half) / self.m_per_px
        pz0 = (z0 + self.world.half) / self.m_per_px
        size = max(4, min(bw, int(round(self.span / self.m_per_px))))
        rect = pygame.Rect(int(max(0, min(bw - size, round(px0)))), int(max(0, min(bw - size, round(pz0)))),
                           size, size)
        mapimg = pygame.Surface((side, side), pygame.SRCALPHA)
        mapimg.blit(pygame.transform.smoothscale(self.base.subsurface(rect), (side, side)), (0, 0))
        # the exact world square the crop shows (after rounding)
        x0 = rect.x * self.m_per_px - self.world.half
        z0 = rect.y * self.m_per_px - self.world.half
        k = side / (size * self.m_per_px)

        def to_map(x: float, z: float) -> tuple[float, float]:
            return (x - x0) * k, (z - z0) * k

        # places
        for kind, places in (("landmark", self.world.landmarks), ("waystone", self.world.waystones)):
            for p in places:
                if p.name == DUSKHOLD:
                    kind_shown = "duskhold"
                elif p.name in discovered:
                    kind_shown = kind
                else:
                    continue
                mx, my = to_map(p.x, p.z)
                if not (-20 <= mx <= side + 20 and -20 <= my <= side + 20):
                    continue
                _icon(mapimg, kind_shown, mx, my, 255, 1.2)
                lab = shadowed(self.label_font, p.name, INK)
                mapimg.blit(lab, (int(mx + 10), int(my - lab.get_height() / 2)))
        # Rowan
        mx, my = to_map(*pos)
        fx, fz = math.sin(heading), math.cos(heading)
        tip = (mx + fx * 12, my + fz * 12)
        left = (mx - fx * 7 + fz * 7, my - fz * 7 - fx * 7)
        right = (mx - fx * 7 - fz * 7, my - fz * 7 + fx * 7)
        back = (mx - fx * 3, my - fz * 3)
        pygame.draw.polygon(mapimg, (12, 8, 8), [(px + 1, py + 1) for px, py in (tip, left, back, right)])
        pygame.draw.polygon(mapimg, (226, 60, 48), (tip, left, back, right))
        # scale bar
        target = self.span / 5
        nice = max(v for v in (50, 100, 200, 250, 500, 1000, 2000) if v <= max(target, 50))
        bar = nice * k
        y = side - 18
        pygame.draw.line(mapimg, (20, 16, 12), (14, y), (14 + bar, y), 3)
        for bx in (14, 14 + bar):
            pygame.draw.line(mapimg, (20, 16, 12), (bx, y - 5), (bx, y + 5), 2)
        mapimg.blit(shadowed(self.hint_font, fmt_distance(nice), INK), (int(20 + bar), y - 10))
        # frame, title and key hints
        out = pygame.Surface((side + 24, side + 84), pygame.SRCALPHA)
        out.fill((16, 12, 10, 235))
        pygame.draw.rect(out, (122, 98, 60), out.get_rect(), 2)
        title = shadowed(self.title_font, region or "Aldmoor", (232, 214, 170))
        out.blit(title, ((out.get_width() - title.get_width()) // 2, 8))
        out.blit(mapimg, (12, 48))
        pygame.draw.rect(out, (122, 98, 60), (11, 47, side + 2, side + 2), 1)
        hint = shadowed(self.hint_font, "M / Esc close    Wheel or + / -  zoom    WASD pan    C centre on Rowan", DIM)
        out.blit(hint, ((out.get_width() - hint.get_width()) // 2, side + 56))
        return out

    def render(self, w: int, h: int, pos: tuple[float, float], heading: float, discovered: set[str],
               region: str) -> None:
        if not self.open:
            return
        side = max(200, min(h - 110, w - 60))
        key = (round(self.center[0]), round(self.center[1]), round(self.span), side, len(discovered),
               round(pos[0] / 2), round(pos[1] / 2), round(heading * 20), region)
        if key != self._key:
            self.view.set_surface(self.surface(side, pos, heading, discovered, region))
            self._key = key
        self.dim.render(w, h, 0, 0, alpha=0.55, size=(w, h))
        vw, vh = self.view.size
        self.view.render(w, h, x=(w - vw) // 2, y=(h - vh) // 2)
