r"""Copy generated Meshy files from the git-ignored drafts folder into a tracked one.

    .venv\Scripts\python.exe tools/meshy/keep.py              # copy new or changed files the game needs
    .venv\Scripts\python.exe tools/meshy/keep.py --dry-run    # just list what would be copied
    .venv\Scripts\python.exe tools/meshy/keep.py --all        # copy every model, used or not
    .venv\Scripts\python.exe tools/meshy/keep.py --prune      # remove tracked models the game doesn't use

assets/meshy/previews/<ID>/... -> assets/models/meshy/<ID>/... (same layout). Only models the game
needs are copied, so Git LFS doesn't fill up with drafts:
  - models data/characters.json uses (items, armor, rigs and their clips) and the sources of
    data/props.json's props (to rebuild them);
  - rig folders (rigged.glb and its clips), unless a newer rig of the same ID is the one in use, so a
    freshly rigged character can be wired in after copying.
Untextured previews, pre-rig character models and superseded versions stay in the drafts folder only.
Thumbnails and task files are always copied (they're small). Files over --max-mb (default 20 MB) and
half-finished downloads (*.part) are skipped.

--prune deletes tracked models that fail those rules (git rm for committed ones; the drafts folder
keeps its copies). Commit the result yourself. Removing files doesn't free GitHub LFS storage that
old commits still point to; it keeps clones small and keeps new drafts out of history.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets" / "meshy" / "previews"
DST = ROOT / "assets" / "models" / "meshy"
CHARACTERS = ROOT / "data" / "characters.json"
PROPS = ROOT / "data" / "props.json"
MODEL_EXT = {".glb", ".gltf", ".fbx", ".obj"}


def _strings(o):
    if isinstance(o, dict):
        for v in o.values():
            yield from _strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from _strings(v)
    elif isinstance(o, str):
        yield o


def used_models() -> set[str]:
    """Model paths (relative to assets/models/meshy) the game and the prop builder use."""
    used = {s for s in _strings(json.loads(CHARACTERS.read_text(encoding="utf-8"))) if s.endswith(".glb")}
    props = json.loads(PROPS.read_text(encoding="utf-8"))["props"]
    used |= {p["source"] for p in props.values() if p.get("source")}
    return {u.replace("\\", "/") for u in used}


RIG = re.compile(r"^(?P<id>[^/]+)/(?P<ver>(?:[^/]+/)?v\d+)/rig/")


def needed(rel: str, used: set[str]) -> bool:
    """Should this file (path relative to the previews / tracked folder) be kept in git?"""
    rel = rel.replace("\\", "/")
    if Path(rel).suffix.lower() not in MODEL_EXT:
        return True                                    # thumbnails, task.json, gifs: small, keep
    if rel in used:
        return True
    m = RIG.match(rel)
    if m:
        rigs_in_use = {RIG.match(u).group(0) for u in used if RIG.match(u) and RIG.match(u).group("id") == m.group("id")}
        return not rigs_in_use or m.group(0) in rigs_in_use      # unless a newer rig is the one in use
    return False


def prune(used: set[str], dry: bool) -> None:
    gone = [p for p in sorted(DST.rglob("*")) if p.is_file() and not needed(p.relative_to(DST).as_posix(), used)]
    if not gone:
        print("  nothing to prune")
        return
    tracked = set(subprocess.run(["git", "ls-files", "--", str(DST.relative_to(ROOT))], cwd=ROOT,
                                 capture_output=True, text=True).stdout.splitlines())
    size = sum(p.stat().st_size for p in gone)
    for p in gone:
        print(f"  {'would remove' if dry else 'remove'}: {p.relative_to(DST).as_posix()}  ({p.stat().st_size / 1e6:.1f} MB)")
    if dry:
        print(f"\n  would remove {len(gone)} files, {size / 1e6:.1f} MB")
        return
    in_git = [p.relative_to(ROOT).as_posix() for p in gone if p.relative_to(ROOT).as_posix() in tracked]
    for i in range(0, len(in_git), 100):                # git rm in chunks (command-line length)
        subprocess.run(["git", "rm", "-q", "--", *in_git[i:i + 100]], cwd=ROOT, check=True)
    for p in gone:
        if p.exists():
            p.unlink()
    for d in sorted((d for d in DST.rglob("*") if d.is_dir()), key=lambda d: -len(d.parts)):
        if not any(d.iterdir()):
            d.rmdir()
    print(f"\n  removed {len(gone)} files, {size / 1e6:.1f} MB ({len(in_git)} were committed: commit the removal)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Copy generated Meshy files into a tracked folder")
    ap.add_argument("--max-mb", type=float, default=20.0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all", action="store_true", help="copy every model, not only the ones the game uses")
    ap.add_argument("--prune", action="store_true", help="remove tracked models the game doesn't use")
    args = ap.parse_args()
    used = used_models()
    if args.prune:
        prune(used, args.dry_run)
        return

    limit = args.max_mb * 1024 * 1024
    copied = skipped_big = same = unused = 0
    copied_bytes = 0
    for src in sorted(SRC.rglob("*")):
        if not src.is_file() or src.suffix == ".part":
            continue
        rel = src.relative_to(SRC)
        if not args.all and not needed(rel.as_posix(), used):
            unused += 1
            continue
        size = src.stat().st_size
        if size > limit:
            skipped_big += 1
            print(f"  skip (too big, {size / 1e6:.0f} MB): {rel}")
            continue
        dst = DST / rel
        if dst.exists() and dst.stat().st_size == size and dst.stat().st_mtime >= src.stat().st_mtime:
            same += 1
            continue
        copied += 1
        copied_bytes += size
        if not args.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    total = sum(p.stat().st_size for p in DST.rglob("*") if p.is_file()) if DST.exists() else 0
    verb = "would copy" if args.dry_run else "copied"
    print(f"\n  {verb} {copied} files ({copied_bytes / 1e6:.1f} MB), {same} already up to date, "
          f"{skipped_big} skipped as too big, {unused} models left out (not used by the game; --all copies them)")
    print(f"  {DST.relative_to(ROOT)} now holds {total / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
