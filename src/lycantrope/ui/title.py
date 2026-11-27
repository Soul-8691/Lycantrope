"""Title / slot-select screen shown before the OpenGL window opens (UIX-27).

Runs in plain 2D pygame (no GL).  App.__init__ calls set_mode() again with
OPENGL flags, which replaces the 2D surface with an OpenGL context.

Usage::

    pygame.display.init()
    pygame.font.init()
    action, slot = title.run()   # ("new", 0..2) or ("load", 0..2) or ("quit", 0)
"""
from __future__ import annotations

from datetime import datetime

import pygame

import lycantrope.core.save as save_sys

_BG     = (8,   8,  12)
_GOLD   = (220, 180, 80)
_WHITE  = (200, 200, 200)
_DIM    = (90,  90, 100)
_SEL_BG = (28,  28,  48)
_BORDER = (55,  55,  85)
_W, _H  = 680, 440


def _fmt_time(seconds: float) -> str:
    m = int(seconds) // 60
    return f"{m // 60}h {m % 60:02d}m"


def _fmt_ts(ts: str) -> str:
    try:
        return datetime.fromisoformat(ts).strftime("%d %b %Y  %H:%M")
    except Exception:
        return ts


def run() -> tuple[str, int]:
    """Display the title screen and return ("new"|"load"|"quit", slot_index).

    Expects pygame.display and pygame.font to already be initialised."""
    screen = pygame.display.set_mode((_W, _H))
    pygame.display.set_caption("Lycantrope")

    big   = pygame.font.SysFont("georgia",  44, bold=True)
    med   = pygame.font.SysFont("consolas", 20)
    small = pygame.font.SysFont("consolas", 13)

    slots = save_sys.list_slots()
    # start cursor on the first occupied slot; default to 0
    sel = next((i for i, s in enumerate(slots) if s is not None), 0)

    clock  = pygame.time.Clock()
    result = ("quit", 0)
    running = True

    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_UP:
                    sel = (sel - 1) % save_sys.NUM_SLOTS
                elif ev.key == pygame.K_DOWN:
                    sel = (sel + 1) % save_sys.NUM_SLOTS
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    result = ("load" if slots[sel] is not None else "new", sel)
                    running = False
                elif ev.key == pygame.K_DELETE and slots[sel] is not None:
                    save_sys.clear(sel)
                    slots[sel] = None
                    # keep cursor on a valid slot after deletion
                    if all(s is None for s in slots):
                        sel = 0

        screen.fill(_BG)

        # title
        t = big.render("LYCANTROPE", True, _GOLD)
        screen.blit(t, (_W // 2 - t.get_width() // 2, 44))

        sub = small.render("select a save slot", True, _DIM)
        screen.blit(sub, (_W // 2 - sub.get_width() // 2, 104))

        # slot rows
        ROW_H, ROW_Y0, PAD = 56, 148, 16
        for i, slot in enumerate(slots):
            y    = ROW_Y0 + i * (ROW_H + 10)
            rect = pygame.Rect(PAD * 4, y, _W - PAD * 8, ROW_H)

            if i == sel:
                pygame.draw.rect(screen, _SEL_BG, rect, border_radius=5)
                pygame.draw.rect(screen, _GOLD,   rect, 1, border_radius=5)
            else:
                pygame.draw.rect(screen, _BORDER, rect, 1, border_radius=5)

            if slot is not None:
                label  = (f"Slot {i + 1}   "
                          f"Level {slot['level']}   "
                          f"{_fmt_time(slot['play_time_s'])}   "
                          f"{_fmt_ts(slot['timestamp'])}")
                action = "LOAD"
                col    = _WHITE if i == sel else _DIM
            else:
                label  = f"Slot {i + 1}   —  new game  —"
                action = "NEW"
                col    = (_DIM[0] + 20, _DIM[1] + 20, _DIM[2] + 20) if i == sel else _DIM

            screen.blit(med.render(label, True, col),
                        (rect.x + 14, rect.y + 10))

            act_col  = _GOLD if i == sel else _BORDER
            act_surf = small.render(action, True, act_col)
            screen.blit(act_surf, (rect.right - act_surf.get_width() - 14, rect.y + 36))

        # hint bar
        hints = "↑↓ select   Enter start/load   Del clear slot   Esc quit"
        h = small.render(hints, True, (55, 55, 75))
        screen.blit(h, (_W // 2 - h.get_width() // 2, _H - 28))

        pygame.display.flip()
        clock.tick(60)

    return result
