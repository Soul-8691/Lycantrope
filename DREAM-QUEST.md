# DREAM-QUEST

> *"Three times Randolph Carter dreamed of the marvellous city, and three times was he snatched away while still he paused on the high terrace above it."*
> — H.P. Lovecraft, *The Dream-Quest of Unknown Kadath* (1927)

**Dream-Quest** is a 3D living-card game. Cards sit on a ritual table. When you play one, the creature climbs out of the card art, and you control it in real time. The setting, characters, and flavor text come from the public-domain fiction of H.P. Lovecraft, with help from machine learning trained on his complete works.

| | |
|---|---|
| **Genre** | Real-time card battler + roguelike deck-builder |
| **Platform** | Windows first (PyInstaller `.exe`), Linux/macOS later |
| **Price** | $5 on itch.io |
| **Language** | Python 3.12 + Cython (engine), Lua 5.4 via Lupa (cards and mods) |
| **Rendering** | pygame-ce (window, input, audio) + moderngl (OpenGL 3.3+) |
| **AI / ML** | HuggingFace `transformers` + `sentence-transformers` (story); stable-baselines3 / PyTorch (CPU opponent); scikit-learn + Gambit (balance analysis) |
| **Tools** | Tkinter + TkinterWeb card editor; NiceGUI (with PyWebView native mode) dashboard |
| **Tests** | pytest (+ Hypothesis for property tests) |

---

## Table of Contents

> All code examples are in [CODE_TEMPLATES.md](CODE_TEMPLATES.md).

