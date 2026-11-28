"""Rowan's HUD (UIX-01, UIX-15..18, UIX-20..22), the level-up screen (UIX-06) and the death screen (UIX-09).

Everything is drawn with pygame onto small surfaces and shown through the overlay shader (UIX-13). A
surface is only redrawn when what it shows changes (bars are compared in whole pixels).

- HP and stamina bars, top-left, that get longer as their maximums rise (UIX-15). The HP bar keeps a pale
  segment for the last hit that drains after a moment (UIX-16).
- A thin XP line under the stamina bar, with the level and a glowing mark once a level can be bought
  (UIX-20), and a short "+XP" note when XP comes in.
- The bars fade out when everything is full and nothing is happening, and come back on any change (UIX-21).
- A red arc on the screen edge toward whoever hit Rowan (UIX-18).
- The flask quick slot, bottom-left, with its charges, greyed when empty (UIX-22), and the food pouch.
"""
from __future__ import annotations

import math

import pygame

from lycantrope.ui.overlay import TextOverlay

GOLD = (236, 196, 110)
INK = (235, 230, 242)
DIM = (150, 144, 156)
GREEN = (120, 214, 120)
RED = (226, 96, 86)


def shadowed(font, text: str, color) -> pygame.Surface:
    """Text with a dark outline, readable on bright sky or snow."""
    fg = font.render(text, True, color)
    bg = font.render(text, True, (8, 6, 10))
    out = pygame.Surface((fg.get_width() + 2, fg.get_height() + 2), pygame.SRCALPHA)
    for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2), (2, 2)):
        out.blit(bg, (dx, dy))
    out.blit(fg, (1, 1))
    return out


def hp_bar_px(max_hp: float) -> int:
    """UIX-15: the HP bar grows with max HP (300 HP: 185 px; about 1,000: 360 px)."""
    return int(110 + max_hp * 0.25)


def st_bar_px(max_st: float) -> int:
    return int(100 + max_st * 1.0)


class HudState:
    """What the HUD shows and how visible it is: plain numbers, tested without a window."""

    CALM_S = 3.0          # everything full and quiet this long: the bars fade away
    ARC_S = 0.9
    NOTE_S = 3.0

    def __init__(self) -> None:
        self.alpha = 1.0
        self.calm = 0.0
        self.arc_t = 0.0                       # seconds left of the hit-direction arc
        self.arc_from: tuple[float, float] | None = None
        self.notes: list[list] = []            # [text, seconds left]
        self.last = None

    def event(self, ev: tuple) -> None:
        kind = ev[0]
        if kind == "hurt":
            self.calm = 0.0
            if ev[2] is not None:
                self.arc_from, self.arc_t = ev[2], self.ARC_S
        elif kind == "xp":
            self.calm = 0.0
            self.note(f"+{ev[1]} XP   {ev[2]}" if len(ev) > 2 and ev[2] else f"+{ev[1]} XP")
        elif kind == "level":
            self.calm = 0.0
            self.note(f"Level {ev[1]}")
        elif kind == "roll":
            self.note("Landing roll")
        elif kind == "ward":
            self.calm = 0.0
            self.note(f"Ward: absorbs {ev[1]:.0f} for {ev[2]:.0f} s")
        elif kind == "reload":
            self.notes.clear()
            self.arc_t = 0.0

    def note(self, text: str) -> None:
        self.notes = (self.notes + [[text, self.NOTE_S]])[-3:]

    def update(self, dt: float, full: bool, fighting: bool) -> None:
        """full: HP and stamina both full; fighting: an enemy is after Rowan."""
        if full and not fighting and not self.notes:
            self.calm += dt
        else:
            self.calm = 0.0
        want = 0.0 if self.calm > self.CALM_S else 1.0
        rate = 1.5 if want < self.alpha else 6.0
        self.alpha += max(-rate * dt, min(rate * dt, want - self.alpha))
        self.arc_t = max(0.0, self.arc_t - dt)
        for n in self.notes:
            n[1] -= dt
        self.notes = [n for n in self.notes if n[1] > 0]

    @staticmethod
    def arc_direction(src: tuple[float, float], me: tuple[float, float], cam_yaw: float) -> float:
        """Screen angle (radians, 0 = up/ahead, + = clockwise/right) from Rowan toward src."""
        dx, dz = src[0] - me[0], src[1] - me[1]
        fx, fz = math.sin(cam_yaw), -math.cos(cam_yaw)      # camera forward on the ground
        rx, rz = math.cos(cam_yaw), math.sin(cam_yaw)       # camera right
        return math.atan2(dx * rx + dz * rz, dx * fx + dz * fz)


