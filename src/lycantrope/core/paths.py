"""Where things live, both from source and from a PyInstaller build."""
from __future__ import annotations

import sys
from pathlib import Path

if getattr(sys, "frozen", False):                      # PyInstaller onedir build
    ROOT = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    USER = Path(sys.executable).parent
else:
    ROOT = Path(__file__).resolve().parents[3]          # src/lycantrope/core/paths.py → repo root
    USER = ROOT

ASSETS = ROOT / "assets"
DATA = ROOT / "data"
SHADERS = Path(__file__).resolve().parents[1] / "render" / "shaders"
SETTINGS_FILE = USER / "settings.json"
SCREENSHOTS = USER / "screenshots"
SAVES_DIR = USER / "saves"
