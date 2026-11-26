r"""Design the NPC voices with ElevenLabs Voice Design (AUD-02: designed voices only, no clones).

Descriptions and preview lines are in tools/voice/voice_designs.json. Two steps:

    .venv\Scripts\python.exe tools/voice/design_voices.py                      # dry run: list what would be designed
    .venv\Scripts\python.exe tools/voice/design_voices.py --send               # make previews for every voice
    .venv\Scripts\python.exe tools/voice/design_voices.py guard_1 --send       # or just some
    .venv\Scripts\python.exe tools/voice/design_voices.py keep guard_1 2       # save preview 2 of guard_1 as a voice

Previews are saved as assets/voice_design/<voice>/preview_<n>.mp3 (git-ignored) so you can listen
and pick. 'keep' saves the chosen one to your ElevenLabs account and records its voice ID in
data/voices.json, which the game's voice tools read. Designing again replaces that voice's previews.
The ElevenLabs docs don't list a price for Voice Design, so check your credit balance after the
first one. The key is ELEVENLABS_API_KEY, read from .env; it is never printed.
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sfx import api_key  # noqa: E402  (same .env reading as the sound effects script)

ROOT = Path(__file__).resolve().parents[2]
SPEC = Path(__file__).with_name("voice_designs.json")
OUT = ROOT / "assets" / "voice_design"
VOICES = ROOT / "data" / "voices.json"
API = "https://api.elevenlabs.io/v1/text-to-voice"


def post(url: str, body: dict, key: str, params: dict | None = None) -> dict:
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode("utf-8")
    for attempt in range(4):
        req = urllib.request.Request(url, data=data, method="POST",
                                     headers={"xi-api-key": key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (409, 429, 500, 502, 503) and attempt < 3:   # 409: a generation is still running
                time.sleep(5 * (attempt + 1))
                continue
            raw = e.read().decode("utf-8", "replace")
            try:
                detail = json.loads(raw).get("detail")
            except ValueError:
                detail = raw[:300]
            raise RuntimeError(f"HTTP {e.code}: {detail}") from None
        except urllib.error.URLError as e:
            if attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(f"network error: {e.reason}") from None
    raise RuntimeError("gave up after retries")


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def design(names: list[str], spec: dict, args) -> None:
    voices = spec["voices"]
    for n in names:
        v = voices[n]
        print(f"  {n:<17} {v['for']:<26} {v['description'][:70]}...")
    print(f"\n  {len(names)} voices, a few previews each (model {args.model})")
    if not args.send:
        print("\n  Dry run: nothing was sent. Add --send to make the previews.")
        return
    typed = input(f"\nThis designs {len(names)} voices on ElevenLabs. Type {len(names)} to go on: ").strip()
    if typed != str(len(names)):
        sys.exit("Cancelled.")
    key = api_key()
    for n in names:
        v = voices[n]
        body = {"voice_description": v["description"], "text": v["text"], "model_id": args.model}
        try:
            res = post(API + "/design", body, key, {"output_format": "mp3_44100_128"})
        except RuntimeError as e:
            print(f"  {n}: FAILED {e}")
            if any(s in str(e) for s in ("HTTP 401", "HTTP 403", "quota", "network")):
                print("  Stopping: the rest would fail the same way.")
                break
            continue
        folder = OUT / n
        folder.mkdir(parents=True, exist_ok=True)
        for old in folder.glob("preview_*.mp3"):
            old.unlink()
        ids = {}
        for i, p in enumerate(res.get("previews", []), 1):
            (folder / f"preview_{i}.mp3").write_bytes(base64.b64decode(p["audio_base_64"]))
            ids[str(i)] = p["generated_voice_id"]
        (folder / "previews.json").write_text(json.dumps({"ids": ids, "text": res.get("text"), "model": args.model},
                                                         indent=2), encoding="utf-8")
        print(f"  {n}: {len(ids)} previews in {folder.relative_to(ROOT)}")
    print("\nListen, then keep one:  .venv\\Scripts\\python.exe tools/voice/design_voices.py keep <voice> <preview number>")


def keep(name: str, number: str, spec: dict) -> None:
    v = spec["voices"].get(name)
    if v is None:
        sys.exit(f"No voice '{name}' in {SPEC.name}.")
    previews = load_json(OUT / name / "previews.json", {}).get("ids", {})
    if number not in previews:
        sys.exit(f"No preview {number} for {name}. Have: {', '.join(previews) or 'none (design it first)'}")
    res = post(API, {"voice_name": f"Lycantrope {name}", "voice_description": v["description"],
                     "generated_voice_id": previews[number],
                     "labels": {"game": "lycantrope", "role": v["for"]}}, api_key())
    vid = res["voice_id"]
    voices = load_json(VOICES, {"_about": ["Designed ElevenLabs voices (AUD-02), made by tools/voice/design_voices.py."],
                                "voices": {}})
    voices["voices"][name] = {"voice_id": vid, "for": v["for"], "description": v["description"],
                              "kept": time.strftime("%Y-%m-%d")}
    VOICES.write_text(json.dumps(voices, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {name} (preview {number}) as voice {vid}; recorded in {VOICES.relative_to(ROOT)}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Design NPC voices with ElevenLabs (dry run by default)")
    ap.add_argument("names", nargs="*", help="voices to design (default: all), or: keep <voice> <n>")
    ap.add_argument("--model", default="eleven_ttv_v3", choices=["eleven_ttv_v3", "eleven_multilingual_ttv_v2"])
    ap.add_argument("--send", action="store_true", help="actually call ElevenLabs")
    args = ap.parse_args()
    spec = load_json(SPEC, None)
    if args.names[:1] == ["keep"]:
        if len(args.names) != 3:
            sys.exit("Usage: design_voices.py keep <voice> <preview number>")
        keep(args.names[1], args.names[2], spec)
        return
    names = args.names or list(spec["voices"])
    unknown = [n for n in names if n not in spec["voices"]]
    if unknown:
        sys.exit(f"Unknown voice(s): {', '.join(unknown)}. Have: {', '.join(spec['voices'])}")
    design(names, spec, args)


if __name__ == "__main__":
    main()
