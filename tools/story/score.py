"""Score prose for how Lovecraftian, how heroic, and how original it is.

    python tools/story/score.py STORY.md --paragraphs     # score each paragraph of the story
    python tools/story/score.py some_text.md               # score a whole file

Used by generate.py to rank candidates. Scores:
  lovecraft  cosine similarity to the corpus centroid (sentence embeddings)
  heroic     similarity to heroic tales minus similarity to bleak ones
  density    how close the signature-word rate is to Lovecraft's own (1 = same)
  copied     share of 8-word runs found verbatim in the corpus (want ~0)
  blocked    matched the slur / ethnic-descriptor lists in config.yaml -> rejected
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys

import numpy as np

from common import (compile_blocklist, load_config, load_index, read_story,
                    repo_path, title_matches)

WORD = re.compile(r"[a-z]+(?:-[a-z]+)*")
# No re.S here: with DOTALL, "^#+ .*$" would swallow everything after the first heading.
MARKUP = re.compile(r"<!--[\s\S]*?-->|\[\^\d+\]\([^)]*\)|^#+ .*$|^>\s?|^---$|[*_]", re.M)


def plain(text: str) -> str:
    return MARKUP.sub("", text).strip()


class Scorer:
    def __init__(self, cfg: dict | None = None):
        from sentence_transformers import SentenceTransformer

        self.cfg = cfg or load_config()
        self.block = compile_blocklist(self.cfg)
        self.n = self.cfg["score"]["copy_ngram"]
        data = repo_path(self.cfg["dataset_dir"])
        self.profile = json.loads((data / "style_profile.json").read_text(encoding="utf-8"))
        self.sig = {w["word"] for w in self.profile["signature_words"][:100]}
        self.model = SentenceTransformer(self.cfg["score"]["embed_model"])

        chunks = {}
        with open(data / "train.jsonl", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                chunks[r["text"]] = r["source"]
        cache = data / "score_cache.npz"
        if cache.exists():
            z = np.load(cache)
            self.c_all, self.c_hero, self.c_bleak = z["all"], z["hero"], z["bleak"]
        else:
            rng = random.Random(0)
            pick = lambda keys, k: rng.sample(keys, min(k, len(keys)))
            keys = list(chunks)
            hero = [c for c in keys if title_matches(chunks[c], self.cfg["heroic_refs"])]
            bleak = [c for c in keys if title_matches(chunks[c], self.cfg["bleak_refs"])]
            self.c_all = self._centroid(pick(keys, 500))
            self.c_hero = self._centroid(pick(hero, 300))
            self.c_bleak = self._centroid(pick(bleak, 300))
            np.savez(cache, all=self.c_all, hero=self.c_hero, bleak=self.c_bleak)

        self.ngrams = set()
        for e in load_index(self.cfg):
            if not e["collaboration"]:
                w = WORD.findall(read_story(self.cfg, e).lower())
                self.ngrams.update(hash(tuple(w[i:i + self.n])) for i in range(len(w) - self.n + 1))

    def _centroid(self, texts):
        v = self.model.encode(texts, normalize_embeddings=True).mean(axis=0)
        return v / np.linalg.norm(v)

    def score(self, text: str) -> dict:
        text = plain(text)
        hit = self.block.search(text)
        # The embedding model only reads ~256 tokens: embed 120-word pieces and average.
        toks = text.split()
        pieces = [" ".join(toks[i:i + 120]) for i in range(0, len(toks), 120)] or [""]
        v = self.model.encode(pieces, normalize_embeddings=True).mean(axis=0)
        v = v / (np.linalg.norm(v) or 1.0)
        words = WORD.findall(text.lower())
        grams = [hash(tuple(words[i:i + self.n])) for i in range(len(words) - self.n + 1)]
        copied = sum(g in self.ngrams for g in grams) / max(len(grams), 1)
        rate = sum(w in self.sig for w in words) / max(len(words), 1) * 1000
        target = self.profile["signature_rate_per_1k"]
        raw = max(0.0, 1 - abs(math.log((rate + 0.5) / (target + 0.5))) / 2)
        # A ~100-word paragraph is too small a sample to judge vocabulary density,
        # so shrink toward neutral (0.5) on short texts; full weight from 400 words.
        conf = min(1.0, len(words) / 400)
        density = conf * raw + (1 - conf) * 0.5
        lovecraft = float(v @ self.c_all)
        heroic = float(v @ self.c_hero - v @ self.c_bleak)
        heroic_n = min(1.0, max(0.0, 0.5 + 5 * heroic))
        total = 0.0 if hit else (0.4 * lovecraft + 0.4 * heroic_n + 0.2 * density
                                 - 2 * max(0.0, copied - 0.02))
        return {"total": round(total, 3), "lovecraft": round(lovecraft, 3),
                "heroic": round(heroic, 3), "density": round(density, 2),
                "copied": round(copied, 3), "blocked": hit.group(0) if hit else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--paragraphs", action="store_true", help="score each paragraph separately")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    text = open(args.file, encoding="utf-8").read()
    s = Scorer()
    if not args.paragraphs:
        print(json.dumps(s.score(text), indent=2))
        return
    rows = []
    for p in text.split("\n\n"):
        body = plain(p)
        if len(body.split()) >= 40:
            rows.append((s.score(body), body[:70]))
    for r, head in rows:
        flag = " BLOCKED:" + r["blocked"] if r["blocked"] else ""
        print(f"{r['total']:.3f}  lc={r['lovecraft']:.2f} hero={r['heroic']:+.3f} "
              f"dens={r['density']:.2f} copy={r['copied']:.2f}{flag}  {head}")
    if rows:
        print(f"\nmean total {np.mean([r['total'] for r, _ in rows]):.3f} over {len(rows)} paragraphs; "
              f"blocked: {sum(bool(r['blocked']) for r, _ in rows)}")


if __name__ == "__main__":
    main()
