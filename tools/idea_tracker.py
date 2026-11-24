#!/usr/bin/env python3
"""
Lycantrope Idea Tracker
=======================

A living checklist for IDEAS.md. Every bullet in IDEAS.md that starts with an ID
in brackets (``- [CMB-04] **Title** — description``) becomes a row you can mark
as Awaiting, Approved or Denied, with an optional note.

* The tracker **watches IDEAS.md**: edit or extend it while the app is open and
  the list updates by itself (new IDs start as "awaiting").
* State lives in **ideas_status.json** (project root). That file is the source
  of truth and is what Claude reads when you refer to "the tracker". If the file
  changes on disk (e.g. Claude updates it), the open app reloads it.
* A human-readable digest is written to **IDEAS_STATUS.md** on every change.

Standard library only (Tkinter). Usage::

    python tools/idea_tracker.py                      # open the GUI
    python tools/idea_tracker.py summary              # counts + decisions, no GUI
    python tools/idea_tracker.py list approved        # IDs with a given status
    python tools/idea_tracker.py set approved CMB-01 CMB-02 [--note "..."]
    python tools/idea_tracker.py set denied "WLF-*"   # wildcards allowed
    python tools/idea_tracker.py note CMB-01 "text"   # set a note

GUI keys (when the list has focus): A approve · D deny · W back to awaiting ·
Space/Enter cycle · Ctrl+Z undo · Ctrl+F search · Ctrl+C copy reference.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IDEAS_MD = ROOT / "IDEAS.md"
OBJECTS_MD = ROOT / "OBJECTS.md"
ENEMIES_MD = ROOT / "ENEMIES.md"
# every file the tracker reads, with the label put in front of its categories
SOURCES = ((IDEAS_MD, ""), (OBJECTS_MD, "Objects · "), (ENEMIES_MD, "Enemies · "))
STATE_JSON = ROOT / "ideas_status.json"
STATUS_MD = ROOT / "IDEAS_STATUS.md"

STATUSES = ("awaiting", "approved", "denied")
LABELS = {"awaiting": "Awaiting", "approved": "Approved", "denied": "Denied"}
ICONS = {"awaiting": "○", "approved": "✔", "denied": "✘"}
ALIASES = {
    "a": "approved", "approve": "approved", "approved": "approved", "yes": "approved", "y": "approved",
    "d": "denied", "deny": "denied", "denied": "denied", "no": "denied", "n": "denied",
    "w": "awaiting", "wait": "awaiting", "awaiting": "awaiting", "pending": "awaiting",
    "reset": "awaiting", "undecided": "awaiting",
}
HISTORY_LIMIT = 500

ID_LINE = re.compile(r"^\s*[-*]\s+\[(?P<id>[A-Z]{2,4}-\d{2,3}[a-z]?)\]\s*(?P<rest>.*)$")
HEADING = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.+?)\s*#*\s*$")
SOURCE = re.compile(r"\*\((?P<src>[^()]*)\)\*\s*$")
TITLE = re.compile(r"^\*\*(?P<title>.+?)\*\*\s*(?:[—–:-]+\s*)?(?P<desc>.*)$")


# --------------------------------------------------------------------------- #
# Parsing & state
# --------------------------------------------------------------------------- #

def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def strip_md(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class Idea:
    id: str
    title: str
    desc: str
    category: str
    section: str
    source: str
    starred: bool
    line: int
    file: str = "IDEAS.md"


def parse_all() -> tuple[list[Idea], list[str]]:
    """Ideas from every source file (IDEAS.md, OBJECTS.md), with duplicate-ID checks across files."""
    ideas: list[Idea] = []
    warnings: list[str] = []
    seen: dict[str, str] = {}
    for path, prefix in SOURCES:
        if not path.exists():
            if path == IDEAS_MD:
                warnings.append(f"{path.name} not found")
            continue
        found, warn = parse_ideas(path, prefix)
        warnings += warn
        for idea in found:
            if idea.id in seen:
                warnings.append(f"Duplicate ID {idea.id} in {idea.file} (already in {seen[idea.id]}) ignored")
                continue
            seen[idea.id] = idea.file
            ideas.append(idea)
    return ideas, warnings


def parse_ideas(path: Path = IDEAS_MD, category_prefix: str = "") -> tuple[list[Idea], list[str]]:
    """Return (ideas in file order, warnings) for one markdown file."""
    if not path.exists():
        return [], [f"{path.name} not found"]
    ideas: list[Idea] = []
    warnings: list[str] = []
    seen: set[str] = set()
    category, section = "Uncategorized", ""
    current: dict | None = None
    in_code = False

    def finish():
        nonlocal current
        if current is None:
            return
        text = " ".join(current["parts"]).strip()
        starred = "⭐" in text
        text = text.replace("⭐", " ").strip()
        source = ""
        m = SOURCE.search(text)
        if m:
            source = m["src"].strip()
            text = text[: m.start()].strip()
        m = TITLE.match(text)
        if m:
            title, desc = m["title"], m["desc"]
        else:
            title, _, desc = text.partition(" — ")
        idea = Idea(current["id"], strip_md(title), strip_md(desc), category_prefix + current["category"],
                    current["section"], source, starred, current["line"], path.name)
        if idea.id in seen:
            warnings.append(f"Duplicate ID {idea.id} (line {idea.line}) ignored")
        else:
            seen.add(idea.id)
            ideas.append(idea)
        current = None

    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if raw.strip().startswith("```"):
            finish()
            in_code = not in_code
            continue
        if in_code:
            continue
        m = HEADING.match(raw)
        if m:
            finish()
            text = strip_md(m["text"])
            if len(m["hashes"]) <= 2:
                category = re.sub(r"^\d+[.)]\s*", "", text)
                section = ""
            else:
                section = text
            continue
        m = ID_LINE.match(raw)
        if m:
            finish()
            current = {"id": m["id"], "parts": [m["rest"]], "category": category,
                       "section": section, "line": lineno}
            continue
        if current is not None and raw.strip() and raw[:1] in (" ", "\t") \
                and not raw.lstrip().startswith(("- ", "* ")):
            current["parts"].append(raw.strip())       # indented continuation line
            continue
        finish()
    finish()
    return ideas, warnings


def _mtime(path: Path) -> int | None:
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return None


def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    for attempt in range(10):                           # Windows: reader may hold the file
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.05 * (attempt + 1))
    os.replace(tmp, path)


class Store:
    """Ideas from IDEAS.md merged with decisions from ideas_status.json."""

    def __init__(self) -> None:
        self.ideas: list[Idea] = []
        self.by_id: dict[str, Idea] = {}
        self.data: dict = {}
        self.warnings: list[str] = []
        self.mtime_md: dict[str, int | None] = {}
        self.mtime_json: int | None = None
        self.load_state()
        self.sync_ideas()

    # -- loading ----------------------------------------------------------- #
    def load_state(self) -> None:
        data: dict = {}
        if STATE_JSON.exists():
            try:
                data = json.loads(STATE_JSON.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                backup = STATE_JSON.with_name(f"ideas_status.corrupt-{int(time.time())}.json")
                try:
                    STATE_JSON.replace(backup)
                except OSError:
                    pass
                self.warnings.append(f"ideas_status.json unreadable ({exc}); backed up to {backup.name}")
                data = {}
        data.setdefault("ideas", {})
        data.setdefault("history", [])
        data.setdefault("ui", {})
        self.data = data
        self.mtime_json = _mtime(STATE_JSON)

    def sync_ideas(self) -> bool:
        """Re-parse IDEAS.md and merge. Returns True if the state changed."""
        self.mtime_md = {str(p): _mtime(p) for p, _ in SOURCES}
        ideas, warnings = parse_all()
        self.warnings = [w for w in self.warnings if "unreadable" in w] + warnings
        self.ideas = ideas
        self.by_id = {i.id: i for i in ideas}
        changed = False
        states = self.data["ideas"]
        for idea in ideas:
            entry = states.get(idea.id)
            fresh = {"title": idea.title, "category": idea.category, "section": idea.section,
                     "starred": idea.starred, "file": idea.file, "in_ideas_md": True}
            if entry is None:
                entry = {"status": "awaiting", "note": "", "changed": None, **fresh}
                states[idea.id] = entry
                changed = True
            elif any(entry.get(k) != v for k, v in fresh.items()):
                entry.update(fresh)
                changed = True
            if entry.get("status") not in STATUSES:
                entry["status"] = "awaiting"
                changed = True
        for iid, entry in states.items():
            if iid not in self.by_id and entry.get("in_ideas_md", True):
                entry["in_ideas_md"] = False               # removed from IDEAS.md; keep decision
                changed = True
        # keep JSON ordered like IDEAS.md, removed ideas last
        order = [i.id for i in ideas] + sorted(k for k in states if k not in self.by_id)
        self.data["ideas"] = {k: states[k] for k in order}
        return changed

    def reload_if_changed(self) -> tuple[bool, bool]:
        """Poll both files. Returns (ideas_md_changed, json_changed_externally)."""
        md_changed = json_changed = False
        m = _mtime(STATE_JSON)
        if m != self.mtime_json:
            self.load_state()
            json_changed = True
            if self.sync_ideas():
                self.save()
        if {str(p): _mtime(p) for p, _ in SOURCES} != self.mtime_md:
            md_changed = True
            if self.sync_ideas():
                self.save()
        return md_changed, json_changed

    # -- queries ------------------------------------------------------------ #
    def status(self, iid: str) -> str:
        return self.data["ideas"].get(iid, {}).get("status", "awaiting")

    def note(self, iid: str) -> str:
        return self.data["ideas"].get(iid, {}).get("note", "")

    def counts(self, ids=None) -> dict[str, int]:
        ids = [i.id for i in self.ideas] if ids is None else ids
        c = {s: 0 for s in STATUSES}
        for iid in ids:
            c[self.status(iid)] += 1
        c["total"] = len(ids)
        return c

    def resolve(self, patterns: list[str]) -> list[str]:
        out: list[str] = []
        for p in patterns:
            p = p.upper()
            matches = [i.id for i in self.ideas if fnmatch.fnmatchcase(i.id, p)]
            if not matches:
                raise SystemExit(f"No idea matches {p!r}")
            out.extend(m for m in matches if m not in out)
        return out

    # -- mutations ---------------------------------------------------------- #
    def set_status(self, ids: list[str], status: str) -> list[tuple[str, str]]:
        """Returns [(id, previous_status)] for ideas that actually changed."""
        changed = []
        stamp = now_iso()
        for iid in ids:
            entry = self.data["ideas"].get(iid)
            if entry is None or entry["status"] == status:
                continue
            changed.append((iid, entry["status"]))
            self.data["history"].append({"time": stamp, "id": iid, "from": entry["status"], "to": status})
            entry["status"] = status
            entry["changed"] = stamp
        del self.data["history"][:-HISTORY_LIMIT]
        return changed

    def set_note(self, iid: str, note: str) -> bool:
        entry = self.data["ideas"].get(iid)
        note = note.strip()
        if entry is None or entry.get("note", "") == note:
            return False
        entry["note"] = note
        entry["changed"] = now_iso()
        return True

    # -- saving ------------------------------------------------------------- #
    def save(self, digest: bool = True) -> None:
        self.data["_about"] = (
            "Lycantrope idea tracker state. Source of truth for idea decisions. "
            "IDs come from IDEAS.md, OBJECTS.md and ENEMIES.md ('file' says which; 'in_ideas_md' means the ID "
            "still exists in its source file). status is one of: awaiting, approved, denied. "
            "'ui' records what the user had selected/filtered in the tracker window. "
            "Edit via tools/idea_tracker.py (GUI or CLI); the GUI hot-reloads this file."
        )
        self.data["updated"] = now_iso()
        self.data["counts"] = self.counts()
        ordered = {k: self.data[k] for k in ("_about", "updated", "counts", "ui", "ideas", "history")}
        _atomic_write(STATE_JSON, json.dumps(ordered, indent=2, ensure_ascii=False) + "\n")
        self.mtime_json = _mtime(STATE_JSON)
        if digest:
            _atomic_write(STATUS_MD, self.digest_markdown())

    def digest_markdown(self) -> str:
        c = self.counts()
        lines = [
            "# Lycantrope — Idea Status",
            "",
            f"_Auto-generated by `tools/idea_tracker.py` on {now_iso()}. "
            "Source of truth: `ideas_status.json`. Do not edit by hand._",
            "",
            f"**Total {c['total']}** · ✔ Approved {c['approved']} · ✘ Denied {c['denied']} "
            f"· ○ Awaiting {c['awaiting']}",
            "",
        ]
        for status in ("approved", "denied", "awaiting"):
            ids = [i for i in self.ideas if self.status(i.id) == status]
            lines += [f"## {ICONS[status]} {LABELS[status]} ({len(ids)})", ""]
            if not ids:
                lines += ["_None._", ""]
                continue
            cat = None
            for idea in ids:
                if idea.category != cat:
                    cat = idea.category
                    lines += ["", f"### {cat}", ""]
                star = " ⭐" if idea.starred else ""
                note = self.note(idea.id)
                lines.append(f"- **{idea.id}** {idea.title}{star}" + (f" — _{note}_" if note else ""))
            lines.append("")
        orphans = [k for k, v in self.data["ideas"].items() if not v.get("in_ideas_md", True)]
        if orphans:
            lines += ["## Removed from the source files (decision kept)", ""]
            lines += [f"- **{k}** {self.data['ideas'][k].get('title', '')} — "
                      f"{self.data['ideas'][k]['status']}" for k in orphans]
            lines.append("")
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _console_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def cli_summary(store: Store) -> None:
    c = store.counts()
    print(f"Lycantrope ideas — total {c['total']}: approved {c['approved']}, "
          f"denied {c['denied']}, awaiting {c['awaiting']}")
    cats: dict[str, list[str]] = {}
    for i in store.ideas:
        cats.setdefault(i.category, []).append(i.id)
    print()
    for cat, ids in cats.items():
        cc = store.counts(ids)
        print(f"  {cat:<32} ✔{cc['approved']:>3}  ✘{cc['denied']:>3}  ○{cc['awaiting']:>3}")
    for status in ("approved", "denied"):
        rows = [i for i in store.ideas if store.status(i.id) == status]
        if rows:
            print(f"\n{LABELS[status]}:")
            for i in rows:
                note = store.note(i.id)
                print(f"  {i.id:<8} {i.title}" + (f"  [note: {note}]" if note else ""))
    notes = [i for i in store.ideas if store.status(i.id) == "awaiting" and store.note(i.id)]
    if notes:
        print("\nAwaiting, with notes:")
        for i in notes:
            print(f"  {i.id:<8} {i.title}  [note: {store.note(i.id)}]")
    hist = store.data["history"][-10:]
    if hist:
        print("\nRecent changes:")
        for h in reversed(hist):
            print(f"  {h['time']}  {h['id']:<8} {h['from']} → {h['to']}")
    sel = store.data.get("ui", {}).get("selected")
    if sel:
        print(f"\nSelected in the tracker window: {', '.join(sel)}")
    for w in store.warnings:
        print(f"\nWARNING: {w}")


def main_cli(argv: list[str]) -> int:
    _console_utf8()
    ap = argparse.ArgumentParser(description="Lycantrope idea tracker")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("gui", help="open the window (default)")
    sub.add_parser("summary", help="print counts and decisions")
    p = sub.add_parser("list", help="list ideas with a status")
    p.add_argument("status", choices=sorted(set(ALIASES)), metavar="STATUS")
    p = sub.add_parser("set", help="set status for IDs (wildcards ok)")
    p.add_argument("status", choices=sorted(set(ALIASES)), metavar="STATUS")
    p.add_argument("ids", nargs="+")
    p.add_argument("--note")
    p = sub.add_parser("note", help="set the note for one idea")
    p.add_argument("id")
    p.add_argument("text")
    args = ap.parse_args(argv)

    if args.cmd in (None, "gui"):
        return run_gui()
    store = Store()
    if args.cmd == "summary":
        store.save()
        cli_summary(store)
    elif args.cmd == "list":
        status = ALIASES[args.status]
        for i in store.ideas:
            if store.status(i.id) == status:
                print(f"{i.id:<8} {i.title}")
    elif args.cmd == "set":
        status = ALIASES[args.status]
        ids = store.resolve(args.ids)
        changed = store.set_status(ids, status)
        if args.note is not None:
            for iid in ids:
                store.set_note(iid, args.note)
        store.save()
        print(f"{len(changed)} changed → {status}: {', '.join(i for i, _ in changed) or '(none)'}")
    elif args.cmd == "note":
        iid = store.resolve([args.id])[0]
        store.set_note(iid, args.text)
        store.save()
        print(f"Note saved for {iid}")
    return 0


# --------------------------------------------------------------------------- #
# GUI
# --------------------------------------------------------------------------- #

def run_gui() -> int:
    import tkinter as tk
    from tkinter import font as tkfont
    from tkinter import messagebox, ttk

    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    C = {
        "bg": "#1b1920", "panel": "#24212b", "field": "#2d2a35", "fg": "#ebe7f2",
        "muted": "#9d96ab", "accent": "#d4a53c", "sel": "#4a3f63",
        "approved": "#7bd88f", "denied": "#ef7a85", "awaiting": "#cfc8de", "cat": "#d4a53c",
    }

    class App(tk.Tk):
        def __init__(self) -> None:
            super().__init__()
            self.store = Store()
            self.title("Lycantrope — Idea Tracker")
            self.geometry("1360x820")
            self.minsize(980, 560)
            self.configure(bg=C["bg"])
            self.undo_stack: list[list[tuple[str, str]]] = []
            self.current: str | None = None
            self.note_dirty = False
            self.note_job = None
            self.ui_job = None
            self.flash_job = None
            self.visible: list[str] = []

            self._fonts()
            self._style()
            self._build()
            ui = self.store.data.get("ui", {})
            self.filter_var.set(ui.get("filter", "all"))
            self.search_var.set(ui.get("search", ""))
            self.star_var.set(ui.get("starred_only", False))
            self.cat_var.set(ui.get("category", "All categories"))
            self.refresh(select=(ui.get("selected") or [None])[0])
            self.after(1500, self.poll)
            self.protocol("WM_DELETE_WINDOW", self.on_close)

        # ---------------- look ---------------- #
        def _fonts(self) -> None:
            base = tkfont.nametofont("TkDefaultFont")
            fam = "Segoe UI" if sys.platform == "win32" else base.actual("family")
            base.configure(family=fam, size=10)
            self.f_base = base
            self.f_small = tkfont.Font(family=fam, size=9)
            self.f_bold = tkfont.Font(family=fam, size=10, weight="bold")
            self.f_title = tkfont.Font(family=fam, size=15, weight="bold")
            self.f_strike = tkfont.Font(family=fam, size=10, overstrike=1)
            self.f_text = tkfont.Font(family=fam, size=11)

        def _style(self) -> None:
            s = ttk.Style(self)
            s.theme_use("clam")
            s.configure(".", background=C["bg"], foreground=C["fg"], fieldbackground=C["field"],
                        bordercolor=C["panel"], lightcolor=C["panel"], darkcolor=C["panel"],
                        troughcolor=C["panel"], focuscolor=C["accent"], font=self.f_base)
            s.configure("TFrame", background=C["bg"])
            s.configure("Panel.TFrame", background=C["panel"])
            s.configure("TLabel", background=C["bg"], foreground=C["fg"])
            s.configure("Panel.TLabel", background=C["panel"])
            s.configure("Muted.TLabel", background=C["panel"], foreground=C["muted"], font=self.f_small)
            s.configure("Title.TLabel", background=C["panel"], foreground=C["fg"], font=self.f_title)
            s.configure("Status.TLabel", background=C["bg"], foreground=C["muted"], font=self.f_small)
            s.configure("TButton", background=C["field"], foreground=C["fg"], padding=(10, 5),
                        borderwidth=0)
            s.map("TButton", background=[("active", C["sel"])])
            for name in ("approved", "denied", "awaiting"):
                s.configure(f"{name}.TButton", foreground=C[name], font=self.f_bold)
            s.configure("TRadiobutton", background=C["bg"], foreground=C["fg"])
            s.map("TRadiobutton", background=[("active", C["bg"])],
                  indicatorcolor=[("selected", C["accent"]), ("!selected", C["field"])])
            s.configure("TCheckbutton", background=C["bg"], foreground=C["fg"])
            s.map("TCheckbutton", background=[("active", C["bg"])],
                  indicatorcolor=[("selected", C["accent"]), ("!selected", C["field"])])
            s.configure("TEntry", fieldbackground=C["field"], foreground=C["fg"],
                        insertcolor=C["fg"], padding=4)
            s.configure("TCombobox", fieldbackground=C["field"], background=C["field"],
                        foreground=C["fg"], arrowcolor=C["fg"], padding=3)
            s.map("TCombobox", fieldbackground=[("readonly", C["field"])],
                  foreground=[("readonly", C["fg"])], selectbackground=[("readonly", C["field"])])
            self.option_add("*TCombobox*Listbox.background", C["field"])
            self.option_add("*TCombobox*Listbox.foreground", C["fg"])
            self.option_add("*TCombobox*Listbox.selectBackground", C["sel"])
            rowh = int(self.f_base.metrics("linespace") * 1.65)
            s.configure("Treeview", background=C["panel"], fieldbackground=C["panel"],
                        foreground=C["fg"], rowheight=rowh, borderwidth=0)
            s.map("Treeview", background=[("selected", C["sel"])], foreground=[("selected", C["fg"])])
            s.configure("Treeview.Heading", background=C["field"], foreground=C["muted"],
                        font=self.f_bold, relief="flat", padding=4)
            s.map("Treeview.Heading", background=[("active", C["sel"])])
            s.configure("Vertical.TScrollbar", background=C["field"], arrowcolor=C["muted"])
            s.configure("TPanedwindow", background=C["bg"])

        # ---------------- layout ---------------- #
        def _build(self) -> None:
            top = ttk.Frame(self, padding=(12, 10, 12, 6))
            top.pack(fill="x")
            ttk.Label(top, text="Search").pack(side="left")
            self.search_var = tk.StringVar()
            self.search = ttk.Entry(top, textvariable=self.search_var, width=28)
            self.search.pack(side="left", padx=(6, 14))
            self.search_var.trace_add("write", lambda *_: self.refresh())

            self.filter_var = tk.StringVar(value="all")
            self.filter_buttons = {}
            for key in ("all", "awaiting", "approved", "denied"):
                b = ttk.Radiobutton(top, variable=self.filter_var, value=key,
                                    command=self.refresh, text=key.title())
                b.pack(side="left", padx=4)
                self.filter_buttons[key] = b

            self.cat_var = tk.StringVar(value="All categories")
            self.cat_box = ttk.Combobox(top, textvariable=self.cat_var, state="readonly", width=26)
            self.cat_box.pack(side="left", padx=(14, 8))
            self.cat_box.bind("<<ComboboxSelected>>", lambda e: self.refresh())

            self.star_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(top, text="⭐ First Playable only", variable=self.star_var,
                            command=self.refresh).pack(side="left", padx=8)
            self.auto_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(top, text="Auto-advance", variable=self.auto_var).pack(side="left", padx=8)
            ttk.Button(top, text="Collapse", command=lambda: self.expand(False)).pack(side="right")
            ttk.Button(top, text="Expand", command=lambda: self.expand(True)).pack(side="right", padx=6)

            paned = ttk.Panedwindow(self, orient="horizontal")
            paned.pack(fill="both", expand=True, padx=12, pady=(0, 6))

            left = ttk.Frame(paned, style="Panel.TFrame")
            self.tree = ttk.Treeview(left, columns=("status", "title", "src"), show="tree headings",
                                     selectmode="extended")
            self.tree.heading("#0", text="ID", anchor="w")
            self.tree.heading("status", text="Status", anchor="w")
            self.tree.heading("title", text="Idea", anchor="w")
            self.tree.heading("src", text="Source / where", anchor="w")
            self.tree.column("#0", width=150, stretch=False)
            self.tree.column("status", width=110, stretch=False)
            self.tree.column("title", width=380, stretch=True)
            self.tree.column("src", width=120, stretch=False)
            sb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
            self.tree.configure(yscrollcommand=sb.set)
            self.tree.pack(side="left", fill="both", expand=True)
            sb.pack(side="right", fill="y")
            for st in STATUSES:
                self.tree.tag_configure(st, foreground=C[st])
            self.tree.tag_configure("denied", font=self.f_strike)
            self.tree.tag_configure("cat", foreground=C["cat"], font=self.f_bold)
            paned.add(left, weight=3)

            right = ttk.Frame(paned, style="Panel.TFrame", padding=16)
            paned.add(right, weight=2)
            self.d_title = ttk.Label(right, style="Title.TLabel", text="", wraplength=460, justify="left")
            self.d_title.pack(anchor="w", fill="x")
            self.d_meta = ttk.Label(right, style="Muted.TLabel", text="", wraplength=460, justify="left")
            self.d_meta.pack(anchor="w", fill="x", pady=(2, 8))
            self.d_status = tk.Label(right, text="", bg=C["panel"], fg=C["fg"], font=self.f_bold,
                                     anchor="w")
            self.d_status.pack(anchor="w", fill="x")
            self.d_desc = tk.Text(right, wrap="word", height=7, bg=C["panel"], fg=C["fg"],
                                  relief="flat", font=self.f_text, padx=0, pady=6,
                                  highlightthickness=0, cursor="arrow")
            self.d_desc.pack(fill="both", expand=True, pady=(4, 8))
            self.d_desc.configure(state="disabled")

            btns = ttk.Frame(right, style="Panel.TFrame")
            btns.pack(fill="x", pady=(0, 10))
            ttk.Button(btns, text="✔ Approve  (A)", style="approved.TButton",
                       command=lambda: self.apply("approved")).pack(side="left")
            ttk.Button(btns, text="✘ Deny  (D)", style="denied.TButton",
                       command=lambda: self.apply("denied")).pack(side="left", padx=6)
            ttk.Button(btns, text="○ Awaiting  (W)", style="awaiting.TButton",
                       command=lambda: self.apply("awaiting")).pack(side="left")
            ttk.Button(btns, text="Copy ref", command=self.copy_ref).pack(side="right")
            ttk.Button(btns, text="Undo", command=self.undo).pack(side="right", padx=6)

            ttk.Label(right, text="Note (saved automatically — Claude sees this too)",
                      style="Muted.TLabel").pack(anchor="w")
            self.d_note = tk.Text(right, wrap="word", height=5, bg=C["field"], fg=C["fg"],
                                  insertbackground=C["fg"], relief="flat", font=self.f_base,
                                  padx=8, pady=6, highlightthickness=1,
                                  highlightbackground=C["field"], highlightcolor=C["accent"])
            self.d_note.pack(fill="x", pady=(2, 10))
            self.d_note.bind("<KeyRelease>", self.on_note_key)
            self.d_note.bind("<FocusOut>", lambda e: self.flush_note())

            ttk.Label(right, text="Recent changes (click to jump)", style="Muted.TLabel").pack(anchor="w")
            self.hist = tk.Listbox(right, height=7, bg=C["field"], fg=C["muted"], relief="flat",
                                   highlightthickness=0, selectbackground=C["sel"],
                                   activestyle="none", font=self.f_small)
            self.hist.pack(fill="x", pady=(2, 0))
            self.hist.bind("<<ListboxSelect>>", self.on_hist)

            self.status = ttk.Label(self, style="Status.TLabel", padding=(12, 0, 12, 8))
            self.status.pack(fill="x")

            self.tree.bind("<<TreeviewSelect>>", self.on_select)
            self.tree.bind("<Double-1>", self.on_double)
            self.tree.bind("<Button-3>", self.on_context)
            for key, st in (("a", "approved"), ("d", "denied"), ("w", "awaiting")):
                self.tree.bind(f"<KeyPress-{key}>", lambda e, s=st: self.apply(s))
                self.tree.bind(f"<KeyPress-{key.upper()}>", lambda e, s=st: self.apply(s))
            self.tree.bind("<space>", lambda e: self.cycle())
            self.tree.bind("<Return>", lambda e: self.cycle())
            self.tree.bind("<Control-c>", lambda e: self.copy_ref())
            self.bind_all("<Control-z>", self.on_ctrl_z)
            self.bind_all("<Control-f>", lambda e: (self.search.focus_set(), "break")[1])
            self.search.bind("<Escape>", lambda e: (self.search_var.set(""), self.tree.focus_set()))
            self.search.bind("<Down>", lambda e: self.tree.focus_set())

            self.menu = tk.Menu(self, tearoff=0, bg=C["field"], fg=C["fg"],
                                activebackground=C["sel"], activeforeground=C["fg"])
            self.menu.add_command(label="✔ Approve", command=lambda: self.apply("approved"))
            self.menu.add_command(label="✘ Deny", command=lambda: self.apply("denied"))
            self.menu.add_command(label="○ Awaiting", command=lambda: self.apply("awaiting"))
            self.menu.add_separator()
            self.menu.add_command(label="Copy reference", command=self.copy_ref)
            self.menu.add_command(label="Open IDEAS.md", command=lambda: self.open_file(IDEAS_MD))
            self.menu.add_command(label="Open OBJECTS.md", command=lambda: self.open_file(OBJECTS_MD))
            self.menu.add_command(label="Open ENEMIES.md", command=lambda: self.open_file(ENEMIES_MD))
            self.menu.add_command(label="Open IDEAS_STATUS.md", command=lambda: self.open_file(STATUS_MD))

        # ---------------- data → view ---------------- #
        def filtered(self) -> list[Idea]:
            f = self.filter_var.get()
            q = self.search_var.get().strip().lower()
            cat = self.cat_var.get()
            out = []
            for i in self.store.ideas:
                if f != "all" and self.store.status(i.id) != f:
                    continue
                if cat != "All categories" and i.category != cat:
                    continue
                if self.star_var.get() and not i.starred:
                    continue
                if q and q not in f"{i.id} {i.title} {i.desc} {i.source} {self.store.note(i.id)}".lower():
                    continue
                out.append(i)
            return out

        def refresh(self, select: str | None = None) -> None:
            if not hasattr(self, "tree"):
                return
            keep = select or self.current
            sel = [s for s in self.tree.selection() if not s.startswith("cat::")]
            closed = {c for c in self.tree.get_children() if not self.tree.item(c, "open")}
            self.tree.delete(*self.tree.get_children())

            cats = list(dict.fromkeys(i.category for i in self.store.ideas))
            self.cat_box["values"] = ["All categories"] + cats
            if self.cat_var.get() not in self.cat_box["values"]:
                self.cat_var.set("All categories")

            ideas = self.filtered()
            all_by_cat: dict[str, list[str]] = {}
            for i in self.store.ideas:
                all_by_cat.setdefault(i.category, []).append(i.id)
            parents: dict[str, str] = {}
            self.visible = []
            for i in ideas:
                if i.category not in parents:
                    pid = f"cat::{i.category}"
                    cc = self.store.counts(all_by_cat[i.category])
                    decided = cc["approved"] + cc["denied"]
                    self.tree.insert("", "end", iid=pid, text=i.category, open=pid not in closed,
                                     values=(f"{decided}/{cc['total']} decided",
                                             f"✔ {cc['approved']}   ✘ {cc['denied']}   ○ {cc['awaiting']}", ""),
                                     tags=("cat",))
                    parents[i.category] = pid
                st = self.store.status(i.id)
                title = ("⭐ " if i.starred else "") + i.title + ("   ✎" if self.store.note(i.id) else "")
                self.tree.insert(parents[i.category], "end", iid=i.id, text=i.id,
                                 values=(f"{ICONS[st]} {LABELS[st]}", title, i.source), tags=(st,))
                self.visible.append(i.id)

            c = self.store.counts()
            for key, b in self.filter_buttons.items():
                n = c["total"] if key == "all" else c[key]
                b.configure(text=f"{key.title()} ({n})")

            restore = [s for s in sel if self.tree.exists(s)]
            if keep and self.tree.exists(keep) and keep not in restore:
                restore = [keep] if not restore else restore
            if restore:
                self.tree.selection_set(restore)
                self.tree.focus(restore[0])
                self.tree.see(restore[0])
            self.show(restore[0] if restore else None)
            self.refresh_history()
            self.update_status()

        def refresh_history(self) -> None:
            self.hist.delete(0, "end")
            self.hist_ids = []
            for h in reversed(self.store.data["history"][-40:]):
                t = h["time"][11:16]
                title = self.store.by_id[h["id"]].title if h["id"] in self.store.by_id else ""
                self.hist.insert("end", f"{t}  {h['id']}  {ICONS[h['from']]}→{ICONS[h['to']]}  {title}")
                self.hist_ids.append(h["id"])

        def update_status(self, msg: str = "") -> None:
            c = self.store.counts()
            parts = [f"Total {c['total']}", f"✔ {c['approved']}", f"✘ {c['denied']}",
                     f"○ {c['awaiting']}", f"showing {len(self.visible)}",
                     f"state: {STATE_JSON.name}", "watching " + " + ".join(p.name for p, _ in SOURCES)]
            parts += [f"⚠ {w}" for w in self.store.warnings]
            if msg:
                parts.insert(0, msg)
            self.status.configure(text="   ·   ".join(parts))

        def flash(self, msg: str) -> None:
            self.update_status(msg)
            if self.flash_job:
                self.after_cancel(self.flash_job)
            self.flash_job = self.after(4000, self.update_status)

        def show(self, iid: str | None) -> None:
            self.flush_note()
            self.current = iid if iid and not iid.startswith("cat::") else None
            self.d_desc.configure(state="normal")
            self.d_desc.delete("1.0", "end")
            self.d_note.configure(state="normal")
            self.d_note.delete("1.0", "end")
            if self.current is None:
                if iid and iid.startswith("cat::"):
                    cat = iid[5:]
                    ids = [i.id for i in self.store.ideas if i.category == cat]
                    cc = self.store.counts(ids)
                    self.d_title.configure(text=cat)
                    self.d_meta.configure(text=f"{cc['total']} ideas")
                    self.d_status.configure(text=f"✔ {cc['approved']}   ✘ {cc['denied']}   ○ {cc['awaiting']}",
                                            fg=C["muted"])
                    self.d_desc.insert("1.0", "Select ideas in this category, or select the category row "
                                              "and press A / D / W to decide every visible idea in it.")
                else:
                    self.d_title.configure(text="No idea selected")
                    self.d_meta.configure(text="")
                    self.d_status.configure(text="")
                self.d_desc.configure(state="disabled")
                self.d_note.configure(state="disabled")
                self.schedule_ui_save()
                return
            idea = self.store.by_id[iid]
            st = self.store.status(iid)
            self.d_title.configure(text=f"{idea.id} · {idea.title}")
            where = idea.category + (f" › {idea.section}" if idea.section else "")
            meta = [where]
            if idea.source:
                meta.append(f"Inspired by: {idea.source}")
            if idea.starred:
                meta.append("⭐ First Playable")
            meta.append(f"{idea.file} line {idea.line}")
            self.d_meta.configure(text="   ·   ".join(meta))
            changed = self.store.data["ideas"][iid].get("changed")
            self.d_status.configure(text=f"{ICONS[st]} {LABELS[st]}" + (f"   (changed {changed})" if changed else ""),
                                    fg=C[st])
            self.d_desc.insert("1.0", idea.desc)
            self.d_desc.configure(state="disabled")
            self.d_note.configure(state="normal")
            self.d_note.insert("1.0", self.store.note(iid))
            self.note_dirty = False
            self.schedule_ui_save()

        # ---------------- actions ---------------- #
        def selected_ids(self) -> list[str]:
            sel = list(self.tree.selection())
            ids = [s for s in sel if not s.startswith("cat::")]
            cats = [s for s in sel if s.startswith("cat::")]
            if cats and not ids:
                kids = [k for c in cats for k in self.tree.get_children(c)]
                names = ", ".join(c[5:] for c in cats)
                if kids and messagebox.askyesno("Decide whole category",
                                                f"Apply to all {len(kids)} visible ideas in {names}?",
                                                parent=self):
                    return kids
                return []
            return ids

        def apply(self, status: str):
            ids = self.selected_ids()
            if not ids:
                return "break"
            self.flush_note()
            nxt = self.next_after(ids[-1]) if (self.auto_var.get() and len(ids) == 1) else None
            changes = self.store.set_status(ids, status)
            if changes:
                self.undo_stack.append(changes)
                self.store.save()
            self.refresh(select=nxt or ids[0])
            if nxt and self.tree.exists(nxt):
                self.tree.selection_set(nxt)
                self.tree.focus(nxt)
                self.tree.see(nxt)
            self.tree.focus_set()
            label = ", ".join(i for i, _ in changes[:6]) + ("…" if len(changes) > 6 else "")
            self.flash(f"{ICONS[status]} {LABELS[status]}: {label}" if changes else "No change")
            return "break"

        def next_after(self, iid: str) -> str | None:
            if iid not in self.visible:
                return None
            idx = self.visible.index(iid)
            rest = self.visible[idx + 1:] + self.visible[:idx]
            for cand in rest:
                if self.store.status(cand) == "awaiting":
                    return cand
            return self.visible[idx + 1] if idx + 1 < len(self.visible) else None

        def cycle(self):
            ids = self.selected_ids()
            if len(ids) != 1:
                return "break"
            order = {"awaiting": "approved", "approved": "denied", "denied": "awaiting"}
            auto = self.auto_var.get()
            self.auto_var.set(False)
            try:
                self.apply(order[self.store.status(ids[0])])
            finally:
                self.auto_var.set(auto)
            return "break"

        def undo(self) -> None:
            if not self.undo_stack:
                self.flash("Nothing to undo")
                return
            changes = self.undo_stack.pop()
            for iid, old in changes:
                self.store.set_status([iid], old)
            self.store.save()
            self.refresh(select=changes[0][0])
            self.flash(f"Undid {len(changes)} change(s)")

        def on_ctrl_z(self, event):
            if isinstance(event.widget, (tk.Text, ttk.Entry, tk.Entry)):
                return None
            self.undo()
            return "break"

        def copy_ref(self):
            ids = [s for s in self.tree.selection() if not s.startswith("cat::")] or \
                  ([self.current] if self.current else [])
            if not ids:
                return "break"
            text = "\n".join(f"{i} {self.store.by_id[i].title} [{LABELS[self.store.status(i)]}]"
                             for i in ids)
            self.clipboard_clear()
            self.clipboard_append(text)
            self.flash(f"Copied {len(ids)} reference(s)")
            return "break"

        def expand(self, open_: bool) -> None:
            for c in self.tree.get_children():
                self.tree.item(c, open=open_)

        def open_file(self, path: Path) -> None:
            try:
                if sys.platform == "win32":
                    os.startfile(path)  # type: ignore[attr-defined]
                else:
                    import subprocess
                    subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(path)])
            except OSError as exc:
                messagebox.showerror("Open file", str(exc), parent=self)

        # ---------------- events ---------------- #
        def on_select(self, _event=None) -> None:
            focus = self.tree.focus()
            sel = self.tree.selection()
            self.show(focus if focus in sel else (sel[0] if sel else None))

        def on_double(self, event) -> str | None:
            row = self.tree.identify_row(event.y)
            if row and not row.startswith("cat::"):
                return self.cycle()
            return None

        def on_context(self, event) -> None:
            row = self.tree.identify_row(event.y)
            if row and row not in self.tree.selection():
                self.tree.selection_set(row)
                self.tree.focus(row)
            self.menu.tk_popup(event.x_root, event.y_root)

        def on_hist(self, _event=None) -> None:
            cur = self.hist.curselection()
            if not cur:
                return
            iid = self.hist_ids[cur[0]]
            if not self.tree.exists(iid):
                self.filter_var.set("all")
                self.search_var.set("")
                self.star_var.set(False)
                self.cat_var.set("All categories")
                self.refresh()
            if self.tree.exists(iid):
                self.tree.selection_set(iid)
                self.tree.focus(iid)
                self.tree.see(iid)

        def on_note_key(self, _event=None) -> None:
            if self.current is None:
                return
            self.note_dirty = True
            if self.note_job:
                self.after_cancel(self.note_job)
            self.note_job = self.after(700, self.flush_note)

        def flush_note(self) -> None:
            if self.note_job:
                self.after_cancel(self.note_job)
                self.note_job = None
            if not self.note_dirty or self.current is None:
                return
            self.note_dirty = False
            if self.store.set_note(self.current, self.d_note.get("1.0", "end")):
                self.store.save()
                if self.tree.exists(self.current):
                    vals = list(self.tree.item(self.current, "values"))
                    idea = self.store.by_id[self.current]
                    vals[1] = ("⭐ " if idea.starred else "") + idea.title + \
                              ("   ✎" if self.store.note(self.current) else "")
                    self.tree.item(self.current, values=vals)
                self.flash(f"Note saved for {self.current}")

        def schedule_ui_save(self) -> None:
            if self.ui_job:
                self.after_cancel(self.ui_job)
            self.ui_job = self.after(1200, self.save_ui)

        def save_ui(self) -> None:
            self.ui_job = None
            sel = [s for s in self.tree.selection() if not s.startswith("cat::")]
            ui = {
                "selected": sel[:25],
                "selected_titles": {i: self.store.by_id[i].title for i in sel[:25] if i in self.store.by_id},
                "filter": self.filter_var.get(),
                "category": self.cat_var.get(),
                "search": self.search_var.get(),
                "starred_only": bool(self.star_var.get()),
                "window_open": True,
                "at": now_iso(),
            }
            if ui != self.store.data.get("ui"):
                self.store.data["ui"] = ui
                self.store.save(digest=False)

        def poll(self) -> None:
            try:
                pending = self.d_note.get("1.0", "end") if self.note_dirty and self.current else None
                cur = self.current
                md, js = self.store.reload_if_changed()
                if pending is not None and (md or js) and cur:
                    self.store.set_note(cur, pending)
                    self.store.save()
                if md or js:
                    self.note_dirty = False
                    self.refresh(select=cur)
                    self.flash("Reloaded " + " & ".join(n for n, f in (("the .md files", md),
                                                                        (STATE_JSON.name, js)) if f))
            except Exception as exc:                       # never let polling die
                self.flash(f"Reload error: {exc}")
            self.after(1500, self.poll)

        def on_close(self) -> None:
            self.flush_note()
            self.store.data.setdefault("ui", {})["window_open"] = False
            self.store.data["ui"]["at"] = now_iso()
            try:
                self.store.save()
            finally:
                self.destroy()

    if not IDEAS_MD.exists():
        print(f"IDEAS.md not found at {IDEAS_MD}", file=sys.stderr)
    app = App()
    if not app.store.data["ideas"]:
        app.after(200, lambda: messagebox.showinfo("Idea Tracker", "No ideas found in IDEAS.md yet.",
                                                   parent=app))
    else:
        app.store.save()
    app.tree.focus_set()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main_cli(sys.argv[1:]))
