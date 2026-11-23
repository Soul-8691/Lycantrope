"""Assemble a generation brief: everything a writer (or Claude) needs for one batch of lines.

    python tools/dialogue/brief.py --topic "latest rumors" \\
        --task "Arkham rumours for each value of tdl_ws_arkham; 4 per state, plus Watch and Collegium lines"
    python tools/dialogue/brief.py --topic "Greeting 5" --characters tdl_pell --task "Pell's greetings"

Writes tools/dialogue/out/briefs/<topic>.md and prints its path. Then, in Claude Code:
    "Write the lines described in tools/dialogue/out/briefs/latest_rumors.md into dialogue/topics/..."
or paste the brief into any chat. The brief contains the conventions, the world bible,
the story states, the relevant character sheets, the lines that already exist (locked
ones must be kept word for word) and the YAML format to answer in.
"""
from __future__ import annotations

import argparse
import re
import sys

import yaml

from dlg import load_config, load_sources, rel, repo_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True, help="topic name, e.g. 'latest rumors' or 'Greeting 5'")
    ap.add_argument("--task", required=True, help="what to write, in plain words")
    ap.add_argument("--characters", nargs="*", help="character ids to include (default: all)")
    ap.add_argument("--story", choices=["v1", "v2", "both"], help="default: config story")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    cfg = load_config()
    root = repo_path(cfg["source_dir"])
    src = load_sources(cfg)
    story = args.story or cfg["story"]

    def include(name: str) -> str:
        """An included document, minus its title, with headings pushed down one level."""
        text = (root / name).read_text(encoding="utf-8")
        text = re.sub(r"\A# .*\n", "", text)
        return re.sub(r"^(#+) ", r"#\1 ", text, flags=re.M).strip()

    want = {c.lower() for c in args.characters} if args.characters else None
    sheets = [s for cid, s in src.characters.items() if want is None or cid in want]
    existing = [ln for ln in src.lines if ln.topic.lower() == args.topic.lower()]

    parts = [
        f"# Dialogue brief: {args.topic}",
        "",
        "## Task",
        "",
        args.task,
        "",
        f"Story: **{story}** (tag lines `story: {story}` if they only fit this story, `both` if they fit either).",
        "",
        "## Conventions",
        "",
        include("conventions.md"),
        "",
        "## World bible",
        "",
        include("bible.md"),
        "",
        "## Story states, globals and factions (states.yaml)",
        "",
        "```yaml",
        (root / "states.yaml").read_text(encoding="utf-8").strip(),
        "```",
        "",
        "## Characters",
        "",
    ]
    for s in sheets:
        parts += ["```yaml", yaml.safe_dump(s, sort_keys=False, allow_unicode=True, width=100).strip(), "```", ""]
    if not sheets:
        parts += ["(none selected)", ""]

    parts += ["## Lines that already exist in this topic", ""]
    if existing:
        parts.append("Keep every **locked** line exactly as it is. Others may be rewritten; keep their keys.")
        parts.append("")
        for ln in existing:
            flag = "LOCKED " if ln.locked else ""
            parts.append(f"- {flag}`{ln.key}` ({rel(ln.file)}, story {ln.story}, when {ln.when}): {ln.text}")
    else:
        parts.append("(none yet)")
    parts += ["", "## Answer format", "",
              "Reply with one YAML document only, in this format (see conventions for the condition keys):",
              "", "```yaml", (root / "topics" / "_FORMAT.yaml").read_text(encoding="utf-8").strip(), "```", ""]

    out = repo_path(cfg["out_dir"]) / "briefs"
    out.mkdir(parents=True, exist_ok=True)
    path = out / (re.sub(r"[^a-z0-9]+", "_", args.topic.lower()).strip("_") + ".md")
    path.write_text("\n".join(parts), encoding="utf-8")
    print(f"brief written: {rel(path)} ({len(existing)} existing lines, {len(sheets)} character sheets)")


if __name__ == "__main__":
    main()
