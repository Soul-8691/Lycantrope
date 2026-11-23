"""Step 2: turn the corpus into training data for the style model.

    python tools/story/build_dataset.py

- Drops collaborations, juvenilia, and the titles listed in config.yaml.
- Drops every paragraph matching the slur list or the ethnic/racial descriptor
  list (config.yaml), and writes data/filtered_out.md so a human can audit them.
- Oversamples the heroic tales (config `upweight`).
- Packs paragraphs into ~chunk_chars windows; writes data/train.jsonl, data/val.jsonl.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter

from common import (compile_blocklist, load_config, load_index, read_story,
                    repo_path, title_matches, weight_for)


def included(entry: dict, cfg: dict) -> tuple[bool, str]:
    if entry["collaboration"]:
        return False, "collaboration/revision"
    if entry["year"] and entry["year"] < cfg["exclude_before_year"]:
        return False, "juvenilia"
    if title_matches(entry["title"], cfg["exclude_titles"]):
        return False, "excluded title"
    return True, ""


def chunk(paragraphs: list[str], size: int) -> list[str]:
    chunks, cur = [], ""
    for p in paragraphs:
        if cur and len(cur) + len(p) > size:
            chunks.append(cur)
            cur = ""
        cur = f"{cur}\n\n{p}" if cur else p
    if cur:
        chunks.append(cur)
    return chunks


def main():
    cfg = load_config()
    tcfg = cfg["train"]
    block = compile_blocklist(cfg)
    out = repo_path(cfg["dataset_dir"])

    train, val = [], []
    report = []          # (title, reason) for excluded works
    dropped = []         # (title, matched term, paragraph) for filtered paragraphs
    words_kept = words_seen = 0

    for e in load_index(cfg):
        ok, why = included(e, cfg)
        if not ok:
            report.append((e["title"], why))
            continue
        paras = [p for p in read_story(cfg, e).split("\n\n") if p.strip()]
        clean = []
        for p in paras:
            words_seen += len(p.split())
            m = block.search(p)
            if m:
                dropped.append((e["title"], m.group(0).lower(), p))
            else:
                clean.append(p)
                words_kept += len(p.split())
        w = weight_for(e["title"], cfg["upweight"])
        for c in chunk(clean, tcfg["chunk_chars"]):
            h = int(hashlib.sha1(c.encode()).hexdigest(), 16) % 1000
            target = val if h < tcfg["val_fraction"] * 1000 else train
            target.extend([{"text": c, "source": e["title"]}] * (w if target is train else 1))

    out.mkdir(parents=True, exist_ok=True)
    for name, rows in (("train.jsonl", train), ("val.jsonl", val)):
        with open(out / name, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Audit file: everything the racism filters removed, grouped by matched term.
    by_term = Counter(t for _, t, _ in dropped)
    with open(out / "filtered_out.md", "w", encoding="utf-8") as f:
        f.write("# Paragraphs removed by the racism filters\n\n")
        f.write(f"{len(dropped)} paragraphs removed "
                f"({words_seen - words_kept:,} of {words_seen:,} words in included stories).\n\n")
        f.write("| Matched term | Paragraphs |\n|---|---|\n")
        for t, n in by_term.most_common():
            f.write(f"| `{t}` | {n} |\n")
        f.write("\n## Excluded works\n\n")
        for title, why in report:
            f.write(f"- {title} — {why}\n")
        f.write("\n## Removed paragraphs\n\n")
        for title, term, p in dropped:
            f.write(f"- **{title}** (`{term}`): {p[:220]}{'…' if len(p) > 220 else ''}\n")

    print(f"train: {len(train)} chunks, val: {len(val)} chunks")
    print(f"excluded works: {len(report)}; filtered paragraphs: {len(dropped)} "
          f"({(words_seen - words_kept) / max(words_seen, 1):.1%} of words in included stories)")
    print(f"audit: {out / 'filtered_out.md'}")


if __name__ == "__main__":
    main()
