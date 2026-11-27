"""The pause menu (UIX-07): Inventory, Character, Settings and Game tabs. The world stops while it's open.

Keys: Q / E (or Tab) switch tabs · arrows or WASD move · Enter or Space use, equip or take off · X drop ·
Esc or I close. The mouse works too: click to pick, double-click to use, click a tab to switch.

Inventory: six equipment slots, the 20-slot backpack, and the picked item's details with the change it would
make to Rowan's stats (green better, red worse). Requirements he doesn't meet show in red (WPR-03, ARS-01).
"""
from __future__ import annotations

import math
import time

import pygame

from lycantrope.ui.hud import DIM, GOLD, GREEN, INK, RED
from lycantrope.ui.overlay import TextOverlay
from lycantrope.world.inventory import BACKPACK, SLOT_LABELS, SLOTS, shortfalls

TABS = ("Inventory", "Character", "Settings", "Game")
W, H = 1080, 640
COLS, ROWS = 5, 4
CELL_W, CELL_H, GAP = 90, 66, 6
EQ_X, BAG_X, INFO_X, TOP = 24, 264, 758, 70
BG = (14, 11, 16, 236)
FRAME = (122, 98, 60)
PANEL = (28, 23, 30, 255)
KIND_LABELS = {"weapon": "Weapon", "catalyst": "Magic weapon", "shield": "Shield", "armor": "Armor",
               "food": "Food", "material": "Material", "currency": "Currency"}
SETTINGS = [  # (field, label, kind, low, high, step)
    ("music_volume", "Music volume", "frac", 0.0, 1.0, 0.1),
    ("sfx_volume", "Sound effects volume", "frac", 0.0, 1.0, 0.1),
    ("subtitles", "Subtitles", "bool", 0, 1, 1),
    ("mouse_sensitivity", "Mouse sensitivity", "num", 0.001, 0.008, 0.0005),
    ("invert_y", "Invert mouse Y", "bool", 0, 1, 1),
    ("fov_deg", "Field of view", "deg", 55.0, 100.0, 5.0),
    ("pixel_scale", "Pixel size", "int", 1, 4, 1),
    ("pixel_smooth", "Smooth pixels", "bool", 0, 1, 1),
    ("flat_shade", "Faceted shading", "bool", 0, 1, 1),
]
GAME = ("Resume", "Save game", "Quit game")


