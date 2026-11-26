r"""Speak the NPC lines in their designed voices with ElevenLabs text to speech (AUD-01, AUD-03).

Lines are in tools/voice/npc_lines.json; voice IDs come from data/voices.json (made with
design_voices.py). Dry run is the default: it lists what's missing and estimates the cost.

    .venv\Scripts\python.exe tools/voice/npc_lines.py                    # dry run: everything that's missing
    .venv\Scripts\python.exe tools/voice/npc_lines.py guard              # one role
    .venv\Scripts\python.exe tools/voice/npc_lines.py --voice guard_1    # one voice
    .venv\Scripts\python.exe tools/voice/npc_lines.py --send             # generate (asks you to type the total)
    .venv\Scripts\python.exe tools/voice/npc_lines.py --redo --send      # remake even the ones that exist

Files: assets/audio/vo/<role>.<voice>/<event>_<n>.mp3 (n counts from 1 in the order of the lines),
so people sharing a voice (the dairymaid and the villager woman) still say their own lines.
assets/audio/vo/manifest.json remembers the text each file was made from, so editing a line remakes
just that line, adding one makes just the new one, and lines you delete have their files removed
(on a full run with --send). The game picks the lines up the next time it starts. Cost: ElevenLabs charges per character of text; the estimate uses 1 credit per
character (eleven_multilingual_v2). The key is ELEVENLABS_API_KEY in .env; it is never printed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sfx import api_key  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SPEC = Path(__file__).with_name("npc_lines.json")
VOICES = ROOT / "data" / "voices.json"
OUT = ROOT / "assets" / "audio" / "vo"
MANIFEST = OUT / "manifest.json"
CREDITS_PER_CHAR = 1.0


def load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def jobs(spec: dict, roles: list[str], only_voice: str | None) -> list[dict]:
    out = []
    for role, r in spec["roles"].items():
        if roles and role not in roles:
            continue
        for voice in r["voices"]:
            if only_voice and voice != only_voice:
                continue
            for event, lines in r["lines"].items():
                for n, text in enumerate(lines, 1):
                    h = hashlib.sha1(json.dumps([text, spec["model_id"], spec.get("voice_settings")],
                                                sort_keys=True).encode()).hexdigest()[:12]
                    out.append({"voice": voice, "file": f"{role}.{voice}/{event}_{n}.mp3", "text": text, "hash": h})
    return out


def speak(job: dict, voice_id: str, spec: dict, key: str) -> bytes:
    url = (f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?"
           + urllib.parse.urlencode({"output_format": "mp3_44100_128"}))
    body = {"text": job["text"], "model_id": spec["model_id"]}
    if spec.get("voice_settings"):
        body["voice_settings"] = spec["voice_settings"]
    data = json.dumps(body).encode("utf-8")
    for attempt in range(4):
        req = urllib.request.Request(url, data=data, method="POST",
                                     headers={"xi-api-key": key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}") from None
        except urllib.error.URLError as e:
            if attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(f"network error: {e.reason}") from None
    raise RuntimeError("gave up after retries")


def main() -> None:
    ap = argparse.ArgumentParser(description="NPC voice lines (dry run by default)")
    ap.add_argument("roles", nargs="*", help="roles to make (default: all), e.g. oswin watch_gate")
    ap.add_argument("--voice", help="only this voice, e.g. guard_1")
    ap.add_argument("--redo", action="store_true", help="remake lines even if the files exist")
    ap.add_argument("--send", action="store_true", help="actually call ElevenLabs (spends credits)")
    args = ap.parse_args()
    spec = load(SPEC, None)
    ids = {k: v["voice_id"] for k, v in load(VOICES, {}).get("voices", {}).items()}
    manifest = load(MANIFEST, {})
    all_jobs = jobs(spec, args.roles, args.voice)
    missing_voice = sorted({j["voice"] for j in all_jobs if j["voice"] not in ids})
    if missing_voice:
        print(f"  No voice ID yet for {', '.join(missing_voice)} (keep one with design_voices.py); skipped")
    todo = [j for j in all_jobs if j["voice"] in ids and (args.redo or not (OUT / j["file"]).exists()
                                                          or manifest.get(j["file"], {}).get("hash") != j["hash"])]
    # lines taken out of npc_lines.json: their old files would still be played, so they go too
    if not args.roles and not args.voice:
        wanted = {j["file"] for j in all_jobs}
        stale = [f for f in sorted(OUT.glob("*/*.mp3")) if f"{f.parent.name}/{f.name}" not in wanted]
        if stale:
            print(f"  {len(stale)} old line(s) no longer in npc_lines.json"
                  + (": removing them" if args.send else ": --send removes them"))
            if args.send:
                for f in stale:
                    f.unlink()
                    manifest.pop(f"{f.parent.name}/{f.name}", None)
                MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False),
                                    encoding="utf-8")
    chars = sum(len(j["text"]) for j in todo)
    total = round(chars * CREDITS_PER_CHAR)
    by_voice: dict[str, int] = {}
    for j in todo:
        by_voice[j["voice"]] = by_voice.get(j["voice"], 0) + 1
    for v, n in by_voice.items():
        print(f"  {v:<17} {n} lines")
    print(f"\n  {len(todo)} of {len(all_jobs)} lines to make, {chars} characters, about {total} credits")
    if not todo:
        return
    if not args.send:
        print("\n  Dry run: nothing was sent. Add --send to generate.")
        return
    typed = input(f"\nThis spends about {total} ElevenLabs credits. Type {total} to go on: ").strip()
    if typed != str(total):
        sys.exit("Cancelled.")
    key = api_key()
    failed = 0
    for i, j in enumerate(todo, 1):
        try:
            audio = speak(j, ids[j["voice"]], spec, key)
        except RuntimeError as e:
            failed += 1
            print(f"  [{i}/{len(todo)}] {j['file']}  FAILED: {e}")
            if any(s in str(e) for s in ("HTTP 401", "HTTP 403", "quota", "network")):
                print("  Stopping: the rest would fail the same way.")
                break
            continue
        path = OUT / j["file"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(audio)
        manifest[j["file"]] = {"hash": j["hash"], "text": j["text"]}
        MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
        print(f"  [{i}/{len(todo)}] {j['file']}  \"{j['text']}\"")
    print(f"\n  Done: {len(todo) - failed} made, {failed} failed.")


if __name__ == "__main__":
    main()
