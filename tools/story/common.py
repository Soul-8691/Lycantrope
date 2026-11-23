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


def dtype_kwarg(dtype) -> dict:
    """transformers renamed `torch_dtype` to `dtype` in 4.56; support both."""
    import transformers
    from packaging.version import Version
    new = Version(transformers.__version__) >= Version("4.56")
    return {"dtype": dtype} if new else {"torch_dtype": dtype}


def check_torchao() -> None:
    """Recent peft refuses to build LoRA layers if an *old* torchao is installed
    (Colab ships one). We never use torchao, so the fix is to remove it."""
    import sys
    from importlib.metadata import PackageNotFoundError, version
    try:
        v = version("torchao")
    except PackageNotFoundError:
        return
    from packaging.version import Version
    if Version(v) < Version("0.16.0"):
        sys.exit(f"torchao {v} is installed and recent peft rejects versions below 0.16.\n"
                 "This project doesn't use torchao. Remove it and re-run:\n"
                 "    pip uninstall -y torchao")


def find_adapter(adapter_dir: Path) -> Path | None:
    """The final adapter, or else the newest training checkpoint that holds one."""
    if (adapter_dir / "adapter_config.json").exists():
        return adapter_dir
    ckpts = sorted((adapter_dir / "checkpoints").glob("checkpoint-*"),
                   key=lambda p: int(p.name.split("-")[-1]) if p.name.split("-")[-1].isdigit() else -1)
    ckpts = [c for c in ckpts if (c / "adapter_config.json").exists()]
    return ckpts[-1] if ckpts else None


def compile_blocklist(cfg: dict) -> re.Pattern:
    """Slurs + ethnic/racial descriptors (config.yaml). Used for training and output."""
    patterns = list(cfg["blocklist"]) + list(cfg.get("descriptor_filter", []))
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)


def load_index(cfg: dict) -> list[dict]:
    with open(repo_path(cfg["corpus_dir"]) / "index.json", encoding="utf-8") as f:
        return json.load(f)


def read_story(cfg: dict, entry: dict) -> str:
    return (repo_path(cfg["corpus_dir"]) / entry["file"]).read_text(encoding="utf-8")
