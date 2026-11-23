"""Check the dialogue sources before compiling.

    python tools/dialogue/validate.py                  # both stories
    python tools/dialogue/validate.py --story v2
    python tools/dialogue/validate.py --vanilla        # also flag words that would link to vanilla topics
    python tools/dialogue/validate.py --check-locked   # locked lines must match the last commit

Errors stop compile.py. Warnings are things a person should look at.

Errors:   broken YAML or conditions, more than 6 filters, duplicate keys, responses
          over 512 characters, racism-filter matches, Tamriel names, undefined
          tdl_ globals, malformed greeting topics, edited locked lines.
Warnings: unreachable responses (shadowed by an earlier, broader one), topics the
          player can never learn, unknown speakers/factions/journal stages,
          long responses, modern phrasing, unknown %variables, vanilla topic
          names in the text (they would become clickable links).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from dlg import (REPO, Line, SourceError, build_conditions, find_tes3conv, group_topics,
                 load_config, load_sources, rel, repo_path, select_story, topic_regex)

TEXT_VARS = {"%name", "%pcname", "%race", "%pcrace", "%class", "%pcclass", "%faction", "%rank",
             "%pcrank", "%nextpcrank", "%cell", "%pccrimelevel", "%crimegolddiscount",
             "%crimegoldturnin"}
ADDTOPIC = re.compile(r'addtopic\s+"?([^"\r\n]+?)"?\s*$', re.I | re.M)
JOURNAL_CMD = re.compile(r'(?:journal|setjournalindex)\s+"?(\w+)"?\s*,?\s*(\d+)', re.I)
SET_GLOBAL = re.compile(r'\bset\s+(\w+)\s+to\b', re.I)


class Report:
    def __init__(self):
        self.errors: dict[str, None] = {}
        self.warnings: dict[str, None] = {}

    def err(self, where: str, msg: str):
        self.errors[f"{where}: {msg}"] = None

    def warn(self, where: str, msg: str):
        self.warnings[f"{where}: {msg}"] = None


def where(ln: Line) -> str:
    return f"{rel(ln.file)} [{ln.topic} / {ln.key}]"


def blocklist():
    """The racism filters from tools/story/config.yaml (slurs + ethnic descriptors)."""
    sys.path.insert(0, str(REPO / "tools" / "story"))
    try:
        from common import compile_blocklist, load_config as story_cfg
        return compile_blocklist(story_cfg())
    except Exception as e:  # noqa: BLE001
        print(f"note: racism filter unavailable ({e})")
        return None
    finally:
        sys.path.pop(0)


def word_regex(words) -> re.Pattern | None:
    words = [w for w in words if w]
    return re.compile(r"\b(" + "|".join(re.escape(w) for w in words) + r")\b", re.I) if words else None


# ------------------------------------------------------------- shadowing

def _atoms(ln: Line):
    speaker, data, filters = build_conditions(ln.when)
    fields = {k: v.lower() for k, v in speaker.items() if v}
    fl = {(f["filter_type"], f["function"], f["comparison"], f["id"].lower(), f["value"]["data"])
          for f in filters}
    return fields, data, fl


def shadows(a: Line, b: Line) -> bool:
    """True if `a` matches every time `b` would, so `b` (later in the list) is never said."""
    fa, da, la = _atoms(a)
    fb, db, lb = _atoms(b)
    for k, v in fa.items():
        if k == "speaker_cell":
            if not fb.get(k, "").startswith(v):
                return False
        elif fb.get(k) != v:
            return False
    if da["disposition"] > db["disposition"]:
        return False
    for k, default in (("speaker_rank", -1), ("player_rank", -1), ("speaker_sex", "Any")):
        if da[k] != default and da[k] != db[k]:
            return False
    return la <= lb


# ------------------------------------------------------------- vanilla topics

def vanilla_topics(cfg: dict) -> set[str]:
    cache = repo_path(cfg["out_dir"]) / "vanilla_topics.txt"
    if cache.exists():
        return set(cache.read_text(encoding="utf-8").splitlines())
    data = cfg["plugin"].get("data_files")
    tes3conv = find_tes3conv(cfg)
    if not data or not tes3conv:
        print("note: --vanilla needs plugin.data_files and tes3conv in config.yaml; skipped.")
        return set()
    names = set()
    for esm in ("Morrowind.esm", "Tribunal.esm", "Bloodmoon.esm"):
        p = Path(data) / esm
        if not p.exists():
            continue
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "x.json"
            subprocess.run([tes3conv, "-c", str(p), str(out)], check=True, capture_output=True)
            for r in json.loads(out.read_text(encoding="utf-8")):
                if r["type"] == "Dialogue" and r["dialogue_type"] == "Topic":
                    names.add(r["id"])
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text("\n".join(sorted(names)), encoding="utf-8")
    return names


# ------------------------------------------------------------- locked lines

def verify_locked(cfg: dict, rep: Report):
    root = repo_path(cfg["source_dir"])
    for p in sorted(root.rglob("*.yaml")):
        r = subprocess.run(["git", "show", f"HEAD:./{p.name}"], cwd=p.parent, capture_output=True,
                           text=True, encoding="utf-8")
        if r.returncode:
            continue  # not committed yet
        old = yaml.safe_load(r.stdout) or {}
        new = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        items = lambda d: {str(x.get("key", x.get("index"))): x for x in (d.get("lines") or d.get("entries") or [])}
        o, n = items(old), items(new)
        for k, x in o.items():
            if not x.get("locked"):
                continue
            same = k in n and all(n[k].get(f) == x.get(f) for f in ("text", "when", "result", "story"))
            if not same:
                rep.err(f"{rel(p)} [{k}]", "locked line was changed or removed since the last commit "
                                           "(unlock it deliberately, or restore it)")


# ------------------------------------------------------------- main checks

def run(cfg: dict, story: str | None, vanilla: bool = False, locked: bool = False,
        quiet: bool = False) -> int:
    """Print the report; return the number of errors."""
    rep = Report()
    src = load_sources(cfg)
    for e in src.errors:
        rep.err("load", e)
    c = cfg["checks"]
    block = blocklist()
    forbidden = word_regex(c.get("forbidden_words", []))
    modern = word_regex(c.get("modern_words", []))
    globals_ = {k.lower(): v for k, v in (src.states.get("globals") or {}).items()}
    factions = {f.lower() for f in (src.states.get("factions") or {})}
    known_start = {t.lower() for t in (src.states.get("known_at_start") or [])}

    # Journals defined in the sources: id -> set of indices
    journals: dict[str, set[int]] = {}
    for ln in src.lines:
        if ln.dtype == "Journal":
            journals.setdefault(ln.topic.lower(), set()).add(ln.index)

    ids: dict[str, Line] = {}
    for ln in src.lines:
        w = where(ln)
        if ln.info_id() in ids and ids[ln.info_id()] is not ln:
            other = ids[ln.info_id()]
            if (other.topic.lower(), other.key) == (ln.topic.lower(), ln.key):
                rep.err(w, "duplicate key in this topic")
            else:
                rep.err(w, f"response ID collides with {where(other)}; change one key")
        ids[ln.info_id()] = ln
        if not ln.text.strip():
            rep.err(w, "empty text")
        if len(ln.text) > c["max_chars"]:
            rep.err(w, f"{len(ln.text)} characters; the Construction Set truncates at {c['max_chars']}")
        elif len(ln.text) > c["warn_chars"]:
            rep.warn(w, f"{len(ln.text)} characters; consider splitting into two responses")
        if block and (m := block.search(ln.text)):
            rep.err(w, f"matches the racism filter ({m.group(0)!r})")
        if forbidden and (m := forbidden.search(ln.text + " " + ln.result)):
            rep.err(w, f"Tamriel name {m.group(0)!r} doesn't belong in the Dreamlands")
        if modern and (m := modern.search(ln.text)):
            rep.warn(w, f"modern phrasing {m.group(0)!r}")
        for v in re.findall(r"%\w+", ln.text):
            if v.lower() not in TEXT_VARS and v[1:].lower() not in globals_:
                rep.warn(w, f"unknown text variable {v}")
        if ln.dtype == "Greeting" and not re.fullmatch(r"Greeting [0-9]", ln.topic):
            rep.err(w, "greetings must use topics 'Greeting 0' to 'Greeting 9'")
        if ln.dtype == "Journal":
            continue
        try:
            _, _, filters = build_conditions(ln.when)
        except SourceError as e:
            rep.err(w, str(e))
            continue
        sp = str(ln.when.get("speaker", "")).lower()
        if sp.startswith("tdl_") and sp not in src.characters:
            rep.warn(w, f"speaker {sp} has no character sheet in dialogue/characters/")
        fac = str(ln.when.get("faction", "")).lower()
        if fac and fac not in factions:
            rep.warn(w, f"faction {fac!r} isn't listed in states.yaml")
        for f in filters:
            fid = f["id"].lower()
            if f["filter_type"] == "Global":
                g = globals_.get(fid)
                if g is None:
                    (rep.err if fid.startswith("tdl_") else rep.warn)(
                        w, f"global {f['id']} is not defined in states.yaml")
                elif g.get("values") and f["comparison"] == "Equal" and f["value"]["data"] not in g["values"]:
                    rep.warn(w, f"{f['id']} == {f['value']['data']} isn't one of its documented values")
            if f["filter_type"] == "Journal" and fid.startswith("tdl_"):
                if fid not in journals:
                    rep.warn(w, f"journal {f['id']} has no file in dialogue/journals/ yet")
                elif f["comparison"] == "Equal" and f["value"]["data"] not in journals[fid]:
                    rep.warn(w, f"journal {f['id']} has no stage {f['value']['data']}")
        for jid, idx in JOURNAL_CMD.findall(ln.result):
            if jid.lower().startswith("tdl_") and jid.lower() in journals and int(idx) not in journals[jid.lower()]:
                rep.warn(w, f"result sets {jid} to {idx}, which isn't a defined stage")
        for g in SET_GLOBAL.findall(ln.result):
            if g.lower().startswith("tdl_") and g.lower() not in globals_:
                rep.err(w, f"result sets {g}, which is not defined in states.yaml")

    stories = [story] if story else ["v1", "v2"]
    vt = vanilla_topics(cfg) if vanilla else set()
    for st in stories:
        lines = select_story(src.lines, st)
        groups = group_topics(lines)
        ours = {t.lower() for (_, t) in groups}
        # Shadowed responses
        for (dtype, topic), g in groups.items():
            if dtype == "Journal":
                continue
            for i, b in enumerate(g):
                for a in g[:i]:
                    try:
                        if shadows(a, b):
                            rep.warn(where(b), f"never said in {st}: the earlier response "
                                               f"'{a.key}' always matches first")
                            break
                    except SourceError:
                        break
        # Topics the player can never learn
        mention = topic_regex([t for (d, t) in groups if d == "Topic"])
        learned = set(known_start)
        for ln in lines:
            learned |= {t.strip().lower() for t in ADDTOPIC.findall(ln.result)}
            if mention:
                learned |= {m.lower() for m in mention.findall(ln.text)}
        for (dtype, topic), g in groups.items():
            if dtype == "Topic" and topic.lower() not in learned:
                rep.warn(f"{rel(g[0].file)} [{topic}]", f"no response mentions this topic or adds it "
                                                        f"with AddTopic, and it isn't in known_at_start ({st})")
        # Vanilla topic names that would become links
        if vt:
            rx = topic_regex([t for t in vt if t.lower() not in ours])
            for ln in lines:
                if ln.dtype != "Journal" and (hits := sorted({m.lower() for m in rx.findall(ln.text)})):
                    rep.warn(where(ln), f"vanilla topic(s) {hits} would show as links")

    if locked:
        verify_locked(cfg, rep)

    for e in rep.errors:
        print(f"ERROR   {e}")
    if not quiet:
        for wmsg in rep.warnings:
            print(f"warning {wmsg}")
        drafts = sum(ln.status == "draft" for ln in src.lines)
        print(f"\n{len(src.lines)} responses ({drafts} draft, {len(src.lines) - drafts} reviewed), "
              f"{sum(ln.voice for ln in src.lines)} voiced; "
              f"{len(rep.errors)} errors, {len(rep.warnings)} warnings")
    elif rep.warnings:
        print(f"{len(rep.warnings)} warnings (run validate.py to see them)")
    return len(rep.errors)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--story", choices=["v1", "v2"])
    ap.add_argument("--vanilla", action="store_true", help="flag vanilla topic names in the text")
    ap.add_argument("--check-locked", action="store_true", help="locked lines must match git HEAD")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    n = run(load_config(), args.story, vanilla=args.vanilla, locked=args.check_locked)
    sys.exit(1 if n else 0)


if __name__ == "__main__":
    main()
