"""Shared helpers for the story tools: config loading, paths, title matching."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path(__file__).with_name("config.yaml")


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def repo_path(rel: str) -> Path:
    return REPO / rel


def norm_title(s: str) -> str:
    """Lower-case ASCII letters/digits only, so titles match across encodings."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


def title_matches(title: str, prefixes) -> bool:
    t = norm_title(title)
    return any(t.startswith(norm_title(p)) for p in prefixes)


def weight_for(title: str, weights: dict) -> int:
    t = norm_title(title)
    for prefix, w in weights.items():
        if t.startswith(norm_title(prefix)):
            return int(w)
    return 1


def compile_blocklist(cfg: dict) -> re.Pattern:
    """Slurs + ethnic/racial descriptors (config.yaml). Used for training and output."""
    patterns = list(cfg["blocklist"]) + list(cfg.get("descriptor_filter", []))
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)


def load_index(cfg: dict) -> list[dict]:
    with open(repo_path(cfg["corpus_dir"]) / "index.json", encoding="utf-8") as f:
        return json.load(f)


def read_story(cfg: dict, entry: dict) -> str:
    return (repo_path(cfg["corpus_dir"]) / entry["file"]).read_text(encoding="utf-8")
