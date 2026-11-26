r"""Character and creature sound effects with the ElevenLabs Sound Effects API (AUD-05, AUD-06).

The sound list is tools/voice/sfx.json. Dry run is the default: it sends nothing and prints what
would be made and the credit cost (40 credits per second per take, since every sound sets its
length). Sending needs --send, and it also asks you to type the credit total.

    .venv\Scripts\python.exe tools/voice/sfx.py                       # dry run: everything that's missing
    .venv\Scripts\python.exe tools/voice/sfx.py wolf bear             # only these groups
    .venv\Scripts\python.exe tools/voice/sfx.py wolf --sound howl     # one sound
    .venv\Scripts\python.exe tools/voice/sfx.py --send                # generate (asks for the credit total)
    .venv\Scripts\python.exe tools/voice/sfx.py wolf --redo --send    # regenerate even if the files exist

Files go to assets/audio/sfx/<group>/<sound>_<n>.mp3. assets/audio/sfx/manifest.json remembers the
prompt each file was made from, so a sound is only made again when its prompt, length or settings
change (or with --redo). The key is ELEVENLABS_API_KEY, read from .env; it is never printed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = Path(__file__).with_name("sfx.json")
OUT = ROOT / "assets" / "audio" / "sfx"
MANIFEST = OUT / "manifest.json"
URL = "https://api.elevenlabs.io/v1/sound-generation"
CREDITS_PER_SECOND = 40


def load_spec(path: Path = SPEC) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def jobs(spec: dict, groups: list[str] | None = None, sound: str | None = None) -> list[dict]:
    """Every (group, sound, take) to make, with its full prompt and request body."""
    out = []
    style = spec.get("style", "")
    known = spec["groups"]
    for g in groups or []:
        if g not in known:
            sys.exit(f"Unknown group '{g}'. Groups: {', '.join(known)}")
    for gname, group in known.items():
        if groups and gname not in groups:
            continue
        voice = group.get("voice", "")
        for sname, s in group["sounds"].items():
            if sound and sname != sound:
                continue
            text = " ".join(p for p in (voice, s["prompt"].rstrip(".") + ".", style) if p)
            seconds = float(s["seconds"])
            if not 0.5 <= seconds <= 30:
                sys.exit(f"{gname}/{sname}: seconds must be 0.5 to 30 (got {seconds})")
            body = {"text": text, "duration_seconds": seconds,
                    "prompt_influence": float(s.get("influence", spec.get("influence", 0.3))),
                    "model_id": spec.get("model_id", "eleven_text_to_sound_v3")}
            if s.get("loop"):
                body["loop"] = True
            digest = hashlib.sha1(json.dumps([body, spec.get("output_format")], sort_keys=True)
                                  .encode()).hexdigest()[:12]
            for n in range(1, int(s.get("takes", 1)) + 1):
                rel = f"{gname}/{sname}_{n}.mp3"
                out.append({"group": gname, "sound": sname, "take": n, "file": rel,
                            "body": body, "hash": digest, "seconds": seconds})
    if sound and not out:
        sys.exit(f"No sound called '{sound}' in those groups.")
    return out


def load_manifest() -> dict:
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_manifest(m: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, indent=2, sort_keys=True), encoding="utf-8")


def todo(all_jobs: list[dict], manifest: dict, redo: bool) -> list[dict]:
    """Drop jobs whose file exists and was made from the same prompt and settings."""
    if redo:
        return all_jobs
    return [j for j in all_jobs
            if not ((OUT / j["file"]).exists() and manifest.get(j["file"], {}).get("hash") == j["hash"])]


def cost(js: list[dict]) -> int:
    return round(sum(j["seconds"] for j in js) * CREDITS_PER_SECOND)


def read_env_file(path: Path) -> dict[str, str]:
    """Minimal .env reader (KEY=value lines), so the script needs no extra packages."""
    out = {}
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        return out
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip().removeprefix("export ").strip()
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        out[k] = v
    return out


def api_key() -> str:
    key = os.environ.get("ELEVENLABS_API_KEY", "") or read_env_file(ROOT / ".env").get("ELEVENLABS_API_KEY", "")
    if not key:
        sys.exit("ELEVENLABS_API_KEY is not set (put it in .env).")
    return key


def generate(job: dict, key: str, output_format: str) -> bytes:
    """One generation. Standard library only (urllib), so any Python 3.9+ can run this script."""
    import urllib.error
    import urllib.parse
    import urllib.request
    url = URL + "?" + urllib.parse.urlencode({"output_format": output_format})
    data = json.dumps(job["body"]).encode("utf-8")
    for attempt in range(4):
        req = urllib.request.Request(url, data=data, method="POST", headers={
            "xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 3:
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


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Character and creature SFX from ElevenLabs (dry run by default)")
    ap.add_argument("groups", nargs="*", help="groups to make (default: all), e.g. wolf bear footsteps")
    ap.add_argument("--sound", help="only this sound, e.g. howl")
    ap.add_argument("--redo", action="store_true", help="make them again even if the files exist")
    ap.add_argument("--send", action="store_true", help="actually call ElevenLabs (spends credits)")
    ap.add_argument("--list", action="store_true", help="also print every full prompt")
    args = ap.parse_args(argv)

    spec = load_spec()
    manifest = load_manifest()
    all_jobs = jobs(spec, args.groups, args.sound)
    js = todo(all_jobs, manifest, args.redo)

    print(f"\n  {len(js)} of {len(all_jobs)} files to make ({len(all_jobs) - len(js)} already done)\n")
    shown = set()
    for j in js:
        key = (j["group"], j["sound"])
        if key in shown:
            continue
        shown.add(key)
        takes = sum(1 for k in js if (k["group"], k["sound"]) == key)
        loop = "  loop" if j["body"].get("loop") else ""
        print(f"  {j['group']:<11} {j['sound']:<14} {takes} x {j['seconds']:.1f} s{loop}"
              f"   {round(takes * j['seconds'] * CREDITS_PER_SECOND):>4} credits")
        if args.list:
            print(f"      {j['body']['text']}")
    total = cost(js)
    print(f"\n  Total: {sum(j['seconds'] for j in js):.1f} s of audio = {total} credits "
          f"({CREDITS_PER_SECOND} per second)")

    if not js:
        return
    if not args.send:
        print("\n  Dry run: nothing was sent. Add --send to generate.")
        return
    typed = input(f"\nThis spends {total} ElevenLabs credits. Type {total} to go on: ").strip()
    if typed != str(total):
        sys.exit("Cancelled.")

    key = api_key()
    fmt = spec.get("output_format", "mp3_44100_128")
    failed = 0
    for i, j in enumerate(js, 1):
        path = OUT / j["file"]
        try:
            audio = generate(j, key, fmt)
        except Exception as e:  # keep going; report at the end
            failed += 1
            print(f"  [{i}/{len(js)}] {j['file']}  FAILED: {e}")
            if any(s in str(e) for s in ("HTTP 401", "HTTP 403", "quota", "network error")):
                print("  Stopping: the rest would fail the same way.")
                break
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(audio)
        manifest[j["file"]] = {"hash": j["hash"], "prompt": j["body"]["text"], "seconds": j["seconds"],
                               "made": time.strftime("%Y-%m-%dT%H:%M:%S")}
        save_manifest(manifest)
        print(f"  [{i}/{len(js)}] {j['file']}  {len(audio) // 1024} KB")
    print(f"\n  Done: {len(js) - failed} made, {failed} failed. Files are in {OUT.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
