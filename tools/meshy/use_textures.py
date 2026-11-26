"""Point the game at textured models once they exist, and rebuild the props that changed.

    python tools/meshy/use_textures.py            # switch and rebuild
    python tools/meshy/use_textures.py --dry-run  # just list what would change

After `batch.py texture ... --send` and `keep.py`: every model path in data/props.json ("source")
and data/characters.json (item "model") written as <key>/model.glb gets <key>/textured/model.glb
instead, wherever that textured file has been downloaded. Changed props are then rebuilt with
tools/props/build.py. Edits only the path strings, so the files' layout and comments stay as they are.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROPS = ROOT / "data" / "props.json"
CHARS = ROOT / "data" / "characters.json"
PREVIEWS = ROOT / "assets" / "meshy" / "previews"
MODELS = ROOT / "assets" / "models" / "meshy"
PATH = re.compile(r'"((?:[A-Z]{3}-\d{2})(?:/[a-z]+)?/v\d+)/model\.glb"')


def switch(path: Path, base: Path, dry: bool) -> list[str]:
    text = path.read_text(encoding="utf-8")
    changed = []

    def sub(m: re.Match) -> str:
        key = m.group(1)
        if (base / key / "textured" / "model.glb").exists():
            changed.append(key)
            return f'"{key}/textured/model.glb"'
        return m.group(0)
    new = PATH.sub(sub, text)
    if changed and not dry:
        path.write_text(new, encoding="utf-8", newline="\n")
    return changed


def main() -> None:
    ap = argparse.ArgumentParser(description="Use textured Meshy models in the game")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    props = switch(PROPS, PREVIEWS, args.dry_run)
    items = switch(CHARS, MODELS, args.dry_run)
    verb = "would switch" if args.dry_run else "switched"
    print(f"props.json: {verb} {len(props)}: {', '.join(props) or '-'}")
    print(f"characters.json: {verb} {len(items)}: {', '.join(items) or '-'}")
    if items and not args.dry_run and any(not (MODELS / k / "textured" / "model.glb").exists() for k in items):
        print("  (run tools/meshy/keep.py first so the textured weapons are in assets/models/meshy)")
    if props and not args.dry_run:
        import json
        catalog = json.loads(PROPS.read_text(encoding="utf-8"))["props"]
        keys = [k for k, p in catalog.items() if any(p.get("source", "").startswith(s + "/textured/") for s in props)]
        print(f"rebuilding {len(keys)} props ...")
        subprocess.run([sys.executable, str(ROOT / "tools" / "props" / "build.py"), *keys], check=True)


if __name__ == "__main__":
    main()
