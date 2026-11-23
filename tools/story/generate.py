"""Step 5: draft prose in Lovecraft's voice for the beats marked in STORY.md.

    python tools/story/generate.py --list                 # show the beats in STORY.md
    python tools/story/generate.py --beat p1-first-incursion
    python tools/story/generate.py --all --n 8
    python tools/story/generate.py --prompt "The sky above Kingsport opened"   # free-form

Beats are HTML comments in STORY.md (invisible when rendered):

    <!-- beat id="p1-first-incursion" seed="The sky above the old burying-ground did not tear as cloth tears;" -->

For each beat the model sees the story text *before* the comment (so it keeps
continuity) followed by the seed sentence, and writes several continuations.
They are scored (score.py) and saved, best first, to out/candidates/<id>.md.
A human picks, edits, and pastes the best one into STORY.md. Nothing is
inserted automatically.

Runs on a GPU (Colab) in seconds per beat; on CPU it works but is slow
(roughly a minute or more per candidate for a 1.5B model).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from common import dtype_kwarg, find_adapter, load_config, repo_path
from score import plain

BEAT = re.compile(r"<!--\s*beat\s+(.*?)-->", re.S)
ATTR = re.compile(r'(\w+)="(.*?)"', re.S)


def find_beats(story: str) -> list[dict]:
    beats = []
    for m in BEAT.finditer(story):
        attrs = dict(ATTR.findall(m.group(1)))
        attrs["context"] = story[:m.start()]
        beats.append(attrs)
    return beats


def trim_to_sentence(text: str) -> str:
    cut = max(text.rfind(". "), text.rfind(".\n"), text.rfind("; "), text.rfind("!"), text.rfind("?"))
    end = text.rstrip()
    if end.endswith((".", "!", "?", "”")):
        return end
    return text[:cut + 1].rstrip() if cut > 0 else end


def load_model(cfg, adapter: str | None, no_adapter: bool):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    base = cfg["train"]["base_model"]
    adapter_dir = Path(adapter) if adapter else repo_path(cfg["train"]["adapter_dir"])
    found = None
    if not no_adapter:
        # Check before loading the 3 GB base model, so a missing adapter fails fast.
        found = find_adapter(adapter_dir)
        if found is None:
            sys.exit(
                f"No trained adapter at {adapter_dir} (and no checkpoints inside it).\n"
                "  - Did the full training cell finish? The adapter is written at the very end;\n"
                "    checkpoints are written every 50 steps under <out-dir>/checkpoints/.\n"
                "  - On Colab: was Google Drive mounted *before* training? Without it, the\n"
                "    output went to a temporary folder that vanished with the session.\n"
                "  - To try generation without training, pass --no-adapter.")
        if found != adapter_dir:
            print(f"Final adapter not found; using the latest checkpoint: {found}")
    if (adapter_dir / "base_model.txt").exists():
        base = (adapter_dir / "base_model.txt").read_text().strip()
    cuda = torch.cuda.is_available()
    tok = AutoTokenizer.from_pretrained(base)
    model = AutoModelForCausalLM.from_pretrained(
        base, **dtype_kwarg(torch.float16 if cuda else torch.float32))
    if found is not None:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, str(found))
    model.to("cuda" if cuda else "cpu").eval()
    return tok, model


def generate(tok, model, prompt: str, n: int, g: dict) -> list[str]:
    import torch
    ids = tok(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**ids, do_sample=True, num_return_sequences=n,
                             max_new_tokens=g["max_new_tokens"], temperature=g["temperature"],
                             top_p=g["top_p"], repetition_penalty=g["repetition_penalty"],
                             pad_token_id=tok.eos_token_id)
    new = out[:, ids["input_ids"].shape[1]:]
    return [trim_to_sentence(t) for t in tok.batch_decode(new, skip_special_tokens=True)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--beat", action="append", help="beat id (repeatable)")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--prompt", help="free-form opening text instead of a beat")
    ap.add_argument("--n", type=int, help="candidates per beat")
    ap.add_argument("--adapter", help="adapter directory (default: config train.adapter_dir)")
    ap.add_argument("--no-adapter", action="store_true", help="use the plain base model, for comparison")
    ap.add_argument("--no-score", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    cfg = load_config()
    g = cfg["generate"]
    n = args.n or g["candidates"]
    story = repo_path(cfg["story_file"]).read_text(encoding="utf-8")
    beats = find_beats(story)

    if args.list:
        for b in beats:
            print(f"{b.get('id', '?'):32} {b.get('seed', '')[:70]}")
        return

    if args.prompt:
        jobs = [{"id": "prompt", "seed": args.prompt, "context": ""}]
    else:
        wanted = set(args.beat or [])
        jobs = [b for b in beats if args.all or b.get("id") in wanted]
        if not jobs:
            sys.exit("No beats selected. Use --list, --beat ID, --all, or --prompt.")

    tok, model = load_model(cfg, args.adapter, args.no_adapter)
    scorer = None
    if not args.no_score:
        from score import Scorer
        scorer = Scorer(cfg)

    out_dir = repo_path(cfg["out_dir"]) / "candidates"
    out_dir.mkdir(parents=True, exist_ok=True)
    for job in jobs:
        context = plain(job["context"])[-g["context_chars"]:]
        prompt = (context + "\n\n" if context else "") + job["seed"]
        texts = [job["seed"] + " " + t for t in generate(tok, model, prompt, n, g)]
        rows = [(scorer.score(t) if scorer else {"total": 0}, t) for t in texts]
        rows.sort(key=lambda r: r[0]["total"], reverse=True)
        lines = [f"# Candidates for `{job['id']}`", "", f"Seed: *{job['seed']}*", ""]
        for i, (s, t) in enumerate(rows, 1):
            lines += [f"## {i}. score {s['total']}", "", f"`{s}`", "", t, ""]
        path = out_dir / f"{job['id']}.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        best = rows[0][0]
        print(f"{job['id']}: {len(rows)} candidates, best {best.get('total')} -> {path}")


if __name__ == "__main__":
    main()
