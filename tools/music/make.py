"""Generate a music track with the ElevenLabs Music API (AUD-07) from a prompt file in tools/music/.

    python tools/music/make.py wilds_explore          # dry run: show the prompt and length
    python tools/music/make.py wilds_explore --send   # generate assets/audio/music/wilds_explore.mp3

The JSON file is the request body as-is (prompt, music_length_ms, force_instrumental, model_id).
An existing track is kept as <name>_old.mp3 rather than overwritten. Key: ELEVENLABS_API_KEY in .env.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "voice"))
from sfx import api_key  # noqa: E402

OUT = ROOT / "assets" / "audio" / "music"


def main() -> None:
    ap = argparse.ArgumentParser(description="ElevenLabs music from tools/music/<name>.json")
    ap.add_argument("name")
    ap.add_argument("--send", action="store_true", help="actually call ElevenLabs")
    args = ap.parse_args()
    spec = Path(__file__).with_name(f"{args.name}.json")
    if not spec.exists():
        sys.exit(f"No {spec.name}. Have: {', '.join(p.stem for p in spec.parent.glob('*.json'))}")
    body = json.loads(spec.read_text(encoding="utf-8"))
    print(f"{args.name}: {body.get('music_length_ms', 0) / 1000:.0f} s, model {body.get('model_id')}\n  {body['prompt']}")
    if not args.send:
        print("\nDry run: nothing was sent. Add --send to generate.")
        return
    req = urllib.request.Request("https://api.elevenlabs.io/v1/music", data=json.dumps(body).encode("utf-8"),
                                 method="POST", headers={"xi-api-key": api_key(), "Content-Type": "application/json"})
    print("\nGenerating (this can take a minute or two)...")
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            audio = r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:400]}")
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{args.name}.mp3"
    if out.exists():
        out.replace(OUT / f"{args.name}_old.mp3")
    out.write_bytes(audio)
    print(f"Saved {out.relative_to(ROOT)} ({len(audio) // 1024} KB)")


if __name__ == "__main__":
    main()
