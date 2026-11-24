"""Copy generated Meshy files from the git-ignored drafts folder into a tracked one.

    python tools/meshy/keep.py              # copy new or changed files
    python tools/meshy/keep.py --dry-run    # just list what would be copied
    python tools/meshy/keep.py --max-mb 50  # change the size limit

assets/meshy/previews/<ID>/... -> assets/models/meshy/<ID>/... (same layout). Files over the
size limit (default 20 MB, e.g. the ~175 MB full-detail haycart and bush meshes) are skipped
to stay within GitHub's free Git LFS allowance. Half-finished downloads (*.part) are skipped too.
Re-run it after each Meshy batch; unchanged files are left alone.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets" / "meshy" / "previews"
DST = ROOT / "assets" / "models" / "meshy"


def main() -> None:
    ap = argparse.ArgumentParser(description="Copy generated Meshy files into a tracked folder")
    ap.add_argument("--max-mb", type=float, default=20.0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    limit = args.max_mb * 1024 * 1024
    copied = skipped_big = same = 0
    copied_bytes = 0
    for src in sorted(SRC.rglob("*")):
        if not src.is_file() or src.suffix == ".part":
            continue
        rel = src.relative_to(SRC)
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
          f"{skipped_big} skipped as too big")
    print(f"  {DST.relative_to(ROOT)} now holds {total / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
