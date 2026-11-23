"""Step 4: train a LoRA "style adapter" on the filtered Lovecraft corpus.

Needs a GPU. The free Google Colab T4 is enough (see train_colab.ipynb):

    python tools/story/train_lora.py                         # settings from config.yaml
    python tools/story/train_lora.py --out-dir /content/drive/MyDrive/dreamlands-lora
    python tools/story/train_lora.py --resume                # continue after a disconnect
    python tools/story/train_lora.py --max-steps 20          # quick smoke test

This is continued pre-training on raw prose (no instructions): the adapter learns
*how Lovecraft writes*, and generate.py steers *what* it writes with STORY.md
context and a seed sentence. Plot comes from the outline, not from the model.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from common import check_torchao, dtype_kwarg, load_config, repo_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", help="where to save the adapter (default: config train.adapter_dir)")
    ap.add_argument("--epochs", type=float)
    ap.add_argument("--max-steps", type=int, default=-1)
    ap.add_argument("--resume", action="store_true", help="resume from the last checkpoint in out-dir")
    ap.add_argument("--push-to-hub", metavar="USER/REPO", help="also upload the adapter (private) to Hugging Face")
    ap.add_argument("--base-model", help="override config train.base_model (e.g. a tiny model for testing)")
    args = ap.parse_args()
    check_torchao()  # fail in a second, not after downloading the model

    import torch
    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model
    from transformers import (AutoModelForCausalLM, AutoTokenizer,
                              DataCollatorForLanguageModeling, Trainer,
                              TrainingArguments)

    cfg = load_config()
    t = cfg["train"]
    if args.base_model:
        t["base_model"] = args.base_model
    out_dir = Path(args.out_dir) if args.out_dir else repo_path(t["adapter_dir"])
    data_dir = repo_path(cfg["dataset_dir"])

    if not torch.cuda.is_available():
        print("WARNING: no GPU found. Training a 1.5B model on CPU would take days; use Colab.")
    bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    fp16 = torch.cuda.is_available() and not bf16          # e.g. Colab's T4

    tok = AutoTokenizer.from_pretrained(t["base_model"])
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    ds = load_dataset("json", data_files={"train": str(data_dir / "train.jsonl"),
                                          "validation": str(data_dir / "val.jsonl")})
    block = t["block_size"]

    def tokenize(batch):
        return tok([x + tok.eos_token for x in batch["text"]])

    def group(batch):
        ids = [i for seq in batch["input_ids"] for i in seq]
        n = len(ids) // block * block
        chunks = [ids[i:i + block] for i in range(0, n, block)]
        return {"input_ids": chunks, "attention_mask": [[1] * block for _ in chunks]}

    ds = ds.map(tokenize, batched=True, remove_columns=ds["train"].column_names)
    ds = ds.map(group, batched=True, remove_columns=ds["train"].column_names)
    print(f"train blocks: {len(ds['train'])}, val blocks: {len(ds['validation'])} ({block} tokens each)")

    dtype = torch.bfloat16 if bf16 else (torch.float16 if fp16 else torch.float32)
    model = AutoModelForCausalLM.from_pretrained(t["base_model"], **dtype_kwarg(dtype))
    model.config.use_cache = False
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    model = get_peft_model(model, LoraConfig(
        r=t["lora_r"], lora_alpha=t["lora_alpha"], lora_dropout=t["lora_dropout"],
        target_modules="all-linear",  # every linear layer except the output head; works for any architecture
        task_type="CAUSAL_LM"))
    for p in model.parameters():          # keep trainable LoRA weights in fp32 for stable fp16 AMP
        if p.requires_grad:
            p.data = p.data.float()
    model.print_trainable_parameters()

    # Warm up for 3% of training. Given as a whole number of steps because
    # transformers 5 removed `warmup_ratio` (and int steps work in 4.x too).
    epochs = args.epochs or t["epochs"]
    per_epoch = math.ceil(len(ds["train"]) / (t["batch_size"] * t["grad_accum"]))
    total_steps = args.max_steps if args.max_steps > 0 else math.ceil(per_epoch * epochs)
    warmup = max(1, round(0.03 * total_steps))
    print(f"optimizer steps: {total_steps} ({per_epoch} per epoch), warmup: {warmup}")

    targs = TrainingArguments(
        output_dir=str(out_dir / "checkpoints"),
        per_device_train_batch_size=t["batch_size"],
        per_device_eval_batch_size=t["batch_size"],
        gradient_accumulation_steps=t["grad_accum"],
        num_train_epochs=epochs,
        max_steps=args.max_steps,
        learning_rate=t["learning_rate"],
        lr_scheduler_type="cosine",
        warmup_steps=warmup,
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="steps",
        save_steps=50,
        save_total_limit=2,
        bf16=bf16,
        fp16=fp16,
        report_to="none",
    )
    trainer = Trainer(model=model, args=targs, train_dataset=ds["train"], eval_dataset=ds["validation"],
                      data_collator=DataCollatorForLanguageModeling(tok, mlm=False))
    trainer.train(resume_from_checkpoint=True if args.resume else None)

    metrics = trainer.evaluate()
    metrics["perplexity"] = math.exp(metrics["eval_loss"])
    out_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(out_dir)
    tok.save_pretrained(out_dir)
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    (out_dir / "base_model.txt").write_text(t["base_model"])
    print(f"adapter saved to {out_dir}; validation perplexity {metrics['perplexity']:.2f}")

    if args.push_to_hub:
        model.push_to_hub(args.push_to_hub, private=True)
        tok.push_to_hub(args.push_to_hub, private=True)
        print(f"pushed to https://huggingface.co/{args.push_to_hub} (private)")


if __name__ == "__main__":
    main()
