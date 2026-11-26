"""Make the Watch guard (WLD-25) and the villager outfits (WLD-26: WLD-27..32) with Meshy.

Two stages, each a dry run unless you add --send (batch.py then asks you to type the credit total):

    python tools/meshy/npcs.py preview          # 7 previews (20 credits each)
    python tools/meshy/npcs.py preview --send
    python tools/meshy/npcs.py finish           # look at the thumbnails first, then: texture the
    python tools/meshy/npcs.py finish --send    # outfits (10 each) and texture + rig the guard (15)

Prompts live in tools/meshy/characters.json. Only IDs approved in the tracker are sent; the
script says which ones still need approving. Re-roll a preview you don't like with
    python tools/meshy/batch.py preview WLD-29 --variants 2 --send
and finish that one by hand with --variant 2. Afterwards: python tools/meshy/keep.py
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = Path(__file__).with_name("batch.py")
GUARD = "WLD-25"
OUTFITS = ["WLD-27", "WLD-28", "WLD-29", "WLD-30", "WLD-31", "WLD-32"]


def statuses() -> dict:
    return {k: v.get("status") for k, v in
            json.loads((ROOT / "ideas_status.json").read_text(encoding="utf-8"))["ideas"].items()}


def run(*args: str) -> None:
    print(f"\n> batch.py {' '.join(args)}")
    subprocess.run([sys.executable, str(BATCH), *args], check=False)


def main() -> None:
    ap = argparse.ArgumentParser(description="Watch guard and villager outfits (Meshy)")
    ap.add_argument("stage", choices=["preview", "finish"])
    ap.add_argument("--send", action="store_true", help="actually call Meshy (spends credits)")
    args = ap.parse_args()

    st = statuses()
    ids = [GUARD] + OUTFITS
    waiting = [i for i in ids if st.get(i) != "approved"]
    if waiting:
        print(f"Not approved in the tracker yet (skipped): {', '.join(waiting)}")
    ok = [i for i in ids if i not in waiting]
    if not ok:
        sys.exit("Nothing approved to make.")
    send = ["--send"] if args.send else []

    if args.stage == "preview":
        run("preview", *ok, *send)
        return
    outfits = [i for i in OUTFITS if i in ok]
    if outfits:
        run("texture", *outfits, *send)                  # outfits are fitted to the villager rigs: no rig
    if GUARD in ok:
        run("animate", GUARD, *send)                     # texture + rig; animations come from Rowan
    if args.send:
        print("\nNext: python tools/meshy/keep.py")


if __name__ == "__main__":
    main()
