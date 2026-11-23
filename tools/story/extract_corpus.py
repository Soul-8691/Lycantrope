"""Step 1: split the Lovecraft PDF into one clean text file per story.

    python tools/story/extract_corpus.py

Reads the PDF's printed table of contents, maps printed page numbers to PDF
pages, and for each story removes running headers, page numbers, footnotes and
superscript markers, re-attaches the drop-cap letter, and rebuilds paragraphs
from line indentation. Writes tools/story/data/corpus/NNN_slug.txt and index.json.
"""
from __future__ import annotations

import json
import re
import statistics

import pymupdf

from common import load_config, norm_title, repo_path


def parse_contents(doc, first: int, last: int) -> list[dict]:
    lines = []
    for i in range(first, last + 1):
        lines += [l.strip() for l in doc[i].get_text().splitlines() if l.strip()]
    lines = [l for l in lines if l != "CONTENTS"]

    entries, i = [], 0
    while i < len(lines):
        title_parts = []
        while i < len(lines) and not re.fullmatch(r"\d+", lines[i]):
            title_parts.append(lines[i])
            i += 1
        if i >= len(lines):
            break
        page = int(lines[i]); i += 1
        date = lines[i] if i < len(lines) else ""; i += 1
        collab = ""
        if i < len(lines) and re.match(r"^(with|for) ", lines[i]):
            collab = lines[i]; i += 1
            while collab.endswith(" and") and i < len(lines):
                collab += " " + lines[i]; i += 1
        title = " ".join(title_parts)
        year = re.search(r"1[89]\d\d", date)
        entries.append({
            "title": title,
            "page": page,
            "date": date,
            "year": int(year.group()) if year else None,
            "collaborator": collab,
            "collaboration": bool(collab),
        })
    return entries


def page_lines(page):
    """Lines as (x0, text, size) with small (footnote/superscript) spans removed."""
    pieces = []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            spans = [s for s in l["spans"] if s["text"].strip()]
            if spans:
                pieces.append((l["bbox"], spans))
    if not pieces:
        return []
    med = statistics.median(s["size"] for _, spans in pieces for s in spans)
    # Drop caps are tall: order them by their top edge and never merge them.
    keyed = []
    for bbox, spans in pieces:
        big = max(s["size"] for s in spans) > med * 1.8
        keyed.append((bbox[1] if big else bbox[3], bbox[0], spans, big))
    # Justified lines can come back as several pieces on one baseline: merge them.
    keyed.sort(key=lambda p: (round(p[0]), p[1]))
    raw = []
    for y, x0, spans, big in keyed:
        if raw and not big and not raw[-1][3] and abs(raw[-1][2] - y) < 2.0:
            prev_x, prev_spans, _, _ = raw[-1]
            joiner = [{"text": " ", "size": spans[0]["size"]}]
            raw[-1] = (prev_x, prev_spans + joiner + spans, y, False)
        else:
            raw.append((x0, spans, y, big))
    raw = [(x0, spans) for x0, spans, _, _ in raw]
    sizes = [round(s["size"], 1) for _, spans in raw for s in spans for _ in s["text"]]
    body = statistics.mode(sizes)
    out = []
    for x0, spans in raw:
        kept = [s for s in spans if s["size"] >= body * 0.85 or s["size"] > body * 1.15]
        text = "".join(s["text"] for s in kept).strip()
        if not text:
            continue  # footnote line or superscript-only line
        size = max(s["size"] for s in kept)
        out.append((x0, text, size))
    return out


def is_header(text: str, title: str) -> bool:
    if text != text.upper():
        return False
    t, h = norm_title(title), norm_title(text)
    return bool(h) and (h in t or t in h)


