"""Meshy batch generation (ART-01): text-to-3D previews for tracker entries.

Dry run is the default. It sends nothing and prints the list, the prompts and the
credit estimate. Sending needs --send, and it also asks you to type the credit total.

    python tools/meshy/batch.py preview --set brackenvale-town
    python tools/meshy/batch.py preview VIL-01 CLT-01 --variants 1
    python tools/meshy/batch.py preview --set brackenvale-town --send
    python tools/meshy/batch.py status
    python tools/meshy/batch.py animate HER-09 --variant 1          # texture -> rig -> animations

Characters (hero and enemies) take their prompts from characters.json.

Prompts come from OBJECTS.md (and the other tracker files) plus the shared style line.
Only IDs marked approved in ideas_status.json are sent. Results go to
assets/meshy/previews/<ID>/v<N>/ (git-ignored), and every task is recorded in
assets/meshy/tasks.json so later refines can reuse the preview task IDs.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILES = ("OBJECTS.md", "ENEMIES.md", "ARMOR.md", "WEAPONS.md")
STATUS_JSON = ROOT / "ideas_status.json"
SETS_JSON = Path(__file__).with_name("sets.json")
CHARACTERS_JSON = Path(__file__).with_name("characters.json")
OUT_DIR = ROOT / "assets" / "meshy" / "previews"
TASKS_JSON = ROOT / "assets" / "meshy" / "tasks.json"

API = "https://api.meshy.ai/openapi/v2/text-to-3d"
STYLE = ("stylized dark-fantasy, hand-painted textures, chunky readable silhouette, "
         "muted earthy palette, game-ready low-poly, single object, centered, "
         "no ground plane, no background")
PROMPT_LIMIT = 800
# Preview credits per task by ai_model (docs.meshy.ai/en/api/pricing, checked 2026-11-24)
PREVIEW_CREDITS = {"latest": 20, "meshy-7.1": 20, "meshy-6": 20,
                   "meshy-6-lite": 5, "meshy-t2": 5, "meshy-t2.5": 5}

ENTRY = re.compile(r"^- \[(?P<id>[A-Z]{3}-\d{2})\] \*\*(?P<name>.+?)\*\*(?P<rest>.*)$")
# "Prompt: ..." is the main object; "Gate prompt: ..." etc. are extra parts generated alongside it
PROMPT = re.compile(r'(?:\b(?P<part>[A-Z][a-z]+) )?[Pp]rompt: "(?P<p>[^"]+)"')
PREVIEW_MIN_TRIS = 750      # previews are kept a bit denser than the final budget so they read well
VARIANTS = re.compile(r"·\s*(\d+)\s+variants?")
TRIS = re.compile(r"·\s*([\d.]+)\s*(k?)\s+tris")


@dataclass
class Entry:
    id: str
    name: str
    prompts: dict[str, str]     # part name ("" = main object) -> prompt
    variants: int
    tris: int | None
    file: str
    pose: str | None = None             # characters: "a-pose" / "t-pose"
    rig: str | None = None              # characters: "biped" / "quadruped"
    height: float | None = None         # rig height in meters
    actions: dict[int, str] | None = None   # animation library ID -> what it's for

    def full_prompt(self, part: str = "") -> str:
        return f"{self.prompts[part].rstrip('. ')}, {STYLE}"


def job_key(e: Entry, part: str, v: int) -> str:
    return f"{e.id}/{part}/v{v}" if part else f"{e.id}/v{v}"


def parse_entries() -> dict[str, Entry]:
    entries: dict[str, Entry] = {}
    for fname in SOURCE_FILES:
        path = ROOT / fname
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            m = ENTRY.match(line)
            if not m:
                continue
            prompts = {(p["part"] or "").lower(): p["p"] for p in PROMPT.finditer(line)}
            if "" not in prompts:
                continue
            v = VARIANTS.search(line)
            t = TRIS.search(line)
            tris = None
            if t:
                tris = int(float(t.group(1)) * (1000 if t.group(2) else 1))
            entries[m["id"]] = Entry(m["id"], m["name"], prompts, int(v.group(1)) if v else 1,
                                     tris, fname)
    if CHARACTERS_JSON.exists():
        chars = json.loads(CHARACTERS_JSON.read_text(encoding="utf-8"))["characters"]
        for cid, c in chars.items():
            entries[cid] = Entry(cid, c["name"], {"": c["prompt"]}, int(c.get("variants", 1)),
                                 c.get("tris"), CHARACTERS_JSON.name, c.get("pose"), c.get("rig"),
                                 c.get("height_m"), {int(k): v for k, v in c.get("actions", {}).items()})
    return entries


def statuses() -> dict[str, str]:
    data = json.loads(STATUS_JSON.read_text(encoding="utf-8"))
    return {k: v.get("status", "awaiting") for k, v in data.get("ideas", {}).items()}


def load_tasks() -> dict:
    if TASKS_JSON.exists():
        return json.loads(TASKS_JSON.read_text(encoding="utf-8"))
    return {"previews": {}}


def save_tasks(tasks: dict) -> None:
    TASKS_JSON.parent.mkdir(parents=True, exist_ok=True)
    TASKS_JSON.write_text(json.dumps(tasks, indent=2), encoding="utf-8")


def api_key() -> str:
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    key = os.environ.get("MESHY_API_KEY", "")
    if not key:
        sys.exit("MESHY_API_KEY is not set (put it in .env).")
    return key


def plan(args) -> list[tuple[Entry, str, int]]:
    """Pick (entry, part, variant number) jobs to generate, skipping ones already done.

    One variant per part unless --variants or --all-variants asks for more. Named parts
    (such as the fence's gate) count toward the entry's variant total.
    """
    entries = parse_entries()
    status = statuses()
    ids: list[str] = list(args.ids)
    if args.set:
        sets = json.loads(SETS_JSON.read_text(encoding="utf-8"))
        if args.set not in sets:
            sys.exit(f"No set named {args.set!r}. Known: {', '.join(k for k in sets if not k.startswith('_'))}")
        ids += sets[args.set]
    if not ids:
        sys.exit("Name some IDs or a --set.")
    done = load_tasks()["previews"]
    jobs: list[tuple[Entry, str, int]] = []
    problems: list[str] = []
    for i in dict.fromkeys(ids):
        e = entries.get(i)
        if e is None:
            problems.append(f"{i}: no entry with a Prompt in {', '.join(SOURCE_FILES)}")
            continue
        if status.get(i) != "approved" and not args.allow_unapproved:
            problems.append(f"{i}: status is {status.get(i, 'awaiting')}, not approved (skipped)")
            continue
        long = [p for p in e.prompts if len(e.full_prompt(p)) > PROMPT_LIMIT]
        if long:
            problems.append(f"{i}: prompt over Meshy's {PROMPT_LIMIT} chars ({', '.join(p or 'main' for p in long)})")
            continue
        for part in e.prompts:
            if args.variants:
                count = args.variants
            elif args.all_variants:
                count = 1 if part else max(1, e.variants - (len(e.prompts) - 1))
            else:
                count = 1
            for v in range(1, count + 1):
                rec = done.get(job_key(e, part, v))
                if rec and rec.get("status") == "SUCCEEDED" and not args.reroll:
                    continue
                jobs.append((e, part, v))
    for p in problems:
        print("  ! " + p)
    return jobs


def print_plan(jobs, model: str) -> int:
    per = PREVIEW_CREDITS[model]
    print(f"\nMeshy text-to-3D PREVIEW (mesh only, no texture) · ai_model={model} · {per} credits each\n")
    print(f"  {'ID':<8}{'Name':<28}{'Previews':>9}{'Tris':>7}  Credits")
    by_id: dict[tuple[str, str], list] = {}
    for e, part, v in jobs:
        by_id.setdefault((e.id, part), []).append(v)
    entries = {e.id: e for e, _, _ in jobs}
    for (i, part), vs in by_id.items():
        e = entries[i]
        name = f"{e.name} ({part})" if part else e.name
        print(f"  {i:<8}{name[:27]:<28}{len(vs):>9}{polycount(e):>7}  {per * len(vs):>5}")
    total = per * len(jobs)
    print(f"\n  {len(entries)} objects · {len(jobs)} previews · {total} credits")
    print(f"  With ~30% re-rolls: about {round(total * 1.3 / 10) * 10} credits")
    return total


def polycount(e: Entry) -> int:
    return max(PREVIEW_MIN_TRIS, min(e.tris or PREVIEW_MIN_TRIS, 300000))


def request_body(e: Entry, part: str, model: str, full_detail: bool = False) -> dict:
    body = {"mode": "preview", "prompt": e.full_prompt(part), "ai_model": model,
            "target_formats": ["glb"]}
    if model.startswith("meshy-t"):
        # Smart Topology models build a clean low-poly mesh directly (t2: up to 15k, t2.5: 30k)
        body["model_type"] = "smart-topology"
        body["target_polycount"] = min(polycount(e), 15000 if model == "meshy-t2" else 30000)
    elif full_detail:   # keep Meshy's full mesh; we reduce it ourselves later
        body["should_remesh"] = False
    else:
        body.update(should_remesh=True, topology="triangle", target_polycount=polycount(e))
    if e.pose:
        body["pose_mode"] = e.pose
    return body


def send(jobs, model: str, total: int, full_detail: bool = False) -> None:
    import requests

    typed = input(f"\nThis spends {total} Meshy credits. Type {total} to go on: ").strip()
    if typed != str(total):
        sys.exit("Cancelled. Nothing was sent.")
    headers = {"Authorization": f"Bearer {api_key()}"}
    tasks = load_tasks()

    pending: dict[str, str] = {}
    for e, part, v in jobs:
        key = job_key(e, part, v)
        task_id = submit(API, request_body(e, part, model, full_detail), headers)
        pending[key] = task_id
        if key in tasks["previews"]:     # a re-roll: keep the old task so its credits still count
            tasks.setdefault("replaced", []).append({"key": key, **tasks["previews"][key]})
        tasks["previews"][key] = {"task_id": task_id, "status": "PENDING", "model": model,
                                  "prompt": e.full_prompt(part), "created": time.time()}
        save_tasks(tasks)
        print(f"  sent {key} -> {task_id}")

    while pending:
        time.sleep(10)
        for key, task_id in list(pending.items()):
            r = requests.get(f"{API}/{task_id}", headers=headers, timeout=60)
            if r.status_code == 429:
                break
            if r.status_code >= 300:
                continue
            t = r.json()
            rec = tasks["previews"][key]
            rec["status"] = t["status"]
            if t["status"] in ("SUCCEEDED", "FAILED", "CANCELED"):
                del pending[key]
                rec["credits"] = t.get("consumed_credits")
                if t["status"] == "SUCCEEDED":
                    download(key, t)
                    print(f"  done {key}")
                else:
                    rec["error"] = (t.get("task_error") or {}).get("message")
                    print(f"  ! {key} {t['status']}: {rec['error']}")
            save_tasks(tasks)
        if pending:
            print(f"  ... {len(pending)} still running")
    print(f"\nFinished. Credits recorded across all previews so far: {credits_spent(tasks)}")


def credits_spent(tasks: dict) -> int:
    records = list(tasks["previews"].values()) + tasks.get("replaced", [])
    for kind in ("refines", "rigs", "animations", "motions"):
        records += list(tasks.get(kind, {}).values())
    records += tasks.get("replaced_motions", [])
    return sum(r.get("credits") or 0 for r in records)


def save_url(url: str, path: Path, label: str = "") -> None:
    """Stream a download to disk (full-detail meshes can be ~180 MB)."""
    import requests

    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(5):
        try:
            with requests.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                size = int(r.headers.get("content-length", 0))
                got, last = 0, 0
                tmp = path.with_name(path.name + ".part")
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
                        got += len(chunk)
                        if size > 20_000_000 and got - last >= 20_000_000:
                            print(f"    {label} {path.name}: {got // 1_000_000}/{size // 1_000_000} MB")
                            last = got
                tmp.replace(path)
                return
        except requests.RequestException as exc:
            print(f"    download of {path.name} failed ({type(exc).__name__}), retrying ({attempt + 1}/5)")
            time.sleep(5 * (attempt + 1))
    print(f"  ! couldn't download {path.name}. The task itself succeeded and its ID is in "
          f"assets/meshy/tasks.json, so the file can still be fetched from Meshy.")


def download(key: str, task: dict) -> None:
    folder = OUT_DIR / key.replace("/", os.sep)
    for name, url in (("model.glb", task.get("model_urls", {}).get("glb")),
                      ("thumb.png", task.get("thumbnail_url"))):
        if url:
            save_url(url, folder / name, key)
    (folder / "task.json").write_text(json.dumps(task, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------- #
# Characters: texture (refine) -> rig -> animations

RIG_API = "https://api.meshy.ai/openapi/v1/rigging"
ANIM_API = "https://api.meshy.ai/openapi/v1/animations"
MOTION_API = "https://api.meshy.ai/openapi/v1/text-to-motion"
REFINE_CREDITS, RIG_CREDITS, ACTION_CREDITS = 10, 5, 3
MOTION_CREDITS = {"prime": 10, "swift": 3}


def safe_name(text: str) -> str:
    words = re.sub(r"[^a-z0-9]+", " ", text.lower()).split()
    return "_".join(words[:5]) or "motion"


def find_recent_task(url: str, headers: dict, since_ms: float, body: dict) -> str | None:
    """After a dropped connection: did Meshy create the task anyway? (Its list endpoints are free.)"""
    import requests

    try:
        r = requests.get(url, headers=headers, params={"page_size": 10, "sort_by": "-created_at"}, timeout=30)
        items = r.json() if r.ok else []
    except requests.RequestException:
        return None
    for t in items if isinstance(items, list) else []:
        if t.get("created_at", 0) < since_ms:
            continue
        if "prompt" in body and t.get("prompt") not in (None, body["prompt"]):
            continue
        return t.get("id")
    return None


def submit(url: str, body: dict, headers: dict) -> str:
    """POST a task, retrying on rate limits and dropped connections without creating duplicates."""
    import requests

    sent_at = time.time() * 1000 - 15_000          # allow for clock skew
    for attempt in range(8):
        try:
            r = requests.post(url, json=body, headers=headers, timeout=60)
        except requests.ConnectionError as exc:
            time.sleep(5 * (attempt + 1))
            existing = find_recent_task(url, headers, sent_at, body)
            if existing:
                print(f"    connection dropped, but Meshy created the task ({existing}); continuing")
                return existing
            print(f"    connection problem ({type(exc).__name__}), retrying ({attempt + 1}/8)")
            continue
        if r.status_code == 429:
            time.sleep(5 * (attempt + 1))
            continue
        break
    else:
        sys.exit(f"  ! couldn't reach {url} after 8 tries. Nothing more was sent; run the command again later.")
    if r.status_code >= 300:
        sys.exit(f"  ! HTTP {r.status_code} from {url}: {r.text[:300]}")
    return r.json()["result"]


def wait(url: str, task_id: str, headers: dict, label: str) -> dict:
    import requests

    last = -1
    while True:
        time.sleep(10)
        try:
            r = requests.get(f"{url}/{task_id}", headers=headers, timeout=60)
        except requests.RequestException:
            print(f"    {label}: connection problem while checking, will retry")
            continue
        if r.status_code >= 300:
            continue
        t = r.json()
        if t["status"] in ("SUCCEEDED", "FAILED", "CANCELED"):
            return t
        if t.get("progress", 0) != last:
            last = t.get("progress", 0)
            print(f"    {label}: {t['status'].lower()} {last}%")


def cmd_animate(args) -> None:
    entries = parse_entries()
    e = entries.get(args.id)
    if e is None or not e.rig:
        sys.exit(f"{args.id} has no character entry with a rig type in {CHARACTERS_JSON.name}.")
    if statuses().get(args.id) != "approved":
        sys.exit(f"{args.id} isn't approved in the tracker.")
    key = f"{args.id}/v{args.variant}"
    tasks = load_tasks()
    prev = tasks["previews"].get(key)
    if not prev or prev.get("status") != "SUCCEEDED":
        sys.exit(f"No finished preview {key}. Make the preview first (batch.py preview {args.id}).")
    refines, rigs, anims = (tasks.setdefault(k, {}) for k in ("refines", "rigs", "animations"))
    mine = {k: v for k, v in anims.items() if k == key or k.startswith(key + "#")}
    done_anim = {a for v in mine.values() if v.get("status") == "SUCCEEDED" for a in v.get("actions", [])}
    if args.motion:
        if e.rig != "biped":
            sys.exit("Text to Motion only works on biped rigs.")
        if len(args.motion) > 400:
            sys.exit(f"Motion prompt is {len(args.motion)} characters; Meshy allows 400.")
        if not (2 <= args.duration <= 10 and (args.duration * 2) == int(args.duration * 2)):
            sys.exit("--duration must be 2 to 10 seconds in steps of 0.5.")
        todo = []
    else:
        actions = ([int(a) for a in args.actions.split(",")] if args.actions
                   else list((e.actions or {}).keys()))
        todo = [a for a in actions if a not in done_anim]

    steps = []
    if refines.get(key, {}).get("status") != "SUCCEEDED":
        steps.append(("texture (refine, 2K)", REFINE_CREDITS))
    if rigs.get(key, {}).get("status") != "SUCCEEDED":
        steps.append((f"rig ({e.rig}{f', {e.height} m' if e.height else ''}; includes walk + run clips)", RIG_CREDITS))
    for i in range(0, len(todo), 10):
        chunk = todo[i:i + 10]
        steps.append((f"{len(chunk)} animations", ACTION_CREDITS * len(chunk)))
    if args.motion:
        steps.append((f"text to motion ({args.motion_mode}, {args.duration:g} s)", MOTION_CREDITS[args.motion_mode]))
        steps.append(("apply the motion to the rig (price not listed; assumed 3)", ACTION_CREDITS))
    total = sum(c for _, c in steps)

    print(f"\nMeshy character pipeline for {e.name} ({key})\n")
    for name, c in steps:
        print(f"  {name:<58}{c:>4} credits")
    if args.motion:
        print(f"\n  Motion prompt: {args.motion}\n  Saved as: rig/motion_{safe_name(args.name or args.motion)}.glb")
    if todo:
        print("\n  Animations:")
        for a in todo:
            print(f"    {a:>5}  {(e.actions or {}).get(a, '')}")
    print(f"\n  Total: {total} credits")
    if not steps:
        print("  Everything is already done.")
        return
    if not args.send:
        print("\n  Dry run: nothing was sent. Add --send to run it.")
        return
    typed = input(f"\nThis spends {total} Meshy credits. Type {total} to go on: ").strip()
    if typed != str(total):
        sys.exit("Cancelled. Nothing was sent.")

    headers = {"Authorization": f"Bearer {api_key()}"}
    folder = OUT_DIR / key.replace("/", os.sep)

    if refines.get(key, {}).get("status") != "SUCCEEDED":
        tid = submit(API, {"mode": "refine", "preview_task_id": prev["task_id"], "enable_pbr": False}, headers)
        refines[key] = {"task_id": tid, "status": "PENDING", "created": time.time()}
        save_tasks(tasks)
        t = wait(API, tid, headers, "texture")
        refines[key].update(status=t["status"], credits=t.get("consumed_credits"))
        save_tasks(tasks)
        if t["status"] != "SUCCEEDED":
            sys.exit(f"  ! texture {t['status']}: {(t.get('task_error') or {}).get('message')}")
        if t.get("model_urls", {}).get("glb"):
            save_url(t["model_urls"]["glb"], folder / "textured" / "model.glb", key)
        if t.get("thumbnail_url"):
            save_url(t["thumbnail_url"], folder / "textured" / "thumb.png", key)
        print("  textured")

    if rigs.get(key, {}).get("status") != "SUCCEEDED":
        body = {"input_task_id": refines[key]["task_id"], "animation_type": e.rig}
        if e.height:
            body["height_meters"] = e.height
        tid = submit(RIG_API, body, headers)
        rigs[key] = {"task_id": tid, "status": "PENDING", "created": time.time()}
        save_tasks(tasks)
        t = wait(RIG_API, tid, headers, "rig")
        rigs[key].update(status=t["status"], credits=t.get("consumed_credits"))
        save_tasks(tasks)
        if t["status"] != "SUCCEEDED":
            sys.exit(f"  ! rig {t['status']}: {(t.get('task_error') or {}).get('message')}")
        res = t.get("result") or {}
        if res.get("rigged_character_glb_url"):
            save_url(res["rigged_character_glb_url"], folder / "rig" / "rigged.glb", key)
        for clip, url in ((res.get("basic_animations") or {}).items()):
            if url and clip.endswith("_glb_url") and "armature" not in clip:
                save_url(url, folder / "rig" / (clip.replace("_glb_url", "") + ".glb"), key)
        print("  rigged")

    def new_anim_key() -> str:
        n = 0
        while (key if n == 0 else f"{key}#{n}") in anims:
            n += 1
        return key if n == 0 else f"{key}#{n}"

    def next_file(stem: str) -> Path:
        n = 1
        while (folder / "rig" / f"{stem}_{n}.glb").exists():
            n += 1
        return folder / "rig" / f"{stem}_{n}.glb"

    for i in range(0, len(todo), 10):
        chunk = todo[i:i + 10]
        tid = submit(ANIM_API, {"rig_task_id": rigs[key]["task_id"], "action_ids": chunk}, headers)
        akey = new_anim_key()
        anims[akey] = {"task_id": tid, "status": "PENDING", "actions": chunk, "created": time.time()}
        save_tasks(tasks)
        t = wait(ANIM_API, tid, headers, "animations")
        anims[akey].update(status=t["status"], credits=t.get("consumed_credits"))
        save_tasks(tasks)
        if t["status"] != "SUCCEEDED":
            sys.exit(f"  ! animations {t['status']}: {(t.get('task_error') or {}).get('message')}")
        url = (t.get("result") or {}).get("animation_glb_url")
        if url:
            save_url(url, next_file("animations"), key)
        print(f"  animated ({len(chunk)} clips)")

    if args.motion:
        motions = tasks.setdefault("motions", {})
        mkey = f"{key}:{safe_name(args.name or args.motion)}"
        prior = motions.get(mkey)
        fresh = prior and prior.get("status") == "SUCCEEDED" and prior.get("prompt") == args.motion \
            and time.time() - prior.get("created", 0) < 2.5 * 86400       # Meshy keeps clips 3 days
        if fresh:
            tid = prior["task_id"]
            print("  reusing the motion generated last time (not charged again)")
        else:
            tid = submit(MOTION_API, {"prompt": args.motion, "mode": args.motion_mode,
                                      "duration": args.duration}, headers)
            if prior:
                tasks.setdefault("replaced_motions", []).append(prior)
            motions[mkey] = {"task_id": tid, "status": "PENDING", "prompt": args.motion, "created": time.time()}
            save_tasks(tasks)
            t = wait(MOTION_API, tid, headers, "motion")
            motions[mkey].update(status=t["status"], credits=t.get("consumed_credits"))
            save_tasks(tasks)
            if t["status"] != "SUCCEEDED":
                sys.exit(f"  ! motion {t['status']}: {(t.get('task_error') or {}).get('message')}")
        tid = submit(ANIM_API, {"rig_task_id": rigs[key]["task_id"], "motion_task_id": tid}, headers)
        akey = new_anim_key()
        anims[akey] = {"task_id": tid, "status": "PENDING", "motion": mkey, "created": time.time()}
        save_tasks(tasks)
        t = wait(ANIM_API, tid, headers, "apply motion")
        anims[akey].update(status=t["status"], credits=t.get("consumed_credits"))
        save_tasks(tasks)
        if t["status"] != "SUCCEEDED":
            sys.exit(f"  ! apply motion {t['status']}: {(t.get('task_error') or {}).get('message')}")
        url = (t.get("result") or {}).get("animation_glb_url")
        if url:
            save_url(url, folder / "rig" / f"motion_{safe_name(args.name or args.motion)}.glb", key)
        print(f"  motion applied (cost recorded: {t.get('consumed_credits')} credits)")
    print(f"\nFinished. Files are in {folder.relative_to(ROOT)}. Credits recorded so far: {credits_spent(tasks)}")


def cmd_status(_args) -> None:
    data = load_tasks()
    tasks = data["previews"]
    if not tasks:
        print("No previews recorded yet.")
        return
    for key, rec in sorted(tasks.items()):
        print(f"  {key:<16}{rec['status']:<12}{rec.get('credits') or '':>4}  {rec['task_id']}")
    for rec in data.get("replaced", []):
        print(f"  {rec['key']:<16}{'replaced':<12}{rec.get('credits') or '':>4}  {rec['task_id']}")
    print(f"\n  Credits spent on previews: {credits_spent(data)}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Meshy batch generation (previews)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preview", help="plan (default) or send preview tasks")
    p.add_argument("ids", nargs="*", help="IDs such as VIL-01")
    p.add_argument("--set", help="named batch from tools/meshy/sets.json")
    p.add_argument("--model", default="latest", choices=sorted(PREVIEW_CREDITS))
    p.add_argument("--variants", type=int, help="variants per object (default 1)")
    p.add_argument("--all-variants", action="store_true",
                   help="use the variant counts written in the .md files")
    p.add_argument("--reroll", action="store_true", help="redo variants that already succeeded")
    p.add_argument("--full-detail", action="store_true",
                   help="skip Meshy's triangle reduction and keep the full mesh (same price)")
    p.add_argument("--allow-unapproved", action="store_true")
    p.add_argument("--show-prompts", action="store_true")
    p.add_argument("--send", action="store_true", help="actually call Meshy (spends credits)")
    sub.add_parser("status", help="list recorded preview tasks")
    a = sub.add_parser("animate", help="texture, rig and animate a character's chosen preview")
    a.add_argument("id", help="character ID from characters.json, such as HER-09")
    a.add_argument("--variant", type=int, default=1, help="which preview to use (v1, v2, ...)")
    a.add_argument("--actions", help="comma-separated animation library IDs (default: from characters.json)")
    a.add_argument("--motion", help="describe a custom move for Text to Motion instead of library actions")
    a.add_argument("--name", help="short name for the motion clip's file (default: from the prompt)")
    a.add_argument("--duration", type=float, default=3.0, help="motion length, 2-10 s in 0.5 steps")
    a.add_argument("--motion-mode", default="prime", choices=sorted(MOTION_CREDITS))
    a.add_argument("--send", action="store_true", help="actually call Meshy (spends credits)")
    args = ap.parse_args()

    if args.cmd == "status":
        cmd_status(args)
        return
    if args.cmd == "animate":
        cmd_animate(args)
        return
    jobs = plan(args)
    if not jobs:
        print("Nothing to generate.")
        return
    total = print_plan(jobs, args.model)
    if args.show_prompts:
        print()
        shown = {(e.id, part): e for e, part, _ in jobs}
        for (i, part), e in shown.items():
            print(f"  {i}{'/' + part if part else ''}: {e.full_prompt(part)}")
    if args.send:
        send(jobs, args.model, total, args.full_detail)
    else:
        print("\n  Dry run: nothing was sent. Add --send to generate.")


if __name__ == "__main__":
    main()
