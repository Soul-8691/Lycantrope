"""Save slots: up to 3 JSON files in USER/saves/ (TEC-16, UIX-27).

Each slot stores Rowan's progress snapshot, his respawn position, and total
play time.  The in-memory death-rollback (Progress._saved / spawn_point) is
kept in sync with the disk every time App.save() is called, so a death after
a session crash still restores to the last write.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from lycantrope.core.paths import SAVES_DIR

NUM_SLOTS = 3
VERSION = 1


def _path(slot: int) -> Path:
    return SAVES_DIR / f"slot_{slot}.json"


def metadata(slot: int) -> dict | None:
    """Return a small info dict for the slot, or None if the slot is empty."""
    p = _path(slot)
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return {
            "slot": slot,
            "timestamp": d.get("timestamp", ""),
            "level": d.get("progress", {}).get("level", 1),
            "play_time_s": float(d.get("play_time_s", 0.0)),
        }
    except Exception:
        return None


def list_slots() -> list[dict | None]:
    return [metadata(i) for i in range(NUM_SLOTS)]


def save(slot: int, progress_snap: dict, spawn: dict, play_time_s: float) -> None:
    SAVES_DIR.mkdir(parents=True, exist_ok=True)
    serialisable = {
        **progress_snap,
        **{k: sorted(progress_snap.get(k, ())) for k in ("discovered", "opened")},
    }
    _path(slot).write_text(
        json.dumps({
            "version": VERSION,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "play_time_s": play_time_s,
            "progress": serialisable,
            "spawn": spawn,
        }, indent=2),
        encoding="utf-8",
    )


def load(slot: int) -> dict | None:
    """Return the save dict, or None if the slot is empty or unreadable.
    `progress["discovered"]` and `progress["opened"]` are converted back to sets."""
    p = _path(slot)
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        prog = d.get("progress", {})
        prog["discovered"] = set(prog.get("discovered", []))
        prog["opened"] = set(prog.get("opened", []))
        return d
    except Exception:
        return None


def clear(slot: int) -> None:
    p = _path(slot)
    if p.exists():
        p.unlink()