1. [Things to Settle First](#1-things-to-settle-first)
2. [Plan by Phase](#2-plan-by-phase)
3. [Game Design](#3-game-design)
4. [Creative Ideas](#4-creative-ideas)
5. [Architecture](#5-architecture)
6. [Project Layout](#6-project-layout)
7. [Code Templates](#7-code-templates) → [CODE_TEMPLATES.md](CODE_TEMPLATES.md)
   - 7.1 [Build config (`pyproject.toml`, `setup.py`)](CODE_TEMPLATES.md#71-build-config)
   - 7.2 [Cython engine core](CODE_TEMPLATES.md#72-cython-engine-core-enginecorepyx)
   - 7.3 [Lua bridge (Lupa, sandboxed)](CODE_TEMPLATES.md#73-lua-bridge-enginescriptingpy)
   - 7.4 [Lua card definitions](CODE_TEMPLATES.md#74-lua-card-definitions)
   - 7.5 [Renderer (pygame + moderngl)](CODE_TEMPLATES.md#75-renderer-pygame--moderngl)
   - 7.6 [Main game loop](CODE_TEMPLATES.md#76-main-game-loop-mainpy)
   - 7.7 [Story pipeline (transformers + sentence-transformers)](CODE_TEMPLATES.md#77-story-pipeline)
   - 7.8 [RL opponent (gymnasium + stable-baselines3)](CODE_TEMPLATES.md#78-rl-opponent)
   - 7.9 [Balance analysis (scikit-learn + Gambit)](CODE_TEMPLATES.md#79-balance-analysis-scikit-learn--gambit)
   - 7.10 [Modding tools (Tkinter / NiceGUI / PyWebView)](CODE_TEMPLATES.md#710-modding-tools)
   - 7.11 [Tests (pytest)](CODE_TEMPLATES.md#711-tests-pytest)
   - 7.12 [Packaging (PyInstaller)](CODE_TEMPLATES.md#712-packaging-pyinstaller)
8. [Assets and Licensing](#8-assets-and-licensing)
9. [Releasing on itch.io](#9-releasing-on-itchio)
10. [Risks and How to Handle Them](#10-risks-and-how-to-handle-them)
11. [Ideas from the Call of Cthulhu RPG](#11-ideas-from-the-call-of-cthulhu-rpg)
12. [First-Person Combat: Skyrim × Bloodborne](#12-first-person-combat-skyrim--bloodborne)
13. [Smart Procedural Environments](#13-smart-procedural-environments)
14. [Beyond the Dreamlands: Waking-World Horrors](#14-beyond-the-dreamlands-waking-world-horrors)

---

## 1. Things to Settle First

These decisions affect everything that follows.

### 1.1 The name "Dream-Quest"
- The title comes from Lovecraft's *The Dream-Quest of Unknown Kadath*, which is a strong thematic fit.
- **However**, a well-known roguelike deck-builder called ***Dream Quest*** (Peter Whalen, 2014) already exists, and it was a major influence on *Slay the Spire*. A card game with almost the same name could confuse players and store search, and could cause trademark problems.
- **Recommendation:** keep "Dream-Quest" as the working title, but think about a distinguishing subtitle or a variant before launch, such as ***Dream-Quest: Unknown Kadath***, ***Kadath: A Dream-Quest***, or ***The Dreamlands Deck***. Search itch.io and Steam before you commit to store art.

### 1.2 Public-domain scope
- Lovecraft's own fiction is generally treated as public domain in the US. Characters he created are safe to use: Randolph Carter, Nyarlathotep, the Cats of Ulthar, Pickman, night-gaunts, and others.
- **Not automatically safe:** things added by later authors, such as August Derleth's "Elder Gods vs. Great Old Ones" framework, Chaosium's *Call of Cthulhu* RPG rules and terms (for example the "Sanity" *rules*, though not the word), and Fantasy Flight's *Arkham Horror* card designs.
- Game **mechanics** are not copyrightable, but names, card text, art, and some terms are. Avoid trademarked terms such as Wizards of the Coast's **"Tap"**. Use your own words, for example **"Spend," "Exhaust," or "Swoon."**

### 1.3 Scope
The stack in this document is large: Cython, Lua, moderngl, RL, LLMs, three GUI toolkits, and PyInstaller. **Build a vertical slice first:**
> One arena, 12 cards, 2 factions, one scripted CPU, no ML, no mod tools.

Add each other technology only once the core game loop is fun.

### 1.4 Shipping ML inside a $5 exe
Shipping PyTorch and transformers in a PyInstaller build adds **2–4 GB**. Plan instead to:
- **Generate story text offline** (at dev time), curate it, and ship it as JSON/Lua data.
- **Export the RL policy to ONNX** and ship `onnxruntime` (~15–50 MB), or a hand-written NumPy forward pass (~0 MB).
- Optionally offer a separate "Dreaming Engine" download later for live text generation.

---

## 2. Plan by Phase

| Phase | Goal | Deliverable | Key tech |
|---|---|---|---|
| **0. Foundations** | Repo, tooling, CI | `pyproject.toml`, pytest running, Cython building, Lupa hello-world | Cython, Lupa, pytest |
| **1. Corpus** | Clean Lovecraft text | `data/corpus/*.txt` split by story, plus metadata JSON | PyMuPDF |
| **2. Rules engine** | Headless, deterministic simulation | `engine/core.pyx` with fixed-tick world, Lua card hooks, replayable seeds | Cython, Lupa |
| **3. Vertical slice** | Playable 3D duel | One arena, 12 cards, scripted CPU, card-to-creature summon animation | pygame-ce, moderngl |
| **4. Story and flavor** | Lovecraftian voice | Fine-tuned small LM, embedding index, curated flavor text, event writing | transformers, sentence-transformers |
| **5. Roguelike layer** | Run structure | Dreamlands map, events, shops, relics ("Talismans"), save/load | Python + Lua data |
| **6. RL opponent** | CPU that learns | Gym env, MaskablePPO training, ONNX export, difficulty tiers | SB3, PyTorch, ONNX |
| **7. Balance** | Fair, varied meta | Win-rate dashboards, card-impact regression, matchup equilibria | scikit-learn, Gambit, NiceGUI |
| **8. Modding** | Community content | Card editor, mod loader, docs, sample mod | Tkinter, TkinterWeb, NiceGUI/PyWebView |
| **9. Polish** | Feel and juice | Shaders, audio, UI, accessibility, settings | moderngl, pygame.mixer |
| **10. Ship** | itch.io release | Windows `onedir` build, butler pipeline, store page, trailer | PyInstaller, butler |

**Rules that apply throughout:**
- The engine is **headless and deterministic**. Rendering only *reads* game state. This one rule makes testing, RL, replays, and netplay possible.
- **Content is data:** cards, events, and enemies are Lua or JSON, never hard-coded in Python.
- **Every bug gets a replay file** (`seed + action log`) and a pytest case.

---

## 3. Game Design

### 3.1 The core idea: living cards
1. **The Table.** The game takes place on a dark, candle-lit 3D ritual table (the *Altar*). Each side has a **hand** (fanned cards, close to the camera), a **deck** (a stack you draw from), and three to five **Rifts** (glowing sigil slots on the table).
2. **Summoning.** Drag a card onto a Rift. The card lies flat, its art *dissolves into a portal*, and the 3D creature **climbs out of the card**. The card frame remains as the creature's "soul anchor," a health bar on the table.
3. **Real time.** Both players spend **Lucidity** (the "mana"), which refills over time, so there are no turns. That makes it feel like a cross between Clash Royale and Magic: The Gathering.
4. **Possession (direct control).** At any moment you can **possess** one of your creatures: WASD/left stick to move, mouse/right stick to aim, and 1–3 for its abilities. Unpossessed creatures follow their Lua behavior script. Possessing costs a slow drain of **Sanity**, so you can't stay in control forever.
5. **Destruction.** When a creature dies, it is *dragged back into its card*, which burns and goes to the **Abyss** (the discard pile).

### 3.2 Resources

| Resource | Inspiration | Rules |
|---|---|---|
| **Lucidity** (Mana) | MTG mana / Clash elixir | Refills at about 1 per 2.5 s, capped at 10. Spent to play cards. |
| **Sanity** (HP + stress) | Darkest Dungeon stress, CoC | Your life total *and* your mind. At **0 you lose**. Crossing thresholds (75/50/25) gives an **Affliction** (bad) or a **Revelation** (good), as in Darkest Dungeon's resolve checks. |
| **Insight** | Bloodborne | Gained by witnessing horrors (enemy Great Old Ones, forbidden cards). High Insight **reveals hidden card text** and lets you play **Forbidden** cards, but enemies also become stronger and the arena warps. |
| **Doom** | Arkham Horror / CoC CCG | A shared clock. Certain cards add Doom. When Doom reaches its limit, the **Outer God awakens** and changes the match (sudden death). |

### 3.3 Card types

| Type | What it does |
|---|---|
| **Dreamer** | Your hero card (Randolph Carter, Kuranes, Richard Upton Pickman...). Gives a passive and one ultimate ability. Always on the table. |
| **Entity** | A creature that comes to life on a Rift and can be possessed. |
| **Rite** | An instant spell (fireball-like, AoE, buffs). Played with a targeting reticle in 3D space. |
| **Locale** | A field card that changes the whole arena (*The Enchanted Wood*, *Plateau of Leng*, *The Underworld*). Changes lighting, shaders, and rules. |
| **Talisman** | A persistent relic (Slay the Spire relics). Mainly found during runs. |
| **Forbidden** | A powerful card with hidden text until your Insight is high enough. Costs Sanity as well as Lucidity. |
| **Omen** | A face-down trap that triggers on a condition (Yu-Gi-Oh! trap cards). |

### 3.4 Keywords (original names, Lovecraftian flavor)
- **Eldritch** — Can't be targeted by Rites below a certain cost.
- **Swarm N** — Summons N small copies (zoogs, ghouls).
- **Whisper** — Triggers an effect when an *opponent's* card enters the Abyss.
- **Nameless** — Has no text until revealed; reveal it by paying Insight.
- **Dreamwalk** — Can move between Rifts by phasing through the table.
- **Unravel X** — When you play it, you lose X Sanity.
- **Hunger** — Gets +1/+1 each time something dies nearby.
- **Gibbering** — Each attack has a random extra effect drawn from a Lua table.
- **Ancient** — Can't be summoned until Doom ≥ N.
- **Ward** — Prevents the next instance of damage (an Elder Sign).

### 3.5 Factions (all from Lovecraft's Dreamlands and related tales)

| Faction | Playstyle | Example cards |
|---|---|---|
| **Cats of Ulthar** | Fast, evasive, protective; punishes aggression | *Cat of Ulthar*, *Saturnian Cat*, *The Elder Cat's Blessing* |
| **Zoogs of the Enchanted Wood** | Swarm, tricks, poison | *Zoog Scout*, *Moon-Tree Wine*, *Council of Zoogs* |
| **Ghouls & Ghasts** | Graveyard recursion; eats the Abyss | *Pickman, Ghoul-Lord*, *Ghast Pack*, *Vaults of Zin* |
| **Gugs** | Huge, slow, crushing tanks | *Gug Sentinel*, *Tower of Koth*, *Stone of the Gugs* |
| **Night-gaunts** | Silent abductions; remove units from the board | *Night-gaunt*, *Nodens' Summons*, *Ride to Ngranek* |
| **Moon-beasts & Men of Leng** | Mind control, slavery, Insight manipulation | *Moon-beast Overseer*, *High-Priest Not to Be Described*, *Black Galley* |
| **The Waking World** | Investigators, science, artifacts | *Randolph Carter*, *Professor Armitage*, *The Silver Key* |
| **Outer Gods** (boss-only, or Forbidden) | Raw cosmic power, warps rules | *Nyarlathotep, Crawling Chaos*, *Azathoth's Piping*, *Shining Trapezohedron* |

### 3.6 Roguelike run structure (Slay the Spire / Darkest Dungeon)
A run is a **descent through dream layers**, following Carter's journey:

```
 Layer 1  The Seventy Steps of Light Slumber  → Cavern of Flame (tutorial)
 Layer 2  The Enchanted Wood → Ulthar → Dylath-Leen
 Layer 3  The Moon (Black Galley) → Celephaïs → Ngranek
 Layer 4  The Underworld (Vaults of Zin, Gugs, Ghouls)
 Layer 5  Plateau of Leng → Inquanok
 Layer 6  Unknown Kadath — Boss: Nyarlathotep (who takes a different form each run)
```

- **Map nodes:** ⚔ Battle, 💀 Elite, ❓ Dream Event (AI-written), 🛒 Bazaar of Dylath-Leen, 🔥 Hearth (rest: heal Sanity *or* upgrade a card), 🗝 Gate (choose your next layer variant).
- **Darkest Dungeon-style persistence:** between runs you return to **Carter's Boston study**, a hub where unlocked cards, Dreamers, and lore are kept. Dreamers who go mad become **"Lost Dreamers,"** enemy cards in future runs.

---

## 4. Creative Ideas

1. **The card *is* the creature's life.** Instead of a floating HP bar, damage *tears and burns the physical card* on the table (a fragment shader with a dissolve noise threshold). You read the board by looking at the cards.
2. **Sanity distorts the UI, not just the numbers.** At low Sanity: card text slowly *rewrites itself* with AI-generated nonsense (from a pre-generated "madness" text pool), hand cards drift, colors shift, and fake enemy cards occasionally appear. Include an accessibility toggle to turn these effects off.
3. **Insight reveals true forms.** At high Insight, models swap to "true-form" variants, for example a vertex-shader displacement that adds tentacles, extra eyes, and shifting geometry. This works even with simple placeholder models.
4. **"The Necronomicon" as the collection screen.** The card collection is a leather book you page through in 3D. Unseen cards are smudged ink. The lore for each card is pulled by **sentence-transformers retrieval** from the real story passage that inspired it ("*Source: The Cats of Ulthar, ¶12*").
5. **Nyarlathotep as a learning boss.** The final boss uses the RL policy, *plus* a **player-modeling layer**: it records the player's most-played cards during the run and counters them ("The Crawling Chaos has seen your dreams."). Its form, and therefore its deck, changes each run: the Black Pharaoh, the Haunter of the Dark, the Bloated Woman, and others.
6. **Dream Events written in Lovecraft's voice.** Events are built from templates. The fine-tuned model writes many variants at dev time, sentence-transformers scores them for "Lovecraftian-ness" (similarity to the corpus centroid) and novelty (distance from existing events), and you curate the best.
7. **Locales as arena transformations.** Playing *The Underworld* sinks the table into darkness, and only creatures near candles are visible. *Plateau of Leng* adds a cold wind particle effect that pushes units sideways.
8. **The Silver Key mechanic.** A once-per-run Talisman that **rewinds the last 10 seconds** of a battle. This is easy to build because the engine is deterministic: keep snapshots in a ring buffer.
9. **Ghoul recursion is literal.** Ghouls can *dig through the table* into the Abyss (discard pile), and you watch them drag a card back up.
10. **Cats vs. Moon-beasts rivalry.** As in the book, cats get bonuses against Moon-beasts. Factions have built-in rivalries that give synergy and hate cards a story reason.
11. **The Dreamer's Journal.** Each run produces a short, AI-assisted **journal entry in Lovecraft's style** summarizing what happened, built from event logs plus template slots. Players can export it and share it.
12. **Mod-friendly "Mythos Packs."** Mods are folders of Lua + glTF + PNG files. Players can write their own Mythos (*Shadow over Innsmouth* pack: Deep Ones, Dagon; *At the Mountains of Madness* pack: Elder Things, shoggoths).
13. **Real-time "Ritual" combos.** Play three specific cards within a 4-second window to trigger a Ritual (a fighting-game-style combo for cards). The rhythm adds skill expression.
14. **Audio:** procedural, droning ambient that layers in dissonant tones as Doom rises. "The piping of Azathoth" is a flute line detuned in real time.

---

## 5. Architecture

```
                    ┌─────────────────────────────┐
                    │        main.py (loop)       │
                    │  fixed 20 Hz sim, 60+ FPS   │
                    └──────┬───────────────┬──────┘
                 inputs    │               │ read-only state
                           ▼               ▼
┌───────────────┐  ┌──────────────┐  ┌───────────────────────┐
│ Input / UI    │→ │ ENGINE       │  │ RENDERER              │
│ pygame events │  │ (Cython)     │  │ moderngl + pygame-ce  │
│ possess, drag │  │ World, Units │  │ cards, models, shaders│
└───────────────┘  │ Rules, RNG   │  │ interpolation, VFX    │
                   └──┬───────┬───┘  └───────────────────────┘
          hooks       │       │  actions/observations
                      ▼       ▼
          ┌───────────────┐  ┌─────────────────────────────┐
          │ SCRIPTING     │  │ AI OPPONENT                 │
          │ Lupa / Lua 5.4│  │ ONNX policy (from SB3/PPO)  │
          │ cards, mods   │  │ + scripted fallbacks        │
          │ (sandboxed)   │  │                             │
          └───────────────┘  └─────────────────────────────┘

   OFFLINE (dev only, never shipped in the exe):
   corpus/ → fine-tune LM → generate → embed/score → curate → data/story/*.json
   self-play → SB3 training → ONNX export → data/ai/*.onnx
   sim logs → scikit-learn / Gambit → balance reports (NiceGUI dashboard)
```

**Main rules:**
- **Determinism:** one seeded RNG (`PCG32` or `xorshift` in Cython) that the engine owns. Lua gets random numbers *only* through `game.rand()`. Never use `math.random`.
- **Fixed timestep:** the simulation advances at 20 Hz (50 ms ticks). The renderer interpolates between the previous and current snapshots so motion stays smooth at 144 Hz.
- **Command pattern:** everything the player or AI does becomes an `Action` record (`PlayCard`, `Possess`, `Move`, `UseAbility`). That makes replays, RL, and tests share the same code path.
- **Events:** the engine emits `Event`s (`UnitSummoned`, `DamageDealt`, `SanityChanged`...). The renderer and audio *subscribe* to them, and the engine never calls the renderer.

---

## 6. Project Layout

```
Dream-Quest/
├── DREAM-QUEST.md                 ← this file
├── pyproject.toml
├── setup.py                       ← Cython build
├── dreamquest.spec                ← PyInstaller spec
├── CREDITS.md                     ← every 3D model / sound / font + license
├── src/dreamquest/
│   ├── main.py                    ← entry point
│   ├── engine/
│   │   ├── core.pyx               ← World, Unit, step()  (Cython)
│   │   ├── core.pxd
│   │   ├── rng.pyx                ← deterministic PCG32
│   │   ├── actions.py             ← Action dataclasses
│   │   ├── events.py              ← Event bus
│   │   └── scripting.py           ← Lupa bridge + sandbox
│   ├── render/
│   │   ├── renderer.py            ← moderngl context, passes
│   │   ├── card_mesh.py
│   │   ├── model_loader.py        ← glTF via pygltflib / trimesh
│   │   ├── camera.py
│   │   └── shaders/
│   │       ├── card.vert / card.frag       ← dissolve / burn / rift
│   │       ├── creature.vert / creature.frag
│   │       └── post_madness.frag           ← sanity screen distortion
│   ├── game/
│   │   ├── run.py                 ← roguelike map, save/load
│   │   ├── deck.py
│   │   └── ui.py                  ← hand, drag & drop, HUD
│   ├── ai/
│   │   ├── policy.py              ← ONNX runtime inference
│   │   └── scripted.py            ← rule-based fallback / easy mode
│   └── modding/
│       └── loader.py              ← discovers mods/, validates manifests
├── content/                       ← shipped *next to* exe, moddable
│   ├── cards/
│   │   ├── core/                  ← *.lua card scripts
│   │   └── api.lua                ← documented helper API for card authors
│   ├── models/                    ← .glb
│   ├── textures/
│   ├── story/                     ← curated AI-assisted text (*.json)
│   └── ai/opponent_v1.onnx
├── mods/                          ← user mods (empty at ship, plus example_mod/)
├── tools/
│   ├── corpus/                    ← extract, clean, split the PDF
│   ├── story/                     ← finetune, generate, embed, score
│   ├── rl/                        ← gym env, train, export_onnx
│   ├── balance/                   ← sklearn + gambit analysis
│   └── modkit/                    ← Tkinter editor, NiceGUI dashboard
└── tests/
    ├── conftest.py
    ├── test_engine.py
    ├── test_cards_lua.py
    ├── test_determinism.py
    └── test_mod_sandbox.py
```

---

## 7. Code Templates

All code examples are in **[CODE_TEMPLATES.md](CODE_TEMPLATES.md)**. They're descriptive skeletons, not finished code. References like §7.3 elsewhere in this document point to the matching section there.

- [7.1 Build config](CODE_TEMPLATES.md#71-build-config)
- [7.2 Cython engine core (`engine/core.pyx`)](CODE_TEMPLATES.md#72-cython-engine-core-enginecorepyx)
- [7.3 Lua bridge (`engine/scripting.py`)](CODE_TEMPLATES.md#73-lua-bridge-enginescriptingpy)
- [7.4 Lua card definitions](CODE_TEMPLATES.md#74-lua-card-definitions)
- [7.5 Renderer (pygame + moderngl)](CODE_TEMPLATES.md#75-renderer-pygame--moderngl)
- [7.6 Main game loop (`main.py`)](CODE_TEMPLATES.md#76-main-game-loop-mainpy)
- [7.7 Story pipeline](CODE_TEMPLATES.md#77-story-pipeline)
- [7.8 RL opponent](CODE_TEMPLATES.md#78-rl-opponent)
- [7.9 Balance analysis (scikit-learn + Gambit)](CODE_TEMPLATES.md#79-balance-analysis-scikit-learn--gambit)
- [7.10 Modding tools](CODE_TEMPLATES.md#710-modding-tools)
- [7.11 Tests (pytest)](CODE_TEMPLATES.md#711-tests-pytest)
- [7.12 Packaging (PyInstaller)](CODE_TEMPLATES.md#712-packaging-pyinstaller)

---

## 8. Assets and Licensing

- **3D models (placeholders):** prefer **CC0** packs, which are safest for a paid game. Good sources include Quaternius, Kenney, KayKit, and itch.io's CC0 3D tag. Check *every* license. Some "free" itch.io assets forbid commercial use or redistribution in a moddable (extractable) format.
- **Format pipeline:** convert everything to **`.glb`** (glTF binary) in Blender and normalize scale and orientation. Load with `pygltflib` or `trimesh`, then upload to moderngl VAOs.
- **Make placeholders feel Lovecraftian cheaply:** dark palette, rim lighting, the vertex "writhing" shader (7.5), fog, and candlelight. Strong lighting and shaders can make generic fantasy models feel uncanny.
- **`CREDITS.md`:** list every asset with its author, URL, license, and the date you downloaded it. Keep this file from day one.
- **Card art:** start with stylized silhouettes or engraving-style public-domain illustrations (old woodcuts and 19th-century engravings), then commission art.
- **AI-generated text:** disclose AI use on the itch.io page. itch.io has AI-disclosure fields, and many players care about this.
- **Your code license:** consider releasing the **Lua card API and mod kit** under a permissive license (MIT) while keeping the game itself proprietary.

---

## 9. Releasing on itch.io

1. **Devlog early.** Post GIFs of cards coming to life. That effect is the hook.
2. **Free demo** (Layer 1–2 of a run, 2 factions) before the $5 paid release. Use itch.io's "pay what you want with a minimum" or a fixed $5.
3. **Upload with `butler`** (itch.io's CLI): `butler push dist/DreamQuest user/dream-quest:windows`. This gives players delta patches automatically.
4. **Store page checklist:** 5+ screenshots, a 30–60 s trailer, tags (`card-game`, `deckbuilder`, `lovecraft`, `horror`, `roguelike`, `moddable`), system requirements (OpenGL 3.3), AI disclosure, and credits.
5. **Code-sign or document SmartScreen.** Unsigned PyInstaller exes trigger Windows SmartScreen warnings. Explain "More info → Run anyway" on the page, or buy a code-signing certificate later.
6. **Mod showcase:** a `mods/` community thread on the itch.io page, plus the sample mod.

---

## 10. Risks and How to Handle Them

| Risk | Mitigation |
|---|---|
| Too many technologies at once | Vertical slice first (§1.3). Add ML, RL, and modding only after the core loop is fun. |
| Real-time + RL is hard to train | Low decision rate (5 Hz), action masking, scripted opponents to start curriculum, league self-play. Keep scripted AI as a fallback. |
| Huge exe from ML libraries | Ship text as JSON and the AI as ONNX. Exclude torch and transformers in the spec. |
| Malicious mods | Lupa sandbox (§7.3): no `os`/`io`/`require`/`python`, memory cap, instruction budget, attribute filter. Tested in `test_mod_sandbox.py`. |
| Non-determinism bugs | A single engine-owned RNG, fixed timestep, no `math.random`, Hypothesis determinism test. |
| Cython build friction on Windows | Install "MSVC Build Tools (C++)". Keep a pure-Python fallback (`core.py`) during early development. Only Cythonize hot paths once profiling shows the need. |
| AI-text quality | Human curation is mandatory. Use the LM as a co-writer, score with embeddings, and link lore back to real Lovecraft passages. |
| Name collision with *Dream Quest* (2014) | Consider a subtitle or variant before launch (§1.1). |
| Asset licenses | CC0-first, `CREDITS.md` from day one, re-check before release. |

---

---

## 11. Ideas from the Call of Cthulhu RPG

Chaosium's *Call of Cthulhu* (1981–today, now in its 7th edition) is the tabletop RPG that defined how Lovecraftian *games* feel: fragile investigators, sanity as a resource you spend, and knowledge that destroys you. Many of its ideas carry over well to a real-time card game.

### 11.1 What you can and can't take

| ✅ Safe to borrow (game mechanics and general ideas) | ❌ Avoid (Chaosium's protected expression and trademarks) |
|---|---|
| Roll-under percentile checks with success tiers | The name **"Call of Cthulhu"** on your store page, title, or marketing in a way that implies affiliation |
| Sanity that drops when you witness horrors and comes back slowly | Copying rulebook text, tables, Sanity-loss values, or monster stat blocks word for word |
| Knowledge of the Mythos lowering maximum sanity | Chaosium's art, logos, trade dress, or character sheet layout |
| Pushing a failed roll at a risk | Chaosium's published scenarios (*Masks of Nyarlathotep*, *The Haunting*, etc.) and the NPCs they invented |
| Skills that improve when used | Their exact term lists ("Cthulhu Mythos skill", "Keeper", "Bout of Madness"). Rename them in your own words, as below. |

> **Note:** Game mechanics are not copyrightable in the US, but their *written expression* is. Chaosium has also released its underlying **Basic Roleplaying (BRP)** system under the **ORC License**. If you ever want to use BRP terms or structures directly, read the current ORC terms and Chaosium's notice first. Following those terms is safer than guessing. Everything below is renamed and adapted so you don't need it.

### 11.2 Mechanics to adapt

| CoC RPG idea | Dream-Quest version | Where it fits |
|---|---|---|
| **Percentile (d100) skill checks** with Regular / Hard / Extreme success | **Omens:** every ability on a card has a **Skill %**. When it fires, a small bone die tumbles above the creature: **Fumble** (96–100), **Fail**, **Success** (≤ skill), **Strong** (≤ ½ skill), **Sublime** (≤ ⅕ skill). Higher tiers add bonus effects in Lua. | Every Entity and Rite |
| **Bonus / penalty dice** | **Favor / Dread dice:** roll two tens digits and keep the better (Favor) or worse (Dread). Created by Locales, flanking, darkness, and Afflictions. | Combat, Locales |
| **Pushing a roll** | **Press On:** after a failed ability, you have 1.5 s to press it again for a reroll. If the reroll *also* fails, a **Dire Consequence** fires (drawn from a Lua table, e.g. the creature turns on you, loses its card, or you lose Sanity). This adds real-time risk and reward. | Possession controls |
| **Luck points** (spend to adjust a roll) | **Fortune:** a per-run pool. Spend Fortune points one-for-one to drop a die result just under a success threshold. Fortune doesn't refill in battle, only at Hearths. | Run-level resource |
| **Sanity loss on witnessing horror** (smaller on a passed check, larger on a failed one) | **Horror rating** on Entity cards, written `1 / 1d6`. When an enemy Horror is **revealed** (summoned or turned face-up), you make a **Composure check** against your Sanity. Pass: lose the small number. Fail: lose the rolled number. | All Mythos Entities |
| **Becoming used to horrors** | **Familiarity:** the Sanity you can lose from one *kind* of creature in a single battle is capped, so the third night-gaunt is less shocking than the first. | Composure checks |
| **Temporary and indefinite insanity** (big losses at once, or a lot in one day) | **Fractures:** losing **5+ Sanity in one hit** (with a failed Intellect check) causes a **Fracture**, a short real-time madness effect (see 11.3). Losing **⅕ of your current Sanity in one battle** gives a lasting **Affliction** for the rest of the run, like Darkest Dungeon. | Ties into §3.2 Sanity thresholds |
| **Mythos knowledge lowers max Sanity** (max SAN = 99 − Mythos) | **Forbidden Lore:** your **Insight** (§3.2) *also* lowers your maximum Sanity: **max Sanity = 100 − 5 × Insight**. Knowledge makes you stronger and more fragile at once, which combines Bloodborne and CoC neatly. | Insight system |
| **Characteristics** (STR, CON, DEX, INT, POW...) | **Dreamer attributes:** *Vigor, Grace, Intellect, Will, Presence*. Will sets Composure checks, Intellect sets Fracture checks and Tome reading, Presence affects Bazaar prices. | Dreamer cards |
| **Occupations and skill points** | **Waking Lives:** each Dreamer has an occupation (Antiquarian, Professor, Painter, Sailor, Dilettante, Occultist) that sets their starting deck, skill bonuses, and one unique card. | Character select |
| **Backstory** (ideology, significant people, treasured possessions...) | **Anchors:** each Dreamer has 3 Anchors (*"My grey cat from Ulthar"*, *"The old house on Benefit Street"*, *"Faith in reason"*). An Anchor can be **sacrificed once** to fully pass a Composure check. Madness can **corrupt** an Anchor, turning it into a liability (inspired by CoC changing a character's backstory after insanity). | Dreamer cards, run events |
| **Skill improvement checks** (successful skills get a mark, then you roll to improve) | **Marks of Experience:** a card that rolls a Success or better in battle gets a mark. At a Hearth, every marked card rolls d100. If the roll is **above** its skill, it improves (+1d10%). Weak cards improve faster, which makes a nice comeback mechanic. | Hearth rest nodes |
| **Mythos tomes** (weeks of reading, Sanity loss, spells learned) | **Tomes:** Talisman-like items found during runs. Reading a Tome takes **3 map nodes**. When finished: gain Insight, lose Sanity, and add a spell (Rite) card to your deck. Some Tomes have hidden **"Translation"** stages. | Map, Talismans |
| **Casting spells** costs magic points and Sanity | **Rites of the Old Ones:** powerful Rites cost Lucidity **and** Sanity. A failed casting roll still costs the Sanity. | Forbidden cards |
| **Dodge or Fight Back** when attacked | **Reaction window:** when a possessed creature is attacked, you have ~0.3 s to press **Dodge** (dodge roll) or **Riposte** (counter-attack roll), a Bloodborne-style parry window. Unpossessed creatures pick a reaction automatically through their Lua script. | Real-time combat |
| **Chases** | **Pursuit nodes:** a short real-time map event where your Dreamer card runs across a scrolling board of hazard cards while something follows. Speed checks, obstacles, and Fortune all matter. | Map event type |
| **Clues and investigation** | **Clues:** some map nodes give Clues. Clues **weaken the final boss** or **reveal which form Nyarlathotep will take** (§4 idea 5), so investigation pays off strategically, not just as flavor. | Run structure |
| **The Game Master runs the world** | **The Dreamwarden:** a hidden **AI director** that watches tension (your Sanity, Doom, recent losses) and adjusts pacing: when to start an ambush, when to allow a quiet Hearth, and which events to show. It narrates in a Lovecraftian voice using pre-generated text (§7.7). | Run/event system |
| **Handouts** (newspaper clippings, letters, diaries) | **Found Documents:** physical-looking papers that show up during runs: letters, telegrams, diary pages, and clippings, rendered on an aged-paper shader. AI-assisted, curated text. Each document may contain a Clue. | Collection book, map events |
| **Credit Rating** | **Standing:** your Dreamer's wealth and status in the Waking World. It sets the starting gold and Bazaar discounts, and some Waking-World events check it. | Dreamer attributes |
| **Settings in different eras** (1890s, 1920s, modern) | **Dream Eras:** unlockable run modifiers that change card pools and visuals: *Gaslight Dreams* (Victorian), *The Jazz-Age Sleep* (default), *Modern Nightmares*. | Late-game replayability |
| **Investigators die often** | Your roguelike already fits this. On death, a Dreamer can become a **"Lost Dreamer"** enemy in a later run (§3.6). Their final **Found Document** can be found later. | Meta-progression |

### 11.3 Fractures (short-lived real-time madness)

When a **Fracture** happens, roll on this table, which is stored as editable Lua data so it can be modded:

| d10 | Fracture | Real-time effect (8–12 s) |
|---|---|---|
| 1 | **Amnesia** | Your hand is face-down; you play cards from memory. |
| 2 | **Flight** | Your possessed creature runs away from the nearest enemy. You can't steer it. |
| 3 | **Hysteria** | Screen shake; the cursor jitters; Lucidity regenerates 50% faster (manic energy). |
| 4 | **Paranoia** | Fake enemy cards appear on empty Rifts. They're harmless, but the CPU's real cards hide among them. |
| 5 | **Catatonia** | You can't possess anything; creatures run on their scripts only. |
| 6 | **Violent Outburst** | Your possessed creature deals double damage to *everything* near it, including allies. |
| 7 | **Phobia** (permanent this run) | You pick up a **Phobia** of the creature type that caused it. Seeing that type always costs +1 Sanity. |
| 8 | **Mania** (permanent this run) | You pick up a **Mania**: a compulsion, such as "must play a card every 6 s or lose 2 Sanity". |
| 9 | **Whispers** | Card text rewrites itself with madness text (§4 idea 2), and one card's *real* text changes for the rest of the battle. |
| 10 | **Revelation** | *Good:* gain 2 Insight and see the CPU's hand for the rest of the battle (with the max-Sanity cost from Forbidden Lore). |

### 11.4 Code template: checks, Composure, Fractures

The code for this section is in **[CODE_TEMPLATES.md §11.4](CODE_TEMPLATES.md#114-code-template-checks-composure-fractures)**.

### 11.5 Updates to the earlier plan

- **§3.2 Resources:** add **Fortune** (per run) and the **max-Sanity cap from Insight**.
- **§3.3 Card types:** add **Tome** (a Talisman read over several map nodes) and **Found Document** (a collectible that holds a Clue).
- **§3.6 Run map:** add **🔍 Investigation** (Clues and Found Documents), **🏃 Pursuit** (chase), and **📖 Study** (keep reading a Tome) node types.
- **§7.8 RL observation:** add the Fortune, Familiarity, active Fracture, and Anchors state so the CPU learns to play around madness. Use the same `check()` code path for the CPU, so it gets no hidden advantages.
- **§7.10 Card Forge:** add a **Skill %** field per ability, a **Horror** field (`small / big`), and a **tier preview** that rolls 1,000 simulated checks and shows the outcome distribution.
- **§9 Store page:** describe the game as *"inspired by classic tabletop horror RPGs and Lovecraft's Dreamlands."* Don't use the *Call of Cthulhu* name in the title, tags, or capsule art.

---

## 12. First-Person Combat: Skyrim × Bloodborne

**The pitch:** you fight from *inside* the cards. From **Skyrim** comes first-person immersion: a separate action for each hand, power attacks, stealth, and getting better at what you use. From **Bloodborne** comes aggression: no shields, dodging instead of blocking, winning back lost health by hitting back, and parry-into-critical. On top of that, **you can switch between your units at any moment**, and most of them are monsters.

> **Naming note:** as with Chaosium, borrow the *mechanics* and invent your own terms. Avoid "Rally," "Visceral Attack," "Blood Echoes," "Trick Weapon," "Hunter," "Shout," "Thu'um," "Dragonborn," and so on. This section uses original names throughout.

### 12.1 Two scales: the Altar and the Dream

| Layer | View | What you do |
|---|---|---|
| **Altar View** | Third-person, overhead, tilt-shift "miniature" look | Play cards onto Rifts, see the whole board, plan. Time runs at **35% speed** while you're here (*Dream-Slow*), so planning doesn't become a pause exploit. |
| **Dream View** | **First-person, inside a creature** | Fight up close. Card play is limited to a quick radial wheel. |

- **The Descent:** the camera drops from the table into the card's portal, through swirling art, and opens behind the creature's eyes in about 0.6 s. The tabletop *is* the arena: at full scale, candles are towers, the tablecloth folds are hills, and spilled ink is a black lake.
- **Ascend** (hold `Tab`): pull back up to the Altar. Your former host keeps fighting on its Lua script.

### 12.2 Soul Leap: switch freely between units

Switching is **instant and free** (no Lucidity cost, no cooldown), so the skill is in *when* and *where* you switch.

| Input | Leap |
|---|---|
| `1`–`5` | Leap to the unit on that Rift |
| `Q` / `E` | Cycle to the previous or next ally |
| **Look at a unit + `F`** | **Sight Leap:** jump into whatever you're looking at, if it's in line of sight |
| `Tab` (hold) | Ascend to the Altar |

**What makes switching deep, not just convenient:**
- **Chorus Chains (cross-unit combos):** land a hit with one unit, leap, and land a hit with another within **1.5 s**. Each link in the chain raises a **Chorus multiplier** (×1.1, ×1.25, ×1.5, up to ×2.0). For example: Gug knocks an enemy up → leap to a Night-gaunt to catch it mid-air → leap to a Ghoul to finish it on landing. This is the game's signature skill.
- **Echo Orders:** the unit you leave repeats your **last action** for 2 s (keeps attacking, keeps running, keeps casting). That lets you set up two things at once.
- **Death Throes:** if your host dies while you're inside it, time slows to 20% for 1.5 s. Leap to a new host before it ends, or get thrown back to the Altar and take **Sanity damage** for "dying in a dream."
- **Dominate (late game, Moon-beast/Leng faction or high Insight):** Sight Leap into a **staggered enemy** to control it for 6 s. When it ends, the enemy takes the damage its own allies dealt it.
- **Possession cost revised:** possessing **human** Dreamers is free. Possessing a **monster** slowly drains Sanity based on its **Horror rating** (§11.2). Alien minds wear you down, so how long you stay inside the big monsters is a decision.

### 12.3 Bloodborne-style aggression

| Mechanic (original name) | How it works | Why it matters |
|---|---|---|
| **Reclaim** | When you take damage, part of the lost HP stays as a **fading orange segment** for 3 s. Hitting enemies during that time wins it back. | Getting hit makes you want to attack, not retreat. |
| **Resolve Reclaim** | The same thing for **Sanity**: Sanity lost to a Horror reveal can be reclaimed by **killing** that Horror within 5 s. | Face your fears, literally. |
| **No shields; Quickstep instead** | Every creature has a fast, low-stamina dodge with invincibility frames, and each one is **different** (see 12.5). | Movement *is* defense. |
| **Severance** (parry → critical) | Hit an enemy with your off-hand (a Rite, a gunshot, an Elder Sign flash) **during its attack wind-up** to stagger it, then press attack for a **Severance** critical: a short close-up finisher with heavy hitstop. | High risk, high reward, and very satisfying. |
| **Frenzy meter** | Builds with each hit and drains when you're passive. At full: +30% damage and faster stamina, but you take +30% damage and slowly lose Sanity. | Keeps you pushing forward. |
| **Shifting Forms** | Many monsters have **two stances** you can switch between mid-combo (Ghoul upright ↔ ghoul on all fours; Nyarlathotep between his forms). A transform attack moves smoothly between moveset A and B. | Gives you a deeper moveset to master without needing more weapons. |
| **Generous stamina, tight windows** | Stamina regenerates quickly, and enemies have readable but short attack wind-ups. | Fast, readable duels. |

### 12.4 Skyrim-style first-person features

- **One hand for weapons, one for cards.** Right hand (`LMB`) is the creature's natural weapon (claws, maw, talons). Left hand (`RMB`) holds a **card**: Rites are *cast from the hand* in first person, like spells. For monsters, "hands" are whatever limbs they have: a Gug's forearm, a Moon-beast's snout-tentacles.
- **Power attacks:** hold attack for a slower, heavier strike that stuns. Direction plus a power attack gives different moves (forward = lunge, backward = sweep).
- **Utterances:** each Dreamer and monster type knows short **eldritch words** (original phrases in Lovecraftian style, written in an "Aklo-like" invented script). Press `Z` for a cone effect with a long cooldown: cats yowl (fear), Gugs give a sub-bass roar (knockdown), and a Dreamer speaks a word that dispels Wards.
- **Stealth and sneak attacks:** crouch to sneak. A half-open **eye indicator** shows how detected you are. Darkness matters: **candles on the table are light sources**, and Locales like *The Underworld* make stealth builds shine. Sneak attacks do ×3 damage (×6 for Cats and Night-gaunts).
- **Learn by doing:** each creature's *moves* get better with use (a Cat's pounce gets faster after many successful pounces). This ties into **Marks of Experience** (§11.2).
- **Quick wheel:** hold `G` for a radial menu of your hand. Time slows (*Dream-Slow*) and you can play a card onto a Rift without Ascending.
- **Finisher close-ups:** killing blows sometimes switch to a 0.8 s close-up of the kill. Keep them short and make them skippable in settings.
- **Optional third person** (`V`), mainly for large creatures (Gugs) and to help with motion sickness.

### 12.5 Playing as monsters: every body feels different

Each creature changes **camera height, FOV, movement, senses, and dodge**. The *senses* in particular should make each monster feel inhuman. Each one gets its own post-processing shader.

| Creature | Camera / body | Movement and dodge | Senses (screen shader) | Signature move |
|---|---|---|---|---|
| **Dreamer (human)** | Eye height 1.7 m, FOV 80 | Run, sprint; *sidestep* dodge | Normal vision. The **lantern** is a cone of light. | Revolver parry (Severance), Elder Sign flash |
| **Cat of Ulthar** | 0.3 m, FOV 100, fast head-bob | Wall-jump, pounce; *twist-flip* dodge | **Darkvision:** dark areas lift to a blue-gray. Enemies' heartbeats pulse. | Pounce-and-pin (stuns, rides the target) |
| **Zoog (Swarm)** | 0.15 m, FOV 110; everything looks huge | Skitter; *scatter* dodge | Sharp but **fish-eye** view | **Swarm hopping:** your Swarm copies are leap targets on a 0.1 s cycle, letting you blink around like a swarm |
| **Ghoul** | 1.4 m, hunched; switches to all fours | Climb walls and the table legs; *burrow* dodge (goes under the tablecloth) | **Scent trails:** wounded enemies leave glowing red trails | Eat a fallen unit's card to heal (graveyard recursion, §3.5) |
| **Night-gaunt** | 2.0 m, **flight** model (pitch/roll), FOV 95 | Fly, glide, dive; *wing-fold* dodge | **Faceless:** no eyes, so you see by **echo-outlines**. Edges pulse with sound, there are no textures, and anything silent is invisible. | Silent Abduction (§11.4): grab, carry, drop |
| **Gug** | 6 m, slow camera, heavy screen shake | Lumbering; no dodge, **brace** instead (armor frames) | Low angle, wide view; small units look like vermin | Vertical-mouth bite that grabs and swallows a small unit |
| **Moon-beast** | 2.5 m, slightly tilted, slippery | Slithering glide; *melt* dodge | **Vibration sense:** footsteps show as ripples on the ground, even through walls | Tentacle snout lash; **Dominate** (12.2) |
| **Nyarlathotep** (boss, rarely playable) | Changes with form | Each form has a different moveset | Reality-warp shader; the HUD **lies** | Form shift mid-combo (Shifting Forms) |

**Instinct Prompts:** monsters have urges. Sometimes a prompt flashes on screen (*"FEED"*, *"FLEE THE LIGHT"*, *"HUNT THE SMALL ONE"*). **Follow it** within 2 s for a temporary buff, or **resist it** to keep a little Sanity. This keeps reminding you that you're playing as something that isn't you.

### 12.6 The CPU in a first-person action game

Training one RL policy for both strategy *and* frame-precise melee isn't practical. Split it into layers:

| Layer | Decides | Tech |
|---|---|---|
| **Commander** (macro, 5 Hz) | Which card to play, which unit to possess, which target to focus, when to Ascend | MaskablePPO → ONNX (§7.8) |
| **Duelist** (micro, 60 Hz) | The possessed unit's attacks, dodges, parry attempts | Behavior tree + utility scoring in Lua per creature. Optionally a small PPO policy trained only on 1v1 duels |
| **Echo / unpossessed units** | Basic aggression and positioning | Each card's `on_tick` Lua script |

Difficulty should mostly come from **Duelist reaction time** and **parry accuracy** (e.g. *Dreamer* 400 ms / 10%, *Elder* 180 ms / 45%). Don't just add more HP, because Bloodborne-style fights feel fair only when enemies follow the same rules you do.

### 12.7 Technical changes this requires

- **Simulation rate:** raise the fixed tick from **20 Hz to 60 Hz** (`TICK_DT = 1/60`). Melee wind-ups, dodges, and parry windows need about 16 ms precision. RL decisions stay at about 5 Hz by stepping 12 ticks per decision.
- **Frame data:** describe every attack in **Lua as frame data** (wind-up, active, recovery, hitbox shape, damage, poise damage, parry window). This is how fighting games do it, it's very moddable, and it can be tested.
- **Hit detection:** capsule-vs-capsule and swept-arc tests in Cython. A spatial hash grid keeps it cheap with dozens of units.
- **Input buffering:** buffer attack and dodge presses for about 150 ms so combos feel responsive.
- **Hitstop and feel:** freeze both units for 50–90 ms on heavy hits, plus camera shake, a short FOV punch, and a loud sound. This matters more for "aggressive" than anything else.
- **First-person rendering:** draw the world, then **clear depth and draw the viewmodel** (the creature's limbs) with its own FOV and near plane so claws never clip into walls.
- **Mouse:** use `pygame.mouse.set_relative_mode(True)` (pygame-ce) for raw mouse look. Support controllers through `pygame.joystick`.
- **Animation:** placeholder models from itch.io often come with *rigged* animations (glTF skins). Use GPU skinning in a vertex shader (joint matrices in a uniform buffer). If a model has no rig, procedural bobbing and lunging is a fine stand-in.
- **Determinism is still required:** mouse look is converted to a quantized yaw/pitch **inside the Action**, so replays and Silver-Key rewinds (§4 idea 8) still work.
- **Comfort settings:** FOV slider, head-bob toggle, reduced camera shake, a third-person option for every creature, and an "Echolocation shader intensity" slider.

### 12.8 Code template

The code for this section is in **[CODE_TEMPLATES.md §12.8](CODE_TEMPLATES.md#128-code-template-first-person-combat)**.

### 12.9 Updates to the earlier plan

- **§1.3 Vertical slice:** the slice must now prove **combat feel**: one Dreamer, Ghoul, Cat, and Gug fighting with gray-box capsules in first person, with Soul Leap, Reclaim, and Severance working. If that isn't fun, nothing else will save the game. Build this **before** the card table.
- **§3.1 Living cards:** "Possession" becomes **Soul Leap** (free switching). The Sanity drain applies only to monsters, scaled by their Horror rating.
- **§5 Architecture / §7.2 Engine:** fixed tick goes to **60 Hz**. Add `combat.pyx` (frame data, hit detection, Reclaim, poise, stagger) and a **time-scale** feature for Dream-Slow and Death Throes. Keep it deterministic.
- **§7.8 RL:** split into **Commander (PPO)** and **Duelist (behavior trees, optionally a duel-only PPO)**.
- **§7.10 Card Forge:** add a **Moveset tab** with a frame-data timeline editor (wind-up/active/recovery bars) and a hitbox preview.
- **§8 Assets:** prefer **rigged and animated** placeholder models (idle, walk, attack, hit, death clips). Check that the license covers the animations too.
- **§10 Risks:** add *"First-person melee feel is the hardest part of the project"*. Prototype it first, playtest often, and tune hitstop and wind-ups before adding content.

---

## 13. Smart Procedural Environments

**Goal:** generate the 3D arenas (and the Dreamlands map) without an environment artist laying out each one, but with enough judgment that they feel designed. The libraries already in the stack can do this. The *generation* itself uses standard procedural algorithms. The **"smart"** part is ML used to **guide** and **judge** the output: transformers, sentence-transformers, CLIP, scikit-learn, and the RL bots.

Dream-Quest helps here: arenas are **bounded tabletops seen at full scale** (§12.1), not open worlds. Table clutter becomes terrain: candles are towers, books are cliffs, tablecloth folds are hills, and ink spills are lakes.

### 13.1 The pipeline

```
 OFFLINE (dev machine, ML allowed)                                     RUNTIME (shipped exe)
 ┌────────────────┐   ┌────────────────┐   ┌──────────────┐   ┌───────────────────────┐
 │ 1. TEXT → SPEC │ → │ 2. SPEC →      │ → │ 3. RENDER    │ → │ 4. SCORE & CURATE     │
 │ Lovecraft      │   │    LAYOUT      │   │ moderngl     │   │ validators (pytest)   │
 │ passage →      │   │ WFC, noise,    │   │ offscreen    │   │ AI playtests (SB3)    │
 │ JSON spec      │   │ Poisson scatter│   │ thumbnails   │   │ CLIP theme score      │
 │ (transformers) │   │ Lua recipes    │   │              │   │ taste model (sklearn) │
 └────────────────┘   └────────────────┘   └──────────────┘   │ human review (NiceGUI)│
                              ▲                               └──────────┬────────────┘
                              │ same deterministic code                  │ accepted seeds/specs
                              └──────────────────────────────────────────▼──────────────
                                                  content/arenas/*.json → stage 2 runs at load time
```

**Main rule:** stage 2 (the layout generator) is **deterministic, ML-free, and shipped**. NumPy, Cython, and Lua only. Everything with ML runs offline and outputs **seeds and specs**, which are tiny JSON files. The exe stays small, layouts stay replay-safe, and modders can write new recipes.

### 13.2 What each library does here

| Library | Role in world generation |
|---|---|
| **transformers** (language model) | Reads Lovecraft's description of a place and writes a structured **arena spec** (landmarks, palette, lighting, hazards, how open it is, which props). It describes *what* is there, not the geometry. |
| **transformers** (CLIP) | Scores rendered thumbnails against a text prompt (*"the cold, desolate Plateau of Leng"*) to rank how well the result matches the theme. |
| **sentence-transformers** | **Matches props to the theme:** embed each asset's tags and pick the closest to the spec's mood. Also finds the source passage for every Locale. |
| **NumPy + Cython** | The generators: Wave Function Collapse, heightmap noise, Poisson-disk scattering, flood-fill checks. Cython for the inner loops. |
| **Lupa / Lua** | **Arena recipes:** rules that turn a spec into a layout, moddable like cards. |
| **moderngl** | Instanced rendering of hundreds of props; offscreen rendering (`create_standalone_context`) for thumbnails; optional compute shaders (GL 4.3) for terrain. |
| **stable-baselines3 bots** | **AI playtesters:** the Commander and Duelist (§12.6) fight on each candidate. Arenas where one side wins far more often, or matches stall, are rejected. |
| **scikit-learn** | A **taste model** trained on your ratings of about 100 arenas to filter new candidates automatically. Also clustering, so accepted arenas aren't all alike. |
| **pytest** | Hard checks: Rifts reachable, no units spawning inside geometry, enough cover. |
| **NiceGUI / PyWebView** | A **curator** to browse candidates, rate them, accept or reject, and re-roll. |
| **SB3 (optional, research)** | **PCGRL:** an RL agent edits a level tile by tile to improve a quality score. Interesting to try, but not needed. |

### 13.3 Design guidelines

- **One hand-made landmark per Locale, generated surroundings.** Fully generated levels look the same. Hand-place one landmark (Kadath's onyx castle, the Tower of Koth, Ulthar's temple) and let the generator fill the rest of the arena around it.
- **Generate for combat, not just looks.** Every arena needs readable **paths between Rifts**, cover for stealth builds (§12.4), **light sources** (candles) that make dark zones, and vertical spaces for Night-gaunts and Cats.
- **Symmetry decides fairness.** Use **rotational symmetry** for PvP-like duels and allow **asymmetric** layouts in boss and elite fights.
- **Non-Euclidean is a feature.** Lovecraft gives you an excuse for impossible spaces: **portal seams** joining far edges, rooms larger inside than outside, and stairs that loop. These are rendering and teleport tricks layered on a normal generated layout, so the validators still work on the underlying grid.
- **The Dreamlands map is generated too.** The run map (§3.6) is a layered graph built Slay the Spire style. Its node types are weighted by the layer's spec (more Pursuit nodes in the Enchanted Wood, more Study nodes in Celephaïs).
- **Generating 3D models themselves (experimental):** Hugging Face hosts image-to-3D models (e.g. TripoSR, among others). They can rough out **static props**, but quality and licenses vary, and they won't produce rigged, animated creatures. Keep using modular CC0 kits for architecture, and check every model's license before shipping its output.

### 13.4 Code template

The code for this section is in **[CODE_TEMPLATES.md §13.4](CODE_TEMPLATES.md#134-code-template-procedural-environments)**.

### 13.5 Updates to the earlier plan

- **§2 Plan by phase:** add **Phase 5b: World generation** after the roguelike layer: generators and validators first, then the offline ML scoring loop, then the Curator.
- **§5 Architecture:** add a `worldgen/` module (shipped, deterministic) next to `engine/`, and `tools/worldgen/` (offline ML) next to `tools/story/`.
- **§6 Project layout:** add `content/arenas/` (accepted seeds and specs), `content/arenas/recipes/` (Lua), and `content/models/manifest.json` (asset tags).
- **§7.10 Modding:** modders can write **arena recipes** in Lua and add tagged assets to the manifest, and a "Generate & Preview" button in Card Forge runs the validators.
- **§8 Assets:** prefer **modular** CC0 kits (walls, floors, pillars, stairs that snap to a grid) because WFC needs them. Tag every asset in the manifest when you import it.

---

## 14. Beyond the Dreamlands: Waking-World Horrors

The Dreamlands are only part of Lovecraft. His best-known horrors live in the **Waking World**: Innsmouth, Dunwich, Arkham, Antarctica, the hills of Vermont, and sunken R'lyeh. In Dream-Quest they come through **Thin Places**, spots where the Wall of Sleep is weak (from *Beyond the Wall of Sleep*), and the nightmares of the waking world leak into the dream.

### 14.1 Story frame: the Wall of Sleep is breaking

- Something is pushing through from the waking side. Carter's quest for Kadath turns out to be connected: **Nyarlathotep is weakening the Wall** so that the Great Old Ones of the waking world can enter the Dreamlands, and from there the minds of every sleeper on Earth.
- **Thin Place** map nodes (🌀) appear on every layer. Entering one turns the next fight into a Waking-World battle with that horror's faction, arena biome, and rules.
- **Alternate layers** make each run different. Each layer of §3.6 can be swapped for a Waking-World variant:

| Layer | Dreamlands route | Waking-World alternative |
|---|---|---|
| 2 | Enchanted Wood → Ulthar | **Dunwich Hills** (Whateleys, whippoorwills) or **Arkham & Miskatonic University** (Herbert West, the Witch House) |
| 3 | The Moon → Celephaïs | **Innsmouth & Devil Reef** (Deep Ones) |
| 4 | The Underworld | **The Mountains of Madness** (Elder Things, shoggoths) or **Exham Priory's depths** (*The Rats in the Walls*) |
| 5 | Plateau of Leng | **Yuggoth & the Vermont hills** (Mi-Go) or **Pnakotus** (the Great Race, flying polyps) |
| 6 (boss) | Kadath: Nyarlathotep | **R'lyeh Rising: Cthulhu** or **The Dunwich Gate: Yog-Sothoth's Spawn** (unlocked after a first win) |

### 14.2 Copyright notes for these works

| Status | Works |
|---|---|
| **Public domain by date** (published 1930 or earlier) | *Dagon* (1919), *Herbert West: Reanimator* (1922), *The Rats in the Walls* (1924), *The Hound* (1924), *The Festival* (1925), *The Colour Out of Space* (1927), *The Call of Cthulhu* (1928), *The Dunwich Horror* (1929), *The Lurking Fear* (1923), *The Music of Erich Zann* (1922), *Beyond the Wall of Sleep* (1919) |
| **Widely treated as public domain** (the general view is that copyright renewals were never validly filed, and many commercial games use these freely, but the date alone doesn't settle it) | *The Whisperer in Darkness* (1931), *The Dreams in the Witch House* (1933), *From Beyond* (1934, written 1920), *At the Mountains of Madness* (1936), *The Shadow over Innsmouth* (1936), *The Shadow out of Time* (1936), *The Haunter of the Dark* (1936), *The Thing on the Doorstep* (1937), *The Case of Charles Dexter Ward* (1941) |
| **⚠ Not Lovecraft. Avoid unless you've checked the specific case** | **Revisions and collaborations** (*The Mound*, *The Curse of Yig*, *Medusa's Coil*, *Out of the Aeons*, *The Horror in the Museum*), whose rights may involve the co-author's estate. **Other authors' creatures:** Hounds of Tindalos (F.B. Long), Tsathoggua (C.A. Smith), Byakhee, Cthugha, and the Derleth "Elder Gods" (August Derleth), Dark Young (later RPG material), Shudde M'ell (Brian Lumley). |

> **Rule of thumb:** use the creature *as Lovecraft described it in his own story*, not later RPG or fan versions. For example, Shub-Niggurath appears in Lovecraft only as an invoked name ("the Black Goat of the Woods with a Thousand Young"), so build her from that phrase, not from later stat blocks.

> **Content note:** several of these stories contain Lovecraft's racism, including the xenophobia of *Innsmouth* and the way *The Call of Cthulhu* describes its cultists. Adapt the *cosmic* horror, not the prejudice: cults are cults of every background, Innsmouth's horror is the sea and inheritance, and leave out *The Horror at Red Hook* and *Arthur Jermyn* entirely.

### 14.3 Waking-World factions

| Faction | Source | Playstyle | Example cards | Signature mechanic |
|---|---|---|---|---|
| **Deep Ones & the Esoteric Order of Dagon** | *Dagon*, *The Shadow over Innsmouth* | Tide control, healing in water, slow corruption | *Deep One Raider*, *Innsmouth Hybrid*, *Father Dagon*, *Mother Hydra*, *Obed Marsh's Pact*, *Devil Reef* (Locale) | **The Innsmouth Look:** hits apply *Change* stacks. At 3 stacks, a unit (or Dreamer) **turns**: it gets amphibious abilities and loses Sanity cap. **Rising Tide:** the arena water level rises over the match. |
| **Cult of Cthulhu & the Spawn** | *The Call of Cthulhu* | Rituals, sacrifice, global Sanity pressure | *Cthulhu Cultist*, *Spawn of Cthulhu*, *Stone Idol of R'lyeh*, *The Sleeper Dreams* (Rite), **Cthulhu** (boss) | **Dreaming Pressure:** Sanity drains slowly for *both* players while Cthulhu's cards are in play. Artists and dreamers (high-Insight units) suffer most. |
| **Elder Things & Shoggoths** | *At the Mountains of Madness* | Builders and engineers vs. rebellious slaves | *Elder Thing Engineer*, *Shoggoth*, *Blind Albino Penguin*, *Cyclopean City* (Locale), *Hibernation Vault* | **Construction:** Elder Things **build cover and walls mid-battle** (runtime use of §13's generators). **Shoggoth Mimicry:** shoggoths copy the last move used on them. |
| **Mi-Go (Fungi from Yuggoth)** | *The Whisperer in Darkness* | Surgery, capture, flight | *Mi-Go Surgeon*, *Mi-Go Swarm*, *Brain Cylinder*, *Voice Machine*, *Henry Akeley's Letters* | **Brain Cylinders:** a Mi-Go can **seal a fallen enemy card in a cylinder** and use its abilities. **Unphotographable:** Mi-Go are **invisible in Altar View** and only seen in first person. |
| **The Great Race of Yith** | *The Shadow out of Time* | Time and mind control | *Yithian Archivist*, *Cone-bodied Scholar*, *Lightning Projector*, *Library of Pnakotus*, *Flying Polyp* | **Mind-Exchange:** swaps the mind of *your* possessed unit: you're thrown into a slow Yithian body for 8 s while the enemy controls yours. (A counter to Soul Leap.) |
| **Flying Polyps** | *The Shadow out of Time* | Invisible wind attacks; fought alone or with Yith | *Flying Polyp*, *Basalt Trapdoor* | **Partly invisible:** only seen at Insight ≥ 4 (via shader). At lower Insight you only hear whistling and see dust. |
| **The Dunwich Whateleys** | *The Dunwich Horror* | Hybrids, invisible giants, summoning | *Wilbur Whateley*, *Old Whateley*, *Lavinia Whateley*, *The Unseen Brother*, *Whippoorwill Flock*, *Sentinel Hill* (Locale) | **The Unseen Brother:** a huge invisible unit that leaves **footprints and crushed terrain**. The *Powder of Ibn Ghazi* (a Rite) reveals it. **Whippoorwills:** when a unit dies near them, they **catch its soul**: no Death Throes window (§12.2). |
| **Reanimators** | *Herbert West: Reanimator* | Graveyard abuse, unstable undead | *Herbert West*, *Reanimated Subject*, *West's Reagent*, *The Headless Thing* | **Reanimation:** bring units back from the Abyss as **uncontrollable frenzied** copies that attack the nearest unit of *either* side. |
| **Witches & Familiars** | *The Dreams in the Witch House* | Hand disruption, impossible angles | *Keziah Mason*, *Brown Jenkin*, *Master of the Witch-Cult* (an avatar of Nyarlathotep), *Witch House Attic* (Locale) | **Brown Jenkin** steals cards from your hand. **Witch House** arenas use non-Euclidean portal seams (§13.3) everywhere. |
| **Necromancers** | *The Case of Charles Dexter Ward* | Raise and dismiss the dead | *Joseph Curwen*, *Essential Saltes*, *Things in the Pits*, *Formula of Dismissal* | **Saltes:** dead cards become **saltes**. Curwen raises the enemy's dead for his own side; the *Formula of Dismissal* instantly destroys any raised unit. |
| **Body-Thieves** | *The Thing on the Doorstep* | Possession duels | *Ephraim Waite*, *Asenath Waite*, *The Thing on the Doorstep* | **Body Theft:** Ephraim steals your **Dreamer's body** (boss mechanic). You must Soul Leap back in by landing a Severance on your own body. |
| **The Rats and the Priory** | *The Rats in the Walls* | Endless swarms; deeper is worse | *Rat Swarm*, *Exham Priory*, *The Twilit Grotto* | **Descent:** the arena has floors. Each time enemies are cleared, the floor collapses into a worse lower level, as in the story. |
| **The Colour Out of Space** | *The Colour Out of Space* | Not a creature: a spreading Locale enemy | *The Colour*, *Blasted Heath*, *The Well* | **Blight:** a spreading tile corruption that **drains** units standing in it and **desaturates** the world (shader). It can't be killed, only **contained**: build cover, burn tiles, or seal the Well. |
| **Things Glimpsed Beyond** | *From Beyond* | Insight punishment | *Tillinghast's Resonator* (Talisman), *Jellyfish Things*, *Crawford Tillinghast* | **Always There:** floating jelly beings exist in *every* arena but stay harmless until your **Insight is high enough to see them**. Then they attack. |
| **Lurkers** | *The Lurking Fear* | Tunnel ambushes in storms | *Martense Degenerate*, *Thunderstorm* (Locale) | **Lightning Reveal:** lurkers come up through the ground and are only visible in **lightning flashes**. |
| **The Hound's Curse** | *The Hound* | A run-long stalker | *Jade Amulet* (Talisman), *The Winged Hound* | **Nemesis:** taking the Jade Amulet makes you stronger, but **the Hound hunts you for the rest of the run** and appears in random fights, getting stronger each time until you return the amulet. |

### 14.4 Playing as Waking-World monsters

Following §12.5, each body needs its own senses and movement:

| Creature | Camera / body | Movement and dodge | Senses (screen shader) | Signature move |
|---|---|---|---|---|
| **Deep One** | 1.8 m, hunched | Slow on land, **fast swimming** (full 3D underwater); *submerge* dodge | Underwater clarity; on land, the view **blurs as you dry out** | Grapple-drown: drag a unit under water |
| **Shoggoth** | 4 m, no fixed "face"; the camera floats inside it | Rolls like a wave; *reform* dodge (splits apart and comes back together) | **Eyes all over:** a wide view with eye-bubbles drifting across the screen | **Engulf:** absorb a small unit and gain its move set. Utterance: *"Tekeli-li!"* |
| **Elder Thing** | 2.4 m, barrel-shaped, 5-fold symmetry | Walk, **glide on membrane wings**; *fold* dodge | Sees in every direction (a ring-shaped panorama shader) | Build: place cover or a ramp from the hand |
| **Mi-Go** | 1.5 m, buzzing | **Flying through the ether** (strafing flight); *phase* dodge | **Colour-shifting head** tints the screen; enemies' brains glow | Surgical extraction: on kill, put the card in a Brain Cylinder |
| **Yithian (cone)** | 3 m, slow, rocking | Gliding on its base; no dodge, **time-skip** instead (rewind your own last 1.5 s) | Library calm: crisp, cold, slow-motion view | Lightning Projector beam; Mind-Exchange |
| **Wilbur Whateley** | 2.7 m, human from the waist up | Long stride; *shamble* dodge | Normal view, but **invisible things show up** as outlines | Reading from the Necronomicon (channel to summon) |
| **The Unseen Brother** | 12 m, giant | Crushing walk; terrain deforms where you step | You're **invisible**; your own body shows only as footprints and broken trees | Stomp: area knockdown, flattens cover |
| **Brown Jenkin** | 0.2 m, rat-sized | Scurry through walls (portal seams); *nip* dodge | Fish-eye view, gnawing sounds | Steal a card from the enemy hand |

### 14.5 New Waking-World Dreamers (playable humans, all Lovecraft characters)

| Dreamer | Source | Occupation (§11.2) | Unique card |
|---|---|---|---|
| **Dr. Henry Armitage** | *The Dunwich Horror* | Librarian | *Powder of Ibn Ghazi*: reveals invisible units |
| **Francis Wayland Thurston** | *The Call of Cthulhu* | Antiquarian | *Collected Clippings*: gives +2 Clues at the start |
| **Inspector John Raymond Legrasse** | *The Call of Cthulhu* | Police detective | *Swamp Raid*: units deal +50% damage to Cultists |
| **Professor William Dyer** | *At the Mountains of Madness* | Geologist | *Expedition Supplies*: start with an extra Talisman |
| **Albert N. Wilmarth** | *The Whisperer in Darkness* | Folklorist | *Phonograph Record*: reveals the Mi-Go in Altar View |
| **Nathaniel Wingate Peaslee** | *The Shadow out of Time* | Economics professor | *Fragmented Memory*: immune to the first Mind-Exchange |
| **Walter Gilman** | *The Dreams in the Witch House* | Mathematics student | *Hyperspace Calculation*: can use enemy portal seams |
| **Dr. Marinus Bicknell Willett** | *The Case of Charles Dexter Ward* | Physician | *Formula of Dismissal*: destroys a raised unit |
| **Daniel Upton** | *The Thing on the Doorstep* | Architect | *Doorstep Revolver*: Severance against body-thieves always succeeds |

### 14.6 Waking-World Talismans and Rites (Lovecraft items)

- **The Necronomicon** *(Talisman, Tome, §11.2)*: by far the most powerful Tome. Reading it takes **5 map nodes** and gives **+4 Insight, −30 Sanity**, and a Rite from each Outer God.
- **Powder of Ibn Ghazi** *(Rite)*: reveals invisible units for 15 s.
- **The Voorish Sign** *(Rite)*: lets *you* see invisible things; your units ignore stealth.
- **West's Reagent** *(Rite)*: reanimate a fallen unit (frenzied, §14.3).
- **Brain Cylinder** *(Talisman)*: store one fallen card from a fight and summon it in the next fight.
- **Lightning Projector** *(Rite)*: Yithian beam weapon; hits invisible units.
- **The Jade Amulet** *(Talisman)*: big stat bonus, plus the Hound's Curse (§14.3).
- **Tillinghast's Resonator** *(Talisman)*: +2 Insight; the Jellyfish Things become visible (and hostile).
- **Obed Marsh's Gold** *(Talisman)*: extra gold at every Bazaar, but each fight starts with one *Change* stack.
- **The Shining Trapezohedron** *(Talisman, §3.5)*: in darkness, calls the Haunter of the Dark. If the arena is fully lit, the Haunter can't appear.

### 14.7 Bosses

| Boss | Arena (worldgen recipe, §13) | Mechanics |
|---|---|---|
| **Cthulhu: R'lyeh Rising** | `core.rlyeh`: geometry where **"the angles are wrong"**: some surfaces count as concave and convex at once (you walk up a slope that is also a wall). Portal seams everywhere. | **Phase 1:** the cult performs the ritual (kill the cultists before the chant finishes). **Phase 2:** Cthulhu rises; Dreaming Pressure drains all Sanity. **Phase 3:** Cthulhu **comes back together** after being "destroyed," as when the ship rammed him in the story. You have 20 s to **scatter his fragments** (a Chorus Chain on each fragment) before he reforms. |
| **The Dunwich Gate: Yog-Sothoth's Spawn** | `core.sentinel_hill`: a hilltop stone ring with whippoorwills around it | The **Unseen Brother** charges up the hill. Throw the *Powder of Ibn Ghazi*, then chant the **counter-formula** (a Ritual combo, §4 idea 13) while defending the chanters. **Yog-Sothoth** sometimes opens **gates**: portals that swap the positions of every unit. |
| **Ephraim Waite** (elite) | `core.crowninshield_house`: a cramped old house | Steals your Dreamer's body (Body Theft). You fight him *in* your own body; landing a Severance on it brings you back. |
| **The Colour** (elite, can't be killed) | `core.blasted_heath`: a farm going grey | **Survive 3 minutes** while containing the Blight. The score is how much of the heath you save. |

### 14.8 Arena recipes to add (§13)

| Recipe | Biome | Generator focus |
|---|---|---|
| `core.innsmouth_harbor` | Decaying fishing town, wharves, Devil Reef offshore | Water-level hazard that **rises over time**; WFC with crumbling wharf tiles |
| `core.antarctic_city` | Cyclopean ruins under ice, tunnels | Heightmap glaciers, WFC with Elder Thing architecture, dark tunnels for shoggoths |
| `core.yuggoth_mines` | Fungal caverns, black rivers, alien towers | Cavern terrain, glowing fungal light sources, vertical shafts for flight |
| `core.dunwich_hills` | Round hills, stone circles, a decaying farmhouse | Hills + stone rings + **footprint trails** (Unseen Brother) |
| `core.arkham_campus` | Gambrel roofs, the Miskatonic library, graveyards | Street grid WFC, graveyard tiles for reanimation |
| `core.witch_house` | A slanted attic room that keeps repeating | **Portal-heavy:** every wall can be a seam |
| `core.exham_depths` | Priory → cellars → grotto | **Stacked floors** that collapse (the Descent mechanic) |
| `core.rlyeh` | Sunken city rising from the sea | Non-Euclidean seams, wet green stone, rising water |
| `core.blasted_heath` | Farmland turning grey | Blight spread over the tile grid; a well at the center |

### 14.9 Code template

The code for this section is in **[CODE_TEMPLATES.md §14.9](CODE_TEMPLATES.md#149-code-template-waking-world-horrors)**.

### 14.10 Updates to the earlier plan

- **§3.5 Factions:** the faction list is now **Dreamlands (§3.5) + Waking World (§14.3)**. Keep the starter set to Dreamlands factions; Waking-World factions **unlock** by visiting Thin Places.
- **§3.6 Run structure:** add **🌀 Thin Place** nodes and the **alternate layers** in 14.1.
- **§4 Creative ideas:** the **Necronomicon collection book** (idea 4) gets a "Waking World" section with lore drawn from the stories in 14.2.
- **§7.7 Story pipeline:** tag corpus passages by **source story** so retrieval for Waking-World cards only uses the matching story.
- **§13 Worldgen:** add the arena recipes in 14.8. The water-level and Blight hazards need new `gen.*` functions.
- **Mod idea now in the core game:** the *Innsmouth* and *Mountains of Madness* "Mythos Packs" from §4 idea 12 are now core content. Suggest other Lovecraft stories for modders instead.

---

*"We live on a placid island of ignorance in the midst of black seas of infinity, and it was not meant that we should voyage far."* Then again, Carter did voyage. Good luck on the Dream-Quest.