def wrap(font, text: str, width: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if font.size(trial)[0] <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


class PauseMenu:
    def __init__(self, ctx, shaders, app) -> None:
        self.app = app
        self.view = TextOverlay(ctx, shaders)
        self.dim = TextOverlay(ctx, shaders)
        black = pygame.Surface((2, 2))
        black.fill((0, 0, 0))
        self.dim.set_surface(black)
        self.f_title = pygame.font.SysFont("georgia,segoeui,dejavuserif,serif", 22)
        self.f_head = pygame.font.SysFont("segoeui,georgia,dejavusans,arial", 16, bold=True)
        self.f = pygame.font.SysFont("segoeui,georgia,dejavusans,arial", 15)
        self.f_small = pygame.font.SysFont("segoeui,georgia,dejavusans,arial", 13)
        self.open = False
        self.tab = 0
        self.focus = "bag"                      # or "equip"
        self.sel_bag = self.sel_eq = self.sel_set = self.sel_game = 0
        self.dirty = True
        self.hits: list[tuple[pygame.Rect, tuple]] = []
        self._rect = (0, 0, W, H)
        self._last_click = (0.0, None)
        self.colors = app.rarity_colors

    # ------------------------------------------------------------------ open / close
    def show(self, tab: int = 0) -> None:
        self.open, self.tab, self.dirty = True, tab, True
        self.sel_bag = min(self.sel_bag, max(0, len(self.inv.bag) - 1))

    def close(self) -> None:
        self.open = False

    @property
    def inv(self):
        return self.app.chars.progress.inv

    # ------------------------------------------------------------------ input
    def key(self, k: int) -> None:
        self.dirty = True
        if k in (pygame.K_ESCAPE,) or (k == pygame.K_i and self.tab == 0):
            self.close()
            return
        if k in (pygame.K_q, pygame.K_e, pygame.K_TAB):
            self.tab = (self.tab + (-1 if k == pygame.K_q else 1)) % len(TABS)
            return
        dx = (k in (pygame.K_RIGHT, pygame.K_d)) - (k in (pygame.K_LEFT, pygame.K_a))
        dy = (k in (pygame.K_DOWN, pygame.K_s)) - (k in (pygame.K_UP, pygame.K_w))
        use = k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
        name = TABS[self.tab]
        if name == "Inventory":
            if dx or dy:
                self._move(dx, dy)
            elif use:
                self._use()
            elif k == pygame.K_x:
                self._drop()
        elif name == "Settings":
            if dy:
                self.sel_set = (self.sel_set + dy) % len(SETTINGS)
            elif dx or use:
                self._change(dx or 1)
        elif name == "Game":
            if dy:
                self.sel_game = (self.sel_game + dy) % len(GAME)
            elif use:
                self._game(self.sel_game)

    def _move(self, dx: int, dy: int) -> None:
        if self.focus == "equip":
            if dx > 0:
                self.focus = "bag"
                self.sel_bag = min(self.sel_bag, BACKPACK - 1)
            else:
                self.sel_eq = (self.sel_eq + dy) % len(SLOTS)
            return
        c, r = self.sel_bag % COLS, self.sel_bag // COLS
        if dx < 0 and c == 0:
            self.focus = "equip"
            return
        c = max(0, min(COLS - 1, c + dx))
        r = max(0, min(ROWS - 1, r + dy))
        self.sel_bag = r * COLS + c

    def click(self, pos: tuple[int, int], button: int) -> None:
        x0, y0, sw, sh = self._rect
        px, py = (pos[0] - x0) * W / sw, (pos[1] - y0) * H / sh
        now = time.perf_counter()
        for rect, act in self.hits:
            if rect.collidepoint(px, py):
                double = self._last_click[1] == act and now - self._last_click[0] < 0.35
                self._last_click = (now, act)
                self._act(act, double, button)
                self.dirty = True
                return

    def _act(self, act: tuple, double: bool, button: int) -> None:
        kind, i = act
        if kind == "tab":
            self.tab = i
        elif kind == "bag":
            self.focus, self.sel_bag = "bag", i
            if double:
                self._use()
        elif kind == "equip":
            self.focus, self.sel_eq = "equip", i
            if double:
                self._use()
        elif kind == "set":
            self.sel_set = i
            self._change(-1 if button == 3 else 1)
        elif kind == "game":
            self.sel_game = i
            self._game(i)

    # ------------------------------------------------------------------ actions
    def selected(self) -> str | None:
        if self.focus == "equip":
            return self.inv.equipped[SLOTS[self.sel_eq]]
        return self.inv.bag[self.sel_bag][0] if self.sel_bag < len(self.inv.bag) else None

    def _use(self) -> None:
        app, inv = self.app, self.inv
        note = app.hud.state.note
        if self.focus == "equip":
            slot = SLOTS[self.sel_eq]
            iid = inv.equipped[slot]
            if iid is None:
                return
            if not inv.unequip(slot):
                note("No room in the backpack")
                return
            app.chars.equipment_changed()
            return
        iid = self.selected()
        if iid is None:
            return
        item = inv.catalog[iid]
        if item["kind"] == "food":
            if app.play and app.chars.eat(iid):
                note(f"Ate {item['name'].lower()}")
            return
        if item["slot"]:
            inv.equip(self.sel_bag)
            app.chars.equipment_changed()
            miss = shortfalls(item, app.chars.progress.attrs)
            if miss:
                note(f"{item['name']}: requirements not met")

    def _drop(self) -> None:
        if self.focus != "bag" or self.sel_bag >= len(self.inv.bag):
            return
        iid = self.inv.bag[self.sel_bag][0]
        if self.inv.catalog[iid]["bound"]:
            self.app.hud.state.note("Too important to leave behind")
            return
        got = self.inv.take_slot(self.sel_bag)
        if got:
            self.app.drop_item(*got)
        self.sel_bag = min(self.sel_bag, max(0, len(self.inv.bag) - 1))

    def _change(self, d: int) -> None:
        field, _label, kind, lo, hi, step = SETTINGS[self.sel_set]
        s = self.app.settings
        v = getattr(s, field)
        if kind == "bool":
            v = not v
        elif kind == "int":
            v = int(max(lo, min(hi, v + d * step)))
        else:
            v = round(max(lo, min(hi, v + d * step)), 4)
        setattr(s, field, v)
        self.app.apply_settings(field)

    def _game(self, i: int) -> None:
        if GAME[i] == "Resume":
            self.close()
        elif GAME[i] == "Save game":
            if self.app.play:
                self.app.save()
            else:
                self.app.hud.state.note("Saving needs Rowan (F4)")
        elif GAME[i] == "Quit game":
            self.app.quit_requested = True

    # ------------------------------------------------------------------ drawing helpers
    def _text(self, surf, font, text, color, pos) -> int:
        img = font.render(text, True, color)
        surf.blit(img, pos)
        return img.get_width()

    def _rarity(self, item: dict | None) -> tuple:
        return tuple(self.colors.get(item["rarity"], INK)) if item else DIM

    def _box(self, surf, rect, selected: bool, color=FRAME) -> None:
        pygame.draw.rect(surf, PANEL, rect, border_radius=4)
        pygame.draw.rect(surf, GOLD if selected else color, rect, 2 if selected else 1, border_radius=4)

    # ------------------------------------------------------------------ tabs
    def surface(self) -> pygame.Surface:
        surf = pygame.Surface((W, H), pygame.SRCALPHA)
        surf.fill(BG)
        pygame.draw.rect(surf, FRAME, surf.get_rect(), 2)
        self.hits = []
        x = 24
        for i, name in enumerate(TABS):
            img = self.f_title.render(name, True, GOLD if i == self.tab else DIM)
            r = pygame.Rect(x - 8, 12, img.get_width() + 16, 38)
            if i == self.tab:
                pygame.draw.line(surf, GOLD, (r.x + 6, r.bottom - 2), (r.right - 6, r.bottom - 2), 2)
            surf.blit(img, (x, 16))
            self.hits.append((r, ("tab", i)))
            x += img.get_width() + 36
        copper = self.inv.count("copper")
        self._text(surf, self.f_head, f"{copper} copper", GOLD, (W - 24 - self.f_head.size(f"{copper} copper")[0], 22))
        pygame.draw.line(surf, FRAME, (16, 56), (W - 16, 56), 1)
        getattr(self, "_tab_" + TABS[self.tab].lower())(surf)
        hint = {"Inventory": "Arrows move   Enter equip / use / take off   X drop   Q / E tabs   Esc resume",
                "Character": "Q / E tabs   Esc resume",
                "Settings": "Up / Down pick   Left / Right change   Q / E tabs   Esc resume",
                "Game": "Up / Down pick   Enter choose   Q / E tabs   Esc resume"}[TABS[self.tab]]
        self._text(surf, self.f_small, hint, DIM, (24, H - 28))
        return surf

    def _tab_inventory(self, surf) -> None:
        inv, prog = self.inv, self.app.chars.progress
        attrs = prog.attrs
        self._text(surf, self.f_head, "Equipped", INK, (EQ_X, TOP))
        for i, slot in enumerate(SLOTS):
            r = pygame.Rect(EQ_X, TOP + 26 + i * 66, 220, 58)
            self._box(surf, r, self.focus == "equip" and self.sel_eq == i)
            self._text(surf, self.f_small, SLOT_LABELS[slot], DIM, (r.x + 10, r.y + 6))
            iid = inv.equipped[slot]
            item = inv.catalog.get(iid) if iid else None
            name = item["name"] if item else ("Fists" if slot == "mainhand" else "—")
            self._text(surf, self.f, name, self._rarity(item) if item else DIM, (r.x + 10, r.y + 27))
            if item and shortfalls(item, attrs):
                self._text(surf, self.f_head, "!", RED, (r.right - 18, r.y + 18))
            self.hits.append((r, ("equip", i)))
        used, cap = prog.equip_load()
        y = TOP + 26 + 6 * 66 + 6
        self._text(surf, self.f_small, f"Equip load  {used:.1f} / {cap:.1f}   ({prog.roll_class()} roll)", INK, (EQ_X, y))
        bar = pygame.Rect(EQ_X, y + 22, 220, 8)
        pygame.draw.rect(surf, (40, 34, 40), bar, border_radius=3)
        frac = min(1.0, used / max(cap, 1e-6))
        col = GREEN if frac < 0.3 else GOLD if frac < 0.7 else RED
        pygame.draw.rect(surf, col, (bar.x, bar.y, int(bar.w * frac), bar.h), border_radius=3)
        for m in (0.3, 0.7):
            pygame.draw.line(surf, DIM, (bar.x + int(bar.w * m), bar.y - 2), (bar.x + int(bar.w * m), bar.bottom + 1))

        self._text(surf, self.f_head, f"Backpack   {len(inv.bag)} / {BACKPACK}", INK, (BAG_X, TOP))
        for i in range(BACKPACK):
            c, r_ = i % COLS, i // COLS
            r = pygame.Rect(BAG_X + c * (CELL_W + GAP), TOP + 26 + r_ * (CELL_H + GAP), CELL_W, CELL_H)
            stack = inv.bag[i] if i < len(inv.bag) else None
            item = inv.catalog[stack[0]] if stack else None
            sel = self.focus == "bag" and self.sel_bag == i
            self._box(surf, r, sel, self._rarity(item) if item else (60, 52, 58))
            if item:
                for j, line in enumerate(wrap(self.f_small, item["name"], CELL_W - 10)[:3]):
                    self._text(surf, self.f_small, line, self._rarity(item), (r.x + 5, r.y + 4 + j * 16))
                if stack[1] > 1:
                    t = f"x{stack[1]}"
                    self._text(surf, self.f_small, t, INK, (r.right - 6 - self.f_small.size(t)[0], r.bottom - 18))
                if shortfalls(item, attrs):
                    self._text(surf, self.f_small, "!", RED, (r.x + 5, r.bottom - 18))
            self.hits.append((r, ("bag", i)))
        self._details(surf)

    def _details(self, surf) -> None:
        inv, prog = self.inv, self.app.chars.progress
        r = pygame.Rect(INFO_X, TOP, W - INFO_X - 24, H - TOP - 44)
        self._box(surf, r, False)
        iid = self.selected()
        x, y, width = r.x + 14, r.y + 12, r.w - 28
        if iid is None:
            self._text(surf, self.f, "Nothing here.", DIM, (x, y))
            return
        item = inv.catalog[iid]
        spec = item["spec"]
        for line in wrap(self.f_title, item["name"], width):
            self._text(surf, self.f_title, line, self._rarity(item), (x, y))
            y += 28
        sub = f"{KIND_LABELS.get(item['kind'], item['kind'])}"
        if item["kind"] == "armor":
            sub += f"  ·  {SLOT_LABELS[item['slot']]}  ·  {spec.get('weight_class', '')}"
        sub += f"  ·  {item['rarity']}"
        self._text(surf, self.f_small, sub, DIM, (x, y))
        y += 24
        rows: list[tuple[str, tuple]] = []
        if item["kind"] in ("weapon", "catalyst"):
            rows.append(("Damage  " + "  ".join(f"{t} {v:g}" for t, v in spec["damage"].items()), INK))
            if spec.get("scaling"):
                rows.append(("Scaling  " + "  ".join(f"{a.title()} {g}" for a, g in spec["scaling"].items()), INK))
            rows.append((f"Reach {spec.get('reach_m', 0):g} m   Poise damage {spec.get('poise_damage', 0)}", INK))
        elif item["kind"] == "shield":
            phys = spec["block"].get("slash", 0) * 100
            rows.append((f"Stability {spec['stability']}   Blocks {phys:.0f}% physical", INK))
        elif item["kind"] == "armor":
            d = spec.get("defence", {})
            rows.append(("Defence  " + "  ".join(f"{t} {v:g}" for t, v in d.items()), INK))
            rows.append((f"Poise {spec.get('poise', 0)}", INK))
        elif item["kind"] == "food":
            rows.append((f"Heals {spec['heal']} HP over {spec['seconds']:g} s", INK))
        if item["weight"]:
            rows.append((f"Weight {item['weight']:g}", INK))
        req = item["requirements"]
        if req:
            miss = shortfalls(item, prog.attrs)
            parts = [(f"{a.title()} {n}", RED if a in miss else INK) for a, n in req.items()]
            rows.append(("__req__", parts))
        for text, col in rows:
            if text == "__req__":
                xx = x + self._text(surf, self.f, "Requires  ", INK, (x, y))
                for t, c in col:
                    xx += self._text(surf, self.f, t + "   ", c, (xx, y))
            else:
                self._text(surf, self.f, text, col, (x, y))
            y += 21
        if item["requirements"] and shortfalls(item, prog.attrs):
            why = ("No scaling, and attacks cost 25% more stamina." if item["kind"] in ("weapon", "catalyst")
                   else "Half defence and poise, 50% more weight." if item["kind"] == "armor" else "")
            if why:
                self._text(surf, self.f_small, why, RED, (x, y))
                y += 19
        y += 8
        for line in wrap(self.f_small, item["text"], width)[:6]:
            self._text(surf, self.f_small, line, DIM, (x, y))
            y += 17
        compare = self._compare()
        if compare:
            y = max(y + 10, r.bottom - 22 * len(compare) - 34)
            self._text(surf, self.f_head, "If equipped", INK, (x, y))
            y += 24
            for label, a, b, fmt, better_high in compare:
                self._text(surf, self.f, label, INK, (x, y))
                t = fmt(a)
                self._text(surf, self.f, t, INK, (x + 120, y))
                if fmt(b) != t:
                    good = (b > a) == better_high
                    self._text(surf, self.f, "->  " + fmt(b), GREEN if good else RED, (x + 185, y))
                y += 22

    def _compare(self) -> list | None:
        """Rowan's numbers now and with the picked backpack item equipped (UIX-07's stat delta)."""
        if self.focus != "bag" or self.sel_bag >= len(self.inv.bag):
            return None
        item = self.inv.catalog[self.inv.bag[self.sel_bag][0]]
        if not item["slot"]:
            return None
        prog = self.app.chars.progress

        def numbers():
            f = prog.fighter()
            used, cap = prog.equip_load()
            phys = sum(f.defence.get(t, 0) for t in ("slash", "strike", "pierce")) / 3
            return (sum(f.attack.values()), phys, f.poise_max, 100 * used / max(cap, 1e-6))

        before = numbers()
        saved = self.inv.to_dict()
        self.inv.equip(self.sel_bag)
        after = numbers()
        self.inv.from_dict(saved)
        return [("Attack", before[0], after[0], lambda v: f"{v:.0f}", True),
                ("Defence", before[1], after[1], lambda v: f"{v:.0f}", True),
                ("Poise", before[2], after[2], lambda v: f"{v:.0f}", True),
                ("Equip load", before[3], after[3], lambda v: f"{v:.0f}%", False)]

    def _tab_character(self, surf) -> None:
        prog = self.app.chars.progress
        d, f = prog.stats(), prog.fighter()
        used, cap = prog.equip_load()
        x, y = 40, TOP + 4
        self._text(surf, self.f_title, "Rowan Fenhallow", GOLD, (x, y))
        y += 34
        self._text(surf, self.f, f"Level {prog.level}     XP {prog.xp}  (next level {prog.xp_needed()})", INK, (x, y))
        y += 34
        self._text(surf, self.f_head, "Attributes", INK, (x, y))
        y += 26
        for a in prog.cfg["attributes"]:
            self._text(surf, self.f, a.title(), DIM, (x, y))
            self._text(surf, self.f, str(prog.attrs.get(a, 0)), INK, (x + 140, y))
            y += 23
        x, y = 420, TOP + 72
        self._text(surf, self.f_head, "Stats", INK, (x, y))
        y += 26
        rows = [("HP", f"{d['hp']:.0f}"), ("Stamina", f"{d['stamina']:.0f}"),
                ("Equip load", f"{used:.1f} / {cap:.1f}  ({prog.roll_class()} roll)"),
                ("Attack", "  ".join(f"{t} {v:.0f}" for t, v in f.attack.items())),
                ("Defence", "  ".join(f"{t} {f.defence.get(t, 0):.0f}" for t in ("slash", "strike", "pierce"))),
                ("Poise", f"{f.poise_max:.0f}"), ("Critical chance", f"{d['crit_chance']:.1f}%"),
                ("Rite power", f"{d['rite_power']:.0f}"),
                ("Weapon", prog.weapon()["name"] + ("" if prog.weapon_ok() else "  (requirements not met)"))]
        for label, val in rows:
            self._text(surf, self.f, label, DIM, (x, y))
            self._text(surf, self.f, val, INK if "not met" not in val else RED, (x + 150, y))
            y += 24

    def _tab_settings(self, surf) -> None:
        s = self.app.settings
        x, y = 40, TOP + 8
        for i, (field, label, kind, *_r) in enumerate(SETTINGS):
            v = getattr(s, field)
            val = ("On" if v else "Off") if kind == "bool" else f"{v * 100:.0f}%" if kind == "frac" \
                else f"{v:.0f}°" if kind == "deg" else f"{v:.4f}" if kind == "num" else str(v)
            r = pygame.Rect(x - 10, y - 4, 560, 34)
            if i == self.sel_set:
                self._box(surf, r, True)
            self._text(surf, self.f, label, INK if i == self.sel_set else DIM, (x, y + 4))
            self._text(surf, self.f, f"<  {val}  >", GOLD if i == self.sel_set else INK, (x + 330, y + 4))
            self.hits.append((r, ("set", i)))
            y += 42
        self._text(surf, self.f_small, "Changes save straight away. Click to raise a value, right-click to lower it.",
                   DIM, (x, y + 6))

    def _tab_game(self, surf) -> None:
        x, y = W // 2 - 120, TOP + 80
        for i, label in enumerate(GAME):
            r = pygame.Rect(x, y, 240, 52)
            self._box(surf, r, i == self.sel_game)
            img = self.f_title.render(label, True, GOLD if i == self.sel_game else INK)
            surf.blit(img, (r.centerx - img.get_width() // 2, r.centery - img.get_height() // 2))
            self.hits.append((r, ("game", i)))
            y += 70

    # ------------------------------------------------------------------ draw
    def render(self, w: int, h: int) -> None:
        if not self.open:
            return
        if self.dirty:
            self.view.set_surface(self.surface())
            self.dirty = False
        k = min(1.0, (w - 40) / W, (h - 40) / H)
        sw, sh = int(W * k), int(H * k)
        self._rect = ((w - sw) // 2, (h - sh) // 2, sw, sh)
        self.dim.render(w, h, 0, 0, alpha=0.6, size=(w, h))
        self.view.render(w, h, x=self._rect[0], y=self._rect[1], size=(sw, sh))