class Hud:
    def __init__(self, ctx, shaders) -> None:
        self.state = HudState()
        self.bars = TextOverlay(ctx, shaders, size=13, mono=False)
        self.slot = TextOverlay(ctx, shaders, size=13, mono=False)
        self.arc = TextOverlay(ctx, shaders)
        self.big = pygame.font.SysFont("segoeui,georgia,dejavusans,arial", 20, bold=True)
        self._bars_key = self._slot_key = self._arc_key = None
        arc = pygame.Surface((260, 70), pygame.SRCALPHA)
        for i, a in enumerate((90, 160, 240)):                       # soft outer glow to a bright core
            pygame.draw.arc(arc, (220, 34, 26, a), (10 + i * 3, 10 + i * 3, 240 - i * 6, 200), math.radians(52),
                            math.radians(128), 20 - i * 6)
        self._arc_base = arc
        self.height = 70

    # ------------------------------------------------------------------ bars
    def _bars_surface(self, f, prog, pulse: float) -> pygame.Surface:
        hw, sw = hp_bar_px(f.max_hp), st_bar_px(f.max_stamina)
        w = max(hw, sw) + 90
        surf = pygame.Surface((w, 62), pygame.SRCALPHA)
        x0, y = 4, 4
        # HP: frame, trail, health
        pygame.draw.rect(surf, (12, 8, 8, 200), (x0 - 2, y - 2, hw + 4, 16), border_radius=3)
        pygame.draw.rect(surf, (225, 196, 160), (x0, y, int(hw * f.trail / f.max_hp), 12), border_radius=2)
        pygame.draw.rect(surf, (172, 30, 28), (x0, y, int(hw * f.hp / f.max_hp), 12), border_radius=2)
        if f.ward_t > 0 and f.ward_hp > 0:       # the Ward: a pale gold band over the HP it guards
            ww = max(3, int(hw * min(1.0, f.ward_hp / f.max_hp)))
            pygame.draw.rect(surf, (250, 218, 140), (x0, y + 1, ww, 4), border_radius=2)
        pygame.draw.rect(surf, (90, 70, 40), (x0 - 2, y - 2, hw + 4, 16), 1, border_radius=3)
        # stamina
        y = 22
        pygame.draw.rect(surf, (12, 8, 8, 200), (x0 - 2, y - 2, sw + 4, 12), border_radius=3)
        col = (110, 120, 96) if f.exhausted else (78, 158, 86)
        pygame.draw.rect(surf, col, (x0, y, int(sw * f.stamina / max(f.max_stamina, 1e-6)), 8), border_radius=2)
        pygame.draw.rect(surf, (60, 70, 40), (x0 - 2, y - 2, sw + 4, 12), 1, border_radius=3)
        # XP line, level and the level-ready mark (UIX-20)
        y = 37
        need = prog.xp_needed()
        frac = 1.0 if prog.level >= prog.cap else min(1.0, prog.xp / max(need, 1))
        pygame.draw.rect(surf, (12, 8, 8, 190), (x0 - 1, y - 1, sw + 2, 5))
        pygame.draw.rect(surf, GOLD, (x0, y, int(sw * frac), 3))
        lv = shadowed(self.bars.font, f"Lv {prog.level}", INK)
        surf.blit(lv, (x0 + sw + 8, y - lv.get_height() // 2 + 1))
        if prog.ready():
            cx, cy = x0 + sw + 16 + lv.get_width(), y + 1
            glow = 90 + int(120 * pulse)
            pygame.draw.circle(surf, (255, 210, 110, glow // 2), (cx, cy), 8)
            pygame.draw.circle(surf, (255, 226, 150, glow), (cx, cy), 5)
            pygame.draw.circle(surf, (255, 250, 220), (cx, cy), 2)
        # incoming XP and other notes
        y = 46
        for text, _left in self.state.notes[-1:]:
            t = shadowed(self.bars.font, text, GOLD)
            surf.blit(t, (x0, y))
        return surf

    def _slot_surface(self, flask: int, flask_max: int, food: dict, rite: str = "", rite_cd: float = 0.0) -> pygame.Surface:
        surf = pygame.Surface((170, 100), pygame.SRCALPHA)
        empty = flask <= 0
        pygame.draw.rect(surf, (10, 8, 14, 175), (2, 2, 64, 64), border_radius=6)
        pygame.draw.rect(surf, (110, 90, 56) if not empty else (70, 66, 70), (2, 2, 64, 64), 2, border_radius=6)
        glass = (150, 170, 176) if not empty else (90, 90, 96)
        water = (70, 190, 200) if not empty else (60, 60, 66)
        pygame.draw.circle(surf, glass, (34, 42), 15)
        pygame.draw.circle(surf, water, (34, 44), 12)
        pygame.draw.rect(surf, glass, (29, 14, 10, 16))
        pygame.draw.rect(surf, (120, 86, 52), (28, 11, 12, 6))
        n = shadowed(self.big, str(flask), INK if not empty else DIM)
        surf.blit(n, (62 - n.get_width(), 64 - n.get_height()))
        k = self.slot.font.render("E", True, DIM)
        surf.blit(k, (6, 4))
        y = 10
        for food_name, count in food.items():
            t = shadowed(self.slot.font, f"{food_name.title()} x{count}", INK if count else DIM)
            surf.blit(t, (74, y))
            y += t.get_height() + 1
        g = shadowed(self.slot.font, "G eat", DIM)
        surf.blit(g, (74, y))
        y += g.get_height() + 1
        if rite:
            ready = rite_cd <= 0
            r = shadowed(self.slot.font, f"Q {rite}" + ("" if ready else f"  {math.ceil(rite_cd)} s"), INK if ready else DIM)
            surf.blit(r, (74, y))
        return surf

    # ------------------------------------------------------------------ draw
    def render(self, w: int, h: int, fighter, progress, cam_yaw: float, me: tuple[float, float], t: float,
               rite_cd: float = 0.0) -> None:
        if fighter is None:
            return
        s = self.state
        pulse = 0.5 + 0.5 * math.sin(t * 4.0) if progress.ready() else 0.0
        key = (int(hp_bar_px(fighter.max_hp) * fighter.hp / fighter.max_hp),
               int(hp_bar_px(fighter.max_hp) * fighter.trail / fighter.max_hp),
               int(st_bar_px(fighter.max_stamina) * fighter.stamina / max(fighter.max_stamina, 1e-6)),
               fighter.exhausted, int(fighter.max_hp), int(fighter.max_stamina), progress.level,
               int(200 * progress.xp / max(progress.xp_needed(), 1)), progress.ready(), int(pulse * 6),
               int(hp_bar_px(fighter.max_hp) * fighter.ward_hp / fighter.max_hp) if fighter.ward_t > 0 else -1,
               tuple(n[0] for n in s.notes[-1:]))
        if key != self._bars_key:
            self.bars.set_surface(self._bars_surface(fighter, progress, pulse))
            self._bars_key = key
        self.bars.render(w, h, x=16, y=16, alpha=s.alpha)
        rite = progress.rite()
        rite_name = rite["name"] if rite and not progress.cast_problem() else ""
        skey = (progress.flask, tuple(sorted(progress.food.items())), rite_name, math.ceil(rite_cd))
        if skey != self._slot_key:
            self.slot.set_surface(self._slot_surface(progress.flask, int(progress.cfg["lifewater"]["charges"]),
                                                     progress.food, rite_name, rite_cd))
            self._slot_key = skey
        self.slot.render(w, h, x=16, y=h - 16 - self.slot.size[1], alpha=0.95)
        if s.arc_t > 0 and s.arc_from is not None:
            ang = s.arc_direction(s.arc_from, me, cam_yaw)
            akey = int(math.degrees(ang) / 4)
            if akey != self._arc_key:
                self.arc.set_surface(pygame.transform.rotate(self._arc_base, -math.degrees(ang)))
                self._arc_key = akey
            r = min(w, h) * 0.36
            cx, cy = w / 2 + math.sin(ang) * r, h / 2 - math.cos(ang) * r
            aw, ah = self.arc.size
            self.arc.render(w, h, x=int(cx - aw / 2), y=int(cy - ah / 2), alpha=min(1.0, s.arc_t / 0.4))


# ---------------------------------------------------------------------------- level-up screen
class LevelPanel:
    """UIX-06 / STA-02: open any time out of combat. Up/Down pick an attribute, Right/Left add or take
    back a point, Enter buys the levels, Esc or L closes. Derived stats preview in green or red."""

    def __init__(self, ctx, shaders) -> None:
        self.view = TextOverlay(ctx, shaders, size=16)
        self.open = False
        self.sel = 0
        self.plan: dict[str, int] = {}
        self._key = None

    def toggle(self) -> None:
        self.open = not self.open
        self.plan, self.sel = {}, 0

    def key(self, k: int, progress) -> str | None:
        """Handle a key; returns "apply" when Enter confirms a plan."""
        names = progress.cfg["attributes"]
        if k in (pygame.K_UP, pygame.K_w):
            self.sel = (self.sel - 1) % len(names)
        elif k in (pygame.K_DOWN, pygame.K_s):
            self.sel = (self.sel + 1) % len(names)
        elif k in (pygame.K_RIGHT, pygame.K_d):
            a = names[self.sel]
            if progress.affordable() > sum(self.plan.values()):
                self.plan[a] = self.plan.get(a, 0) + 1
        elif k in (pygame.K_LEFT, pygame.K_a):
            a = names[self.sel]
            if self.plan.get(a, 0) > 0:
                self.plan[a] -= 1
        elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return "apply"
        elif k in (pygame.K_ESCAPE, pygame.K_l):
            self.toggle()
        return None

    def surface(self, progress) -> pygame.Surface:
        font = self.view.font
        lh = font.get_linesize()
        names = progress.cfg["attributes"]
        n = sum(self.plan.values())
        rows: list[list[tuple[str, tuple]]] = []
        cost = progress.plan_cost(n)
        rows.append([("LEVEL UP", GOLD)])
        rows.append([(f"Level {progress.level}" + (f" -> {progress.level + n}" if n else ""), INK),
                     (f"    XP {progress.xp}", INK),
                     (f"    next level {progress.xp_needed(progress.level + n)}", DIM),
                     (f"    cost {cost}" if n else "", GOLD)])
        rows.append([("", INK)])
        for i, a in enumerate(names):
            v, add = progress.attrs.get(a, 0), self.plan.get(a, 0)
            mark = ">" if i == self.sel else " "
            row = [(f"{mark} {a.title():<11}{v:>3}", INK if i == self.sel else DIM)]
            if add:
                row.append((f"  -> {v + add}", GREEN))
            rows.append(row)
        rows.append([("", INK)])
        now, then = progress.stats(), progress.stats(self.plan)
        for name, spec in progress.cfg["derived"].items():
            a, b = now[name], then[name]
            row = [(f"  {spec['label']:<16}{a:7.0f}", INK)]
            if round(b) != round(a):
                row.append((f"  -> {b:.0f}", GREEN if b > a else RED))
            rows.append(row)
        rows.append([("", INK)])
        hint = "Up/Down pick   Right/Left add or remove   Enter confirm   Esc close"
        if progress.affordable() == 0 and not n:
            hint = "Not enough XP for a level yet.   Esc close"
        rows.append([(hint, DIM)])
        width = max(sum(font.size(t)[0] for t, _ in r) for r in rows) + 40
        surf = pygame.Surface((width, lh * len(rows) + 32), pygame.SRCALPHA)
        surf.fill((10, 8, 14, 215))
        pygame.draw.rect(surf, (110, 90, 56), surf.get_rect(), 2)
        for i, r in enumerate(rows):
            x = 20
            for text, col in r:
                if text:
                    surf.blit(font.render(text, True, col), (x, 16 + i * lh))
                    x += font.size(text)[0]
        return surf

    def render(self, w: int, h: int, progress) -> None:
        if not self.open:
            return
        key = (progress.level, progress.xp, tuple(sorted(self.plan.items())), self.sel, tuple(progress.attrs.items()))
        if key != self._key:
            self.view.set_surface(self.surface(progress))
            self._key = key
        pw, ph = self.view.size
        self.view.render(w, h, x=(w - pw) // 2, y=(h - ph) // 2)


# ---------------------------------------------------------------------------- death screen
class DeathScreen:
    """UIX-09: the screen darkens, "AND SO THE LEGEND ENDED…" fades in, then "…or did it?", and the
    last save loads."""

    def __init__(self, ctx, shaders) -> None:
        self.dark = TextOverlay(ctx, shaders)
        s = pygame.Surface((2, 2))
        s.fill((0, 0, 0))
        self.dark.set_surface(s)
        font = pygame.font.SysFont("georgia,segoeui,dejavuserif,serif", 40)
        small = pygame.font.SysFont("georgia,segoeui,dejavuserif,serif", 30, italic=True)
        self.line1 = TextOverlay(ctx, shaders)
        self.line1.set_surface(font.render("AND SO THE LEGEND ENDED…", True, (196, 160, 112)))
        self.line2 = TextOverlay(ctx, shaders)
        self.line2.set_surface(small.render("…or did it?", True, (220, 200, 170)))

    @staticmethod
    def ramp(t: float, start: float, length: float) -> float:
        return max(0.0, min(1.0, (t - start) / length))

    def render(self, w: int, h: int, down_t: float, total: float) -> None:
        if down_t <= 0:
            return
        out = 1.0 - self.ramp(down_t, total - 0.6, 0.6)            # brighten again just before the reload
        self.dark.render(w, h, 0, 0, alpha=0.75 * self.ramp(down_t, 1.2, 1.5) * out, size=(w, h))
        a1 = self.ramp(down_t, 2.0, 1.2) * out
        lw, lh = self.line1.size
        self.line1.render(w, h, x=(w - lw) // 2, y=int(h * 0.42 - lh / 2), alpha=a1)
        a2 = self.ramp(down_t, 4.2, 1.0) * out
        l2w, l2h = self.line2.size
        self.line2.render(w, h, x=(w - l2w) // 2, y=int(h * 0.42 + lh / 2 + 12), alpha=a2)
