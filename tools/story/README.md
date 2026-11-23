# Story tools

Scripts for writing The Dreamlands' story in H.P. Lovecraft's voice. They train a small "style adapter" on his public-domain fiction (the PDF in the repo root), draft prose for marked beats in [STORY.md](../../STORY.md), and score drafts for how Lovecraftian, heroic and original they are.

**The model supplies texture, not plot.** A 1.5B-parameter model trained on 360k words can imitate Lovecraft's sentences well, but it can't hold a plot together. The plot lives in STORY.md, written and edited by people (and Claude). The model drafts alternatives for individual passages, and a person chooses and edits them.

## Pipeline

| Step | Script | Where | Time |
|---|---|---|---|
| 1. Split the PDF into stories | `extract_corpus.py` | local CPU | ~1 min |
| 2. Filter and build the dataset | `build_dataset.py` | local CPU | seconds |
| 3. Measure his style | `style_profile.py` → [STYLE_PROFILE.md](STYLE_PROFILE.md) | local CPU | seconds |
| 4. Train the style adapter | `train_lora.py` (or [train_colab.ipynb](train_colab.ipynb)) | **GPU (free Colab T4)** | very roughly 1 hour |
| 5. Draft beats | `generate.py --all` | GPU (or slow CPU) | minutes |
| 6. Score text | `score.py STORY.md --paragraphs` | local CPU | ~1 min |
| 7. Check carets and filters | `check_annotations.py` | local CPU | instant |

```bash
pip install -r tools/story/requirements.txt          # steps 1-3, 7
python tools/story/extract_corpus.py
python tools/story/build_dataset.py
python tools/story/style_profile.py
python tools/story/check_annotations.py

pip install -r tools/story/requirements-ml.txt       # steps 4-6 (install torch first if local)
python tools/story/score.py STORY.md --paragraphs
```

To test the whole training and generation pipeline on a CPU in about a minute (the output is gibberish, because the model is random):

```bash
python tools/story/train_lora.py --base-model trl-internal-testing/tiny-Qwen2ForCausalLM-2.5 --max-steps 3 --out-dir /tmp/tiny
python tools/story/generate.py --beat p1-galley --n 2 --adapter /tmp/tiny
```

Generated data goes to `tools/story/data/` and `tools/story/out/`, which are git-ignored. Everything is rebuilt from the PDF.

## Racism safeguards

Lovecraft's fiction is full of racism, and none of it should reach the game. Three layers:

1. **Excluded works** (`config.yaml` → `exclude_titles`): *The Horror at Red Hook*, *Arthur Jermyn*, *The Street*, *He*, *Herbert West*, and *The Shadow over Innsmouth*. Collaborations and juvenilia are excluded too.
2. **Paragraph filters** (`blocklist` + `descriptor_filter`): any paragraph with a slur **or** an ethnic/racial descriptor is dropped, even when a given use is harmless. That's about 6% of the remaining words. Every removed paragraph is listed in `data/filtered_out.md` for audit.
3. **Output filters:** `score.py` rejects any generated candidate matching either list, and `check_annotations.py` fails if STORY.md or ANNOTATIONS.md match.

Filters catch words, not ideas. A person still reads every passage before it goes into STORY.md. If you spot something the filters missed, add the pattern to `config.yaml` and rebuild.

## Writing a beat

Mark a place in STORY.md with an invisible comment:

```markdown
<!-- beat id="p1-first-incursion" seed="The sky above the old burying-ground did not tear as cloth tears;" -->
```

`generate.py --beat p1-first-incursion` gives the model the story text before the comment plus the seed, writes six continuations, scores them, and saves them best-first to `out/candidates/p1-first-incursion.md`. Nothing is inserted automatically.

## Scores (score.py)

| Score | Meaning | Good |
|---|---|---|
| `lovecraft` | similarity to the corpus (sentence embeddings) | higher; STORY.md overall ≈ 0.81 |
| `heroic` | similarity to his heroic tales minus his bleakest | above 0 |
| `density` | signature-word rate vs. his own (1 = same) | near 1; low values = too plain, or parody |
| `copied` | share of 8-word runs copied from the corpus | ≈ 0 (deliberate quotes excepted) |
| `blocked` | matched a racism filter | must be `null` |

## Costs

**Nothing here needs a paid subscription.**

- Steps 1–3, 6 and 7 run on any PC.
- Step 4 needs a GPU. **Google Colab's free T4** is enough. Free sessions can disconnect, so the notebook saves to Google Drive and `--resume` continues.
- If Colab's free GPU isn't available, **Kaggle Notebooks** are also free (weekly GPU quota). A paid GPU on **Hugging Face** (Spaces hardware or Jobs; check their current pricing page) would cost a few dollars for one run, well within a $20 budget. A Hugging Face account to store the adapter privately (`--push-to-hub`) is free.
- The scorer downloads a small public embedding model from Hugging Face the first time. No account is needed.
