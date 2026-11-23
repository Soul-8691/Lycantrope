"""Check that every caret marker in STORY.md has a note in ANNOTATIONS.md, and vice versa.

    python tools/story/check_annotations.py

Markers in STORY.md look like  [^12](ANNOTATIONS.md#a12)
Notes in ANNOTATIONS.md start with an anchor  <a id="a12"></a>
Also runs the racism filters over STORY.md as a final safety net.
"""
from __future__ import annotations

import re
import sys

from common import compile_blocklist, load_config, repo_path

MARK = re.compile(r"\[\^(\d+)\]\(ANNOTATIONS\.md#a(\d+)\)")
ANCHOR = re.compile(r'<a id="a(\d+)"></a>')


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cfg = load_config()
    story = repo_path(cfg["story_file"]).read_text(encoding="utf-8")
    notes = repo_path(cfg["annotations_file"]).read_text(encoding="utf-8")
    problems = []

    marks = MARK.findall(story)
    for shown, target in marks:
        if shown != target:
            problems.append(f"marker [^{shown}] links to #a{target}")
    used = [int(t) for _, t in marks]
    anchors = [int(a) for a in ANCHOR.findall(notes)]

    dup = {a for a in anchors if anchors.count(a) > 1}
    if dup:
        problems.append(f"duplicate notes: {sorted(dup)}")
    missing = sorted(set(used) - set(anchors))
    unused = sorted(set(anchors) - set(used))
    if missing:
        problems.append(f"markers with no note: {missing}")
    if unused:
        problems.append(f"notes never referenced: {unused}")
    stray = re.findall(r"\[\^\d+\](?!\()", story)
    if stray:
        problems.append(f"markers without a link: {stray[:5]}")

    block = compile_blocklist(cfg)
    for name, text in (("STORY.md", story), ("ANNOTATIONS.md", notes)):
        for m in block.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            problems.append(f"{name}:{line} matches the racism filter: '{m.group(0)}'")

    print(f"{len(set(used))} markers, {len(anchors)} notes")
    if problems:
        print("\n".join("PROBLEM: " + p for p in problems))
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