def story_lines(doc, start: int, end: int, entry: dict) -> list[tuple[float, str]]:
    result = []
    for idx in range(start, end):
        lines = page_lines(doc[idx])
        if not lines:
            continue
        if re.fullmatch(r"\d+", lines[-1][1]):
            lines = lines[:-1]
        if idx == start:
            lines = strip_opening(lines, entry)
        elif lines and is_header(lines[0][1], entry["title"]):
            lines = lines[1:]
        # Normalise the margin per page (odd/even pages differ).
        body = [x for x, t, _ in lines if len(t) > 30]
        margin = min(body) if body else (min(x for x, _, _ in lines) if lines else 0)
        result += [(x - margin, t) for x, t, _ in lines]
    return reattach_dropcaps(result)


def reattach_dropcaps(lines, window: int = 80):
    """A drop cap can land away from its word (e.g. after an epigraph, before a
    section numeral like 'I.'). Glue it to the next line that starts lower-case."""
    out, pending = [], None
    for i, (x, t) in enumerate(lines):
        if i < window and re.fullmatch(r"[“\"‘']?[A-Z]", t):
            pending = t
            continue
        if pending and re.fullmatch(r"[IVXLC]+\.", t):
            out.append((-1, t))  # -1 = force a paragraph break
            continue
        if pending and t[:1].islower():
            t = pending + t
            x = -1
        elif pending:
            out.append((x, pending))
        pending = None
        out.append((x, t))
    return out


def strip_opening(lines, entry):
    """Remove drop cap, title and date on a story's first page; re-attach the drop cap."""
    dropcap = ""
    if lines and len(lines[0][1]) <= 2:
        dropcap = lines[0][1]
        lines = lines[1:]
    date_norm = norm_title(entry["date"])
    for i, (_, text, _) in enumerate(lines):
        if date_norm and norm_title(text) == date_norm:
            lines = lines[i + 1:]
            break
    else:  # no date line found: skip leading all-caps title lines
        while lines and lines[0][1] == lines[0][1].upper() and is_header(lines[0][1], entry["title"]):
            lines = lines[1:]
    if dropcap and lines:
        x, t, s = lines[0]
        lines[0] = (x, dropcap + t, s)
    return lines


def build_paragraphs(lines: list[tuple[float, str]]) -> list[str]:
    paras, cur, prev_indented = [], "", False
    for x, text in lines:
        if re.fullmatch(r"[IVXLC]+\.", text):  # section numeral: its own paragraph
            if cur:
                paras.append(cur)
            paras.append(text)
            cur, prev_indented = "", True
            continue
        indented = x > 8 or x < 0
        if cur and (x < 0 or (indented and not prev_indented)):
            paras.append(cur)
            cur = ""
        if not cur:
            cur = text
        elif cur.endswith(("-", "—", "–")):
            cur += text
        else:
            cur += " " + text
        prev_indented = indented
    if cur:
        paras.append(cur)
    return [re.sub(r"\s+", " ", p).strip() for p in paras if p.strip()]


def slugify(title: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", norm_title_keep_spaces(title))).strip("-")[:60]


def norm_title_keep_spaces(title: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower()
    return s


def main():
    cfg = load_config()
    doc = pymupdf.open(repo_path(cfg["pdf"]))
    first, last = cfg["contents_pages"]
    entries = parse_contents(doc, first, last)
    offset = cfg["pdf_page_offset"]

    out_dir = repo_path(cfg["corpus_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    for n, e in enumerate(entries):
        start = e["page"] + offset
        end = entries[n + 1]["page"] + offset if n + 1 < len(entries) else doc.page_count
        paras = build_paragraphs(story_lines(doc, start, end, e))
        text = "\n\n".join(paras) + "\n"
        e["file"] = f"{n:03d}_{slugify(e['title'])}.txt"
        e["pdf_pages"] = [start, end - 1]
        e["words"] = len(text.split())
        e["paragraphs"] = len(paras)
        (out_dir / e["file"]).write_text(text, encoding="utf-8")

    with open(out_dir / "index.json", "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    total = sum(e["words"] for e in entries)
    solo = sum(e["words"] for e in entries if not e["collaboration"])
    print(f"{len(entries)} works, {total:,} words ({solo:,} in Lovecraft's solo works) -> {out_dir}")


if __name__ == "__main__":
    main()
