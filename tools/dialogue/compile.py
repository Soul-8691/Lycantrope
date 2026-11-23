"""Compile dialogue/*.yaml into a tes3conv JSON plugin (and an .esp if tes3conv is available).

    python tools/dialogue/compile.py               # story from config.yaml
    python tools/dialogue/compile.py --story v1
    python tools/dialogue/compile.py --no-validate # skip the checks (not recommended)

Output (git-ignored), in tools/dialogue/out/:
    tdl_dialogue.json     tes3conv JSON: the plugin as text
    tdl_dialogue.esp      built from the JSON with tes3conv, then converted back and compared
    voice_lines.csv       every line marked `voice: true`, for the ElevenLabs pipeline

The compiler orders each topic's responses exactly as they appear in the YAML
(Morrowind uses the first response whose conditions match), links them into
Morrowind's prev/next chain, and gives every response a stable ID derived from
its topic and key, so rebuilding never reshuffles IDs.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from dlg import (SourceError, build_records, find_tes3conv, group_topics, load_config,
                 load_sources, rel, repo_path, select_story)


def roundtrip(tes3conv: str, json_path: Path, esp_path: Path) -> str | None:
    """Build the .esp, convert it back, and check nothing was lost. Returns an error or None."""
    r = subprocess.run([tes3conv, "-o", str(json_path), str(esp_path)], capture_output=True, text=True)
    if r.returncode:
        return f"tes3conv failed: {r.stderr.strip() or r.stdout.strip()}"
    with tempfile.TemporaryDirectory() as tmp:
        back = Path(tmp) / "back.json"
        r = subprocess.run([tes3conv, "-o", str(esp_path), str(back)], capture_output=True, text=True)
        if r.returncode:
            return f"tes3conv could not read the .esp back: {r.stderr.strip()}"
        a = json.loads(json_path.read_text(encoding="utf-8"))
        b = json.loads(back.read_text(encoding="utf-8"))
    # tes3conv may reorder some record types (globals are sorted), so compare as a set,
    # but the order of dialogue responses must survive exactly: it decides what is said.
    canon = lambda recs: sorted(json.dumps({k: v for k, v in x.items() if k != "num_objects"},
                                           sort_keys=True, ensure_ascii=False) for x in recs)
    if canon(a) != canon(b):
        return "the .esp does not convert back to the same records"
    infos = lambda recs: [x["id"] for x in recs if x["type"] in ("Dialogue", "DialogueInfo")]
    if infos(a) != infos(b):
        return "the .esp changed the order of dialogue responses"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--story", choices=["v1", "v2"])
    ap.add_argument("--no-validate", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    cfg = load_config()
    story = args.story or cfg["story"]
    if not args.no_validate:
        import validate
        if validate.run(cfg, story, quiet=True) > 0:
            sys.exit("Validation failed; fix the errors above (or run validate.py for details).")

    src = load_sources(cfg)
    if src.errors:
        sys.exit("\n".join(src.errors))
    try:
        recs = build_records(cfg, src, story)
    except SourceError as e:
        sys.exit(str(e))

    out = repo_path(cfg["out_dir"])
    out.mkdir(parents=True, exist_ok=True)
    name = cfg["plugin"]["name"]
    json_path = out / f"{name}.json"
    json_path.write_text(json.dumps(recs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = select_story(src.lines, story)
    groups = group_topics(lines)
    n_info = sum(r["type"] == "DialogueInfo" for r in recs)
    print(f"story {story}: {len(groups)} topics/journals, {n_info} responses -> {rel(json_path)}")

    voice = [ln for ln in lines if ln.voice]
    with open(out / "voice_lines.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["speaker", "topic", "key", "info_id", "sound_path", "text"])
        for ln in voice:
            w.writerow([ln.when.get("speaker", ""), ln.topic, ln.key, ln.info_id(), ln.sound, ln.text])
    print(f"{len(voice)} voiced lines -> {rel(out / 'voice_lines.csv')}")

    tes3conv = find_tes3conv(cfg)
    if not tes3conv:
        print("tes3conv not found: skipped the .esp (set `tes3conv` in config.yaml or TES3CONV).")
        return
    esp = out / f"{name}.esp"
    err = roundtrip(tes3conv, json_path, esp)
    if err:
        sys.exit(err)
    print(f"built and round-trip checked -> {rel(esp)}")


if __name__ == "__main__":
    main()
