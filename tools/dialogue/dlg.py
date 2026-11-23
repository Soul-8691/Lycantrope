"""Shared code for the dialogue tools: load YAML sources, build tes3conv JSON records.

Source layout (repo root):
    dialogue/states.yaml            globals, factions, journals' meaning, topics known at start
    dialogue/bible.md               world facts by story state (for writers and Claude)
    dialogue/conventions.md         style guide
    dialogue/characters/*.yaml      one sheet per named NPC
    dialogue/topics/**/*.yaml       topic / greeting / voice lines   (top-level key `topic:`)
    dialogue/journals/**/*.yaml     quest journals                    (top-level key `journal:`)
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
TOOL = Path(__file__).resolve().parent
CONFIG_PATH = TOOL / "config.yaml"

CMP = {"==": "Equal", "!=": "NotEqual", ">=": "GreaterEqual", "<=": "LessEqual",
       ">": "Greater", "<": "Less"}
DTYPES = {"topic": "Topic", "greeting": "Greeting", "voice": "Voice",
          "persuasion": "Persuasion", "journal": "Journal"}
STORIES = {"v1", "v2", "both"}

# when-keys that become INFO header fields
SPEAKER_FIELDS = {"speaker": "speaker_id", "race": "speaker_race", "class": "speaker_class",
                  "faction": "speaker_faction", "cell": "speaker_cell",
                  "player_faction": "player_faction"}
DATA_FIELDS = {"rank": "speaker_rank", "player_rank": "player_rank",
               "disposition": "disposition", "sex": "speaker_sex"}
# when-keys that become filters: key -> (filter_type, function)
VAR_FILTERS = {"global": ("Global", "VariableCompare"), "local": ("Local", "VariableCompare"),
               "not_local": ("NotLocal", "VariableCompare"), "journal": ("Journal", "JournalType"),
               "dead": ("Dead", "DeadType"), "item": ("Item", "ItemType")}
NOT_FILTERS = {"not_id": ("NotId", "NotIdType"), "not_faction": ("NotFaction", "NotFaction"),
               "not_class": ("NotClass", "NotClass"), "not_race": ("NotRace", "NotRace"),
               "not_cell": ("NotCell", "NotCell")}
WHEN_KEYS = set(SPEAKER_FIELDS) | set(DATA_FIELDS) | set(VAR_FILTERS) | set(NOT_FILTERS) | {"function"}
MAX_FILTERS = 6


class SourceError(Exception):
    pass


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def repo_path(rel: str) -> Path:
    return REPO / rel


def rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(REPO).as_posix()
    except ValueError:
        return str(p)


# ---------------------------------------------------------------- conditions

def parse_cmp(v) -> tuple[str, int | float]:
    """'>= 30' -> ('GreaterEqual', 30); a bare number means '=='."""
    if isinstance(v, bool):
        v = int(v)
    if isinstance(v, (int, float)):
        return "Equal", v
    m = re.fullmatch(r"\s*(==|!=|>=|<=|>|<)\s*(-?\d+(?:\.\d+)?)\s*", str(v))
    if not m:
        raise SourceError(f"bad comparison {v!r}; use e.g. '>= 30' or '== 0'")
    num = float(m.group(2)) if "." in m.group(2) else int(m.group(2))
    return CMP[m.group(1)], num


def camel(name: str) -> str:
    """pc_level -> PcLevel; already-CamelCase names pass through."""
    return name if "_" not in name and name[:1].isupper() else "".join(p.capitalize() for p in name.split("_"))


def value_json(v):
    return {"type": "Float", "data": float(v)} if isinstance(v, float) else {"type": "Integer", "data": int(v)}


def merge_when(base: dict | None, extra: dict | None) -> dict:
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in (base or {}).items()}
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k].update(v)
        else:
            out[k] = v
    return out


def build_conditions(when: dict) -> tuple[dict, dict, list]:
    """Return (speaker fields, data fields, filters) for an INFO record."""
    unknown = set(when) - WHEN_KEYS
    if unknown:
        raise SourceError(f"unknown when-keys {sorted(unknown)}; allowed: {sorted(WHEN_KEYS)}")
    speaker = {f: "" for f in SPEAKER_FIELDS.values()}
    for k, f in SPEAKER_FIELDS.items():
        if k in when:
            speaker[f] = str(when[k])
    data = {"disposition": 0, "speaker_rank": -1, "speaker_sex": "Any", "player_rank": -1}
    if "disposition" in when:
        data["disposition"] = int(when["disposition"])
    for k in ("rank", "player_rank"):
        if k in when:
            data[DATA_FIELDS[k]] = int(when[k])
    if "sex" in when:
        s = str(when["sex"]).capitalize()
        if s not in ("Male", "Female", "Any"):
            raise SourceError(f"sex must be male/female, not {when['sex']!r}")
        data["speaker_sex"] = s

    filters = []
    for k, (ftype, func) in VAR_FILTERS.items():
        for var, c in (when.get(k) or {}).items():
            comp, num = parse_cmp(c)
            filters.append({"filter_type": ftype, "function": func, "comparison": comp,
                            "id": str(var), "value": value_json(num)})
    for k, (ftype, func) in NOT_FILTERS.items():
        ids = when.get(k) or []
        for i in ([ids] if isinstance(ids, str) else ids):
            filters.append({"filter_type": ftype, "function": func, "comparison": "Equal",
                            "id": str(i), "value": value_json(1)})
    for fn, c in (when.get("function") or {}).items():
        comp, num = parse_cmp(c)
        filters.append({"filter_type": "Function", "function": camel(fn), "comparison": comp,
                        "id": "", "value": value_json(num)})
    if len(filters) > MAX_FILTERS:
        raise SourceError(f"{len(filters)} filters; Morrowind allows {MAX_FILTERS} per response")
    for i, f in enumerate(filters):
        f["index"] = i
    filters = [{"index": f["index"], **{k: v for k, v in f.items() if k != "index"}} for f in filters]
    return speaker, data, filters


# ---------------------------------------------------------------- sources

@dataclass
class Line:
    key: str
    topic: str
    dtype: str                      # Topic / Greeting / Voice / Persuasion / Journal
    text: str
    file: Path
    when: dict = field(default_factory=dict)
    result: str = ""
    story: str = "both"
    locked: bool = False
    status: str = "draft"
    voice: bool = False
    sound: str = ""
    quest_state: str | None = None  # journals: Name / Finished / Restart
    index: int = 0                  # journals: entry index
    order: int = 50

    def info_id(self) -> str:
        h = hashlib.sha1(f"{self.topic.lower()}|{self.key}".encode()).hexdigest()
        return str(int(h[:15], 16))


@dataclass
class Sources:
    states: dict
    characters: dict                # id -> sheet
    lines: list[Line]
    errors: list[str]


def _story(v, where):
    s = str(v or "both").lower()
    if s not in STORIES:
        raise SourceError(f"{where}: story must be one of {sorted(STORIES)}, not {v!r}")
    return s


def _load_topic_file(path: Path, doc: dict) -> list[Line]:
    topic = str(doc["topic"])
    dtype = DTYPES.get(str(doc.get("type", "topic")).lower())
    if dtype is None or dtype == "Journal":
        raise SourceError(f"{rel(path)}: type must be topic/greeting/voice/persuasion")
    d = doc.get("defaults") or {}
    out = []
    for i, ln in enumerate(doc.get("lines") or []):
        where = f"{rel(path)} line {i + 1}"
        if "key" not in ln or "text" not in ln:
            raise SourceError(f"{where}: every line needs `key` and `text`")
        out.append(Line(
            key=str(ln["key"]), topic=topic, dtype=dtype, file=path,
            text=" ".join(str(ln["text"]).split()),
            when=merge_when(d.get("when"), ln.get("when")),
            result=str(ln.get("result", d.get("result", "")) or "").strip(),
            story=_story(ln.get("story", d.get("story")), where),
            locked=bool(ln.get("locked", False)),
            status=str(ln.get("status", d.get("status", "draft"))),
            voice=bool(ln.get("voice", d.get("voice", False))),
            sound=str(ln.get("sound", "") or ""),
            order=int(doc.get("order", 50))))
    return out


def _load_journal_file(path: Path, doc: dict) -> list[Line]:
    jid = str(doc["journal"])
    out = []
    if doc.get("name"):
        out.append(Line(key="name", topic=jid, dtype="Journal", text=str(doc["name"]), file=path,
                        quest_state="Name", index=0, locked=bool(doc.get("locked", False))))
    for i, e in enumerate(doc.get("entries") or []):
        where = f"{rel(path)} entry {i + 1}"
        if "index" not in e or "text" not in e:
            raise SourceError(f"{where}: every entry needs `index` and `text`")
        state = "Finished" if e.get("finished") else ("Restart" if e.get("restart") else None)
        out.append(Line(key=str(e.get("key", e["index"])), topic=jid, dtype="Journal",
                        text=" ".join(str(e["text"]).split()), file=path, index=int(e["index"]),
                        quest_state=state, result=str(e.get("result", "") or "").strip(),
                        story=_story(e.get("story", doc.get("story")), where),
                        locked=bool(e.get("locked", False)), status=str(e.get("status", "draft"))))
    return out


def load_sources(cfg: dict, root: Path | None = None) -> Sources:
    root = root or repo_path(cfg["source_dir"])
    errors = []
    states = yaml.safe_load((root / "states.yaml").read_text(encoding="utf-8")) or {}
    characters = {}
    for p in sorted((root / "characters").glob("*.yaml")):
        if p.name.startswith("_"):
            continue
        try:
            sheet = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            characters[str(sheet["id"]).lower()] = sheet
        except Exception as e:  # noqa: BLE001 - report every broken file, keep going
            errors.append(f"{rel(p)}: {e}")
    lines = []
    for sub in ("topics", "journals"):
        for p in sorted((root / sub).rglob("*.yaml")):
            if p.name.startswith("_"):
                continue
            try:
                doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                if "topic" in doc:
                    lines += _load_topic_file(p, doc)
                elif "journal" in doc:
                    lines += _load_journal_file(p, doc)
                else:
                    errors.append(f"{rel(p)}: needs a top-level `topic:` or `journal:` key")
            except SourceError as e:
                errors.append(str(e))
            except Exception as e:  # noqa: BLE001
                errors.append(f"{rel(p)}: {e}")
    return Sources(states, characters, lines, errors)


def select_story(lines: list[Line], story: str) -> list[Line]:
    return [ln for ln in lines if ln.story in ("both", story)]


def group_topics(lines: list[Line]) -> dict[tuple[str, str], list[Line]]:
    """(dtype, topic) -> lines in final order (file order, then line order)."""
    groups: dict[tuple[str, str], list[Line]] = {}
    for ln in sorted(lines, key=lambda x: (x.order, rel(x.file))):  # stable: keeps line order
        groups.setdefault((ln.dtype, ln.topic), []).append(ln)
    for (dtype, _), g in groups.items():
        if dtype == "Journal":
            g.sort(key=lambda x: (x.quest_state != "Name", x.index))
    return groups


# ---------------------------------------------------------------- records

def info_record(ln: Line) -> dict:
    if ln.dtype == "Journal":
        speaker, data, filters = build_conditions({})
        data["disposition"] = ln.index          # the journal index lives in the disposition field
    else:
        speaker, data, filters = build_conditions(ln.when)
    data = {"dialogue_type": ln.dtype, **data}
    rec = {"type": "DialogueInfo", "flags": "", "id": ln.info_id(), "prev_id": "", "next_id": "",
           "data": data, **speaker, "sound_path": ln.sound, "text": ln.text}
    if ln.quest_state:
        rec["quest_state"] = ln.quest_state
    rec["filters"] = filters
    rec["script_text"] = ln.result.replace("\r\n", "\n").replace("\n", "\r\n")
    return rec


def global_records(states: dict) -> list[dict]:
    out = []
    for gid, g in (states.get("globals") or {}).items():
        t = str(g.get("type", "short")).capitalize()
        if t not in ("Short", "Long", "Float"):
            raise SourceError(f"global {gid}: type must be short/long/float")
        v = g.get("value", 0)
        out.append({"type": "GlobalVariable", "flags": "", "id": gid,
                    "value": {"type": t, "data": float(v) if t == "Float" else int(v)}})
    return out


def build_records(cfg: dict, src: Sources, story: str) -> list[dict]:
    recs = []
    if cfg["plugin"].get("emit_globals", True):
        recs += global_records(src.states)
    for (dtype, topic), group in group_topics(select_story(src.lines, story)).items():
        recs.append({"type": "Dialogue", "flags": "", "id": topic, "dialogue_type": dtype})
        infos = [info_record(ln) for ln in group]
        for i, r in enumerate(infos):
            r["prev_id"] = infos[i - 1]["id"] if i else ""
            r["next_id"] = infos[i + 1]["id"] if i + 1 < len(infos) else ""
        recs += infos
    p = cfg["plugin"]
    data_files = Path(os.path.expandvars(p.get("data_files") or "")) if p.get("data_files") else None
    masters = []
    for m in p.get("masters", []):
        f = data_files / m if data_files else None
        masters.append([m, f.stat().st_size if f and f.exists() else 0])
    header = {"type": "Header", "flags": "", "version": 1.3, "file_type": "Esp",
              "author": p.get("author", ""), "description": p.get("description", ""),
              "num_objects": len(recs), "masters": masters}
    return [header] + recs


def find_tes3conv(cfg: dict) -> str | None:
    for c in (os.environ.get("TES3CONV"), cfg.get("tes3conv")):
        if c and Path(os.path.expandvars(c)).exists():
            return str(Path(os.path.expandvars(c)))
    return shutil.which("tes3conv")


# ---------------------------------------------------------------- text helpers

def topic_regex(names) -> re.Pattern | None:
    """Case-insensitive whole-phrase matcher, longest names first (as the game does)."""
    names = sorted({n for n in names if n}, key=len, reverse=True)
    if not names:
        return None
    return re.compile(r"(?<![\w'-])(" + "|".join(re.escape(n) for n in names) + r")(?![\w'-])", re.I)
