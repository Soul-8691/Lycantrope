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

1. [Things to Settle First](#1-things-to-settle-first)
2. [Plan by Phase](#2-plan-by-phase)
3. [Game Design](#3-game-design)
4. [Creative Ideas](#4-creative-ideas)
5. [Architecture](#5-architecture)
6. [Project Layout](#6-project-layout)
7. [Code Template](#7-code-template)
   - 7.1 [Build config (`pyproject.toml`, `setup.py`)](#71-build-config)
   - 7.2 [Cython engine core](#72-cython-engine-core-enginecorepyx)
   - 7.3 [Lua bridge (Lupa, sandboxed)](#73-lua-bridge-enginescriptingpy)
   - 7.4 [Lua card definitions](#74-lua-card-definitions)
   - 7.5 [Renderer (pygame + moderngl)](#75-renderer-pygame--moderngl)
   - 7.6 [Main game loop](#76-main-game-loop-mainpy)
   - 7.7 [Story pipeline (transformers + sentence-transformers)](#77-story-pipeline)
   - 7.8 [RL opponent (gymnasium + stable-baselines3)](#78-rl-opponent)
   - 7.9 [Balance analysis (scikit-learn + Gambit)](#79-balance-analysis-scikit-learn--gambit)
   - 7.10 [Modding tools (Tkinter / NiceGUI / PyWebView)](#710-modding-tools)
   - 7.11 [Tests (pytest)](#711-tests-pytest)
   - 7.12 [Packaging (PyInstaller)](#712-packaging-pyinstaller)
8. [Assets and Licensing](#8-assets-and-licensing)
9. [Releasing on itch.io](#9-releasing-on-itchio)
10. [Risks and How to Handle Them](#10-risks-and-how-to-handle-them)
11. [Ideas from the Call of Cthulhu RPG](#11-ideas-from-the-call-of-cthulhu-rpg)

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

## 7. Code Template

> These templates are **descriptive skeletons**. They show the intended shape of each system and the important details. They are not finished code.

### 7.1 Build config

**`pyproject.toml`**
```toml
[build-system]
requires = ["setuptools>=69", "wheel", "Cython>=3.0"]
build-backend = "setuptools.build_meta"

[project]
name = "dreamquest"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pygame-ce>=2.5",      # maintained pygame fork, drop-in replacement
    "moderngl>=5.10",
    "pyglm>=2.7",          # fast matrix math for cameras/transforms
    "lupa>=2.2",           # Lua 5.4 runtime
    "pygltflib>=1.16",     # load .glb models
    "numpy>=1.26",
    "onnxruntime>=1.18",   # ships the trained AI, NOT torch
]

[project.optional-dependencies]
dev   = ["pytest", "pytest-cov", "hypothesis", "pyinstaller", "cython"]
ml    = ["torch", "transformers", "datasets", "peft", "accelerate",
         "sentence-transformers", "pymupdf"]
rl    = ["gymnasium", "stable-baselines3", "sb3-contrib", "torch", "onnx"]
tools = ["nicegui", "pywebview", "tkinterweb", "scikit-learn", "pandas", "pygambit"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**`setup.py`** (compiles the Cython engine)
```python
from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension("dreamquest.engine.core", ["src/dreamquest/engine/core.pyx"]),
    Extension("dreamquest.engine.rng",  ["src/dreamquest/engine/rng.pyx"]),
]

setup(
    package_dir={"": "src"},
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": 3,
            "boundscheck": False,   # turn back on while debugging
            "wraparound": False,
            "cdivision": True,
        },
        annotate=True,              # emits .html showing Python-interaction hot spots
    ),
)
# Build in place:  python setup.py build_ext --inplace
```

---

### 7.2 Cython engine core (`engine/core.pyx`)

```cython
# cython: language_level=3
"""
Deterministic, headless simulation for Dream-Quest.

- Fixed timestep (TICK_DT). No wall-clock time, no global random.
- Pure state + rules. The renderer only reads `snapshot()`.
- Card *behavior* lives in Lua; this module calls hooks via `self.script`.
"""
from libc.math cimport sqrt
from dreamquest.engine.rng cimport PCG32

DEF TICK_DT = 0.05            # 20 Hz simulation
DEF LUCIDITY_REGEN = 0.4      # per second
DEF LUCIDITY_MAX = 10.0

cdef class Unit:
    cdef public int uid, owner, rift
    cdef public str card_id
    cdef public double x, z, vx, vz, facing
    cdef public int hp, max_hp, atk
    cdef public double speed, attack_range, attack_cooldown, cd_timer
    cdef public bint possessed, alive
    cdef public dict tags          # e.g. {"eldritch": True, "ward": 1}

    def __init__(self, int uid, int owner, str card_id, dict stats, double x, double z):
        self.uid, self.owner, self.card_id = uid, owner, card_id
        self.x, self.z = x, z
        self.vx = self.vz = 0.0
        self.hp = self.max_hp = stats["hp"]
        self.atk = stats["atk"]
        self.speed = stats.get("speed", 2.0)
        self.attack_range = stats.get("range", 1.2)
        self.attack_cooldown = stats.get("cooldown", 1.0)
        self.cd_timer = 0.0
        self.possessed = False
        self.alive = True
        self.tags = dict(stats.get("tags", {}))


cdef class Player:
    cdef public int pid
    cdef public double lucidity, sanity, insight
    cdef public list deck, hand, abyss
    cdef public int possessed_uid          # -1 = none

    def __init__(self, int pid, list deck):
        self.pid = pid
        self.lucidity, self.sanity, self.insight = 3.0, 100.0, 0.0
        self.deck, self.hand, self.abyss = list(deck), [], []
        self.possessed_uid = -1


cdef class World:
    cdef public list players
    cdef public dict units                 # uid -> Unit
    cdef public int tick, next_uid
    cdef public double doom, doom_limit
    cdef public object script              # ScriptHost (Lupa bridge)
    cdef public object events              # EventBus
    cdef PCG32 rng

    def __init__(self, unsigned long long seed, list decks, object script, object events):
        self.rng = PCG32(seed)
        self.players = [Player(i, d) for i, d in enumerate(decks)]
        self.units = {}
        self.tick = 0
        self.next_uid = 1
        self.doom, self.doom_limit = 0.0, 13.0
        self.script, self.events = script, events
        self.script.bind_world(self)       # exposes a safe `game` API to Lua

    # ---------- public API used by Lua through ScriptHost ----------
    cpdef int rand_int(self, int lo, int hi):
        return lo + <int>(self.rng.next_u32() % <unsigned int>(hi - lo + 1))

    cpdef void deal_damage(self, int target_uid, int amount, int source_uid=-1):
        cdef Unit u = self.units.get(target_uid)
        if u is None or not u.alive:
            return
        if u.tags.get("ward", 0) > 0:          # Elder Sign blocks one hit
            u.tags["ward"] -= 1
            self.events.emit("Warded", uid=target_uid)
            return
        u.hp -= amount
        self.events.emit("DamageDealt", uid=target_uid, amount=amount, src=source_uid)
        if u.hp <= 0:
            self._kill(u)

    cpdef void change_sanity(self, int pid, double delta):
        cdef Player p = self.players[pid]
        cdef double before = p.sanity
        p.sanity = max(0.0, min(100.0, p.sanity + delta))
        self.events.emit("SanityChanged", pid=pid, before=before, after=p.sanity)
        # Darkest-Dungeon-style threshold checks (Affliction / Revelation)
        for threshold in (75.0, 50.0, 25.0):
            if before > threshold >= p.sanity:
                self.script.call_global("on_sanity_threshold", pid, threshold)

    # ---------- actions (from player input or AI) ----------
    def apply(self, action):
        """Route an Action dataclass to its handler. Invalid actions are ignored."""
        handler = getattr(self, "_do_" + action.kind, None)
        if handler is not None and self.is_legal(action):
            handler(action)

    def is_legal(self, action) -> bool:
        ...  # cost checks, Rift occupancy, Insight requirements for Forbidden cards

    def legal_action_mask(self, int pid):
        """Fixed-size boolean mask for RL (MaskablePPO). See ai/env.py."""
        ...

    def _do_play_card(self, action):
        cdef Player p = self.players[action.pid]
        card = self.script.card(action.card_id)
        p.lucidity -= card["cost"]
        p.hand.remove(action.card_id)
        if card["type"] == "entity":
            u = self._spawn(action.pid, action.card_id, card["stats"], action.rift)
            self.script.call_hook(action.card_id, "on_summon", u.uid)
        else:
            self.script.call_hook(action.card_id, "on_play", action.pid, action.target)
            p.abyss.append(action.card_id)

    def _do_possess(self, action): ...
    def _do_move(self, action): ...         # sets velocity for the possessed unit
    def _do_ability(self, action): ...

    # ---------- simulation ----------
    cpdef void step(self):
        """Advance exactly one fixed tick."""
        cdef Player p
        cdef Unit u
        self.tick += 1
        for p in self.players:
            p.lucidity = min(LUCIDITY_MAX, p.lucidity + LUCIDITY_REGEN * TICK_DT)
            if p.possessed_uid != -1:
                p.sanity -= 0.5 * TICK_DT          # possession slowly drains the mind
        for u in list(self.units.values()):
            if not u.alive:
                continue
            if not u.possessed:
                self.script.call_hook(u.card_id, "on_tick", u.uid, TICK_DT)  # Lua AI
            self._integrate(u)
            self._auto_attack(u)
        if self.doom >= self.doom_limit:
            self.script.call_global("on_doom_awakens")

    cdef void _integrate(self, Unit u):
        u.x += u.vx * TICK_DT
        u.z += u.vz * TICK_DT
        # clamp to the Altar bounds, resolve unit overlap (simple circle push-apart)

    cdef void _auto_attack(self, Unit u):
        u.cd_timer -= TICK_DT
        if u.cd_timer > 0:
            return
        target = self._nearest_enemy(u)
        if target is not None and self._dist(u, target) <= u.attack_range:
            self.script.call_hook(u.card_id, "on_attack", u.uid, target.uid)
            self.deal_damage(target.uid, u.atk, u.uid)
            u.cd_timer = u.attack_cooldown

    cdef Unit _spawn(self, int owner, str card_id, dict stats, int rift): ...
    cdef void _kill(self, Unit u): ...      # on_death hook, card to Abyss, emit event
    cdef object _nearest_enemy(self, Unit u): ...
    cdef double _dist(self, Unit a, Unit b):
        return sqrt((a.x - b.x) ** 2 + (a.z - b.z) ** 2)

    def snapshot(self) -> dict:
        """Plain-data copy for rendering, saving, Silver Key rewinds, and tests."""
        ...

    def winner(self):
        """Return pid of winner, or None. A player loses at Sanity 0."""
        ...
```

---

### 7.3 Lua bridge (`engine/scripting.py`)

```python
"""
Lupa-backed scripting host.

Security: mods are untrusted code. We strip dangerous Lua globals,
cap memory, limit instruction count per call, and expose ONLY a curated `game` table.
"""
from pathlib import Path
import lupa
from lupa import LuaRuntime

SAFE_ATTRS = {"rand_int", "deal_damage", "change_sanity", "draw", "units_of",
              "unit", "add_doom", "add_insight", "emit_vfx"}

def _attr_filter(obj, attr_name, is_setting):
    """Block Lua from reaching arbitrary Python attributes (e.g. __class__)."""
    if isinstance(attr_name, str) and attr_name in SAFE_ATTRS and not is_setting:
        return attr_name
    raise AttributeError(f"Lua may not access '{attr_name}'")

SANDBOX_PRELUDE = r"""
-- Instruction budget: abort runaway scripts (infinite loops in mods).
local sethook = debug.sethook
function __dq_guard(budget)
  sethook(function() error("script exceeded instruction budget", 2) end, "", budget)
end
function __dq_unguard() sethook() end

-- Remove dangerous capabilities.
os, io, debug, package, require, dofile, loadfile, load, collectgarbage = nil
math.random, math.randomseed = nil, nil   -- use game.rand(lo, hi) for determinism
"""

class ScriptHost:
    def __init__(self, content_dirs: list[Path], instruction_budget: int = 200_000):
        self.lua = LuaRuntime(
            unpack_returned_tuples=True,
            register_eval=False,             # no python.eval from Lua
            register_builtins=False,         # no python.builtins from Lua
            attribute_filter=_attr_filter,
            max_memory=64 * 1024 * 1024,     # 64 MB cap (Lupa >= 2.0)
        )
        self.lua.execute(SANDBOX_PRELUDE)
        self.budget = instruction_budget
        self.cards: dict[str, object] = {}   # card_id -> Lua table
        for d in content_dirs:
            self._load_dir(d)

    def _load_dir(self, directory: Path):
        for path in sorted(directory.rglob("*.lua")):
            chunk = path.read_text(encoding="utf-8")
            card = self.lua.execute(chunk)   # each file `return`s a card table
            if card is not None and card["id"]:
                self.cards[card["id"]] = card

    def bind_world(self, world):
        """Expose the curated game API as the global `game` table."""
        g = self.lua.globals()
        api = self.lua.table()
        api.rand = world.rand_int
        api.damage = world.deal_damage
        api.sanity = world.change_sanity
        # ... units_of(pid), unit(uid) -> read-only proxy, add_doom, emit_vfx, etc.
        g.game = api

    def card(self, card_id: str) -> dict:
        t = self.cards[card_id]
        return {"cost": t.cost, "type": t.type, "stats": dict(t.stats or {})}

    def call_hook(self, card_id: str, hook: str, *args):
        fn = self.cards[card_id][hook]
        if fn is None:
            return None
        self.lua.globals().__dq_guard(self.budget)
        try:
            return fn(*args)
        except lupa.LuaError as e:
            # Never crash the game because of a bad mod: log it and disable the hook.
            print(f"[mod error] {card_id}.{hook}: {e}")
        finally:
            self.lua.globals().__dq_unguard()

    def call_global(self, name: str, *args): ...
```

---

### 7.4 Lua card definitions

**`content/cards/core/cat_of_ulthar.lua`**
```lua
-- Every card file returns ONE table. Hooks are optional.
return {
  id      = "core.cat_of_ulthar",
  name    = "Cat of Ulthar",
  type    = "entity",
  faction = "cats",
  cost    = 2,
  rarity  = "common",
  model   = "models/cat_small.glb",
  art     = "textures/cards/cat_of_ulthar.png",
  stats   = { hp = 6, atk = 2, speed = 4.5, range = 1.0, cooldown = 0.7,
              tags = { swift = true } },

  -- Flavor pulled from content/story/flavor.json at load time by key.
  flavor_key = "cat_of_ulthar",

  keywords = { "Swift", "Rivalry(moonbeasts)" },
  text = "Deals double damage to Moon-beasts. When an allied Dreamer drops "
      .. "below 50 Sanity, gains Ward.",

  on_summon = function(uid)
    game.emit_vfx("rift_open_soft", uid)
  end,

  -- Called every tick when NOT possessed: simple behavior script.
  on_tick = function(uid, dt)
    local me = game.unit(uid)
    local target = game.nearest_enemy(uid, { prefer_tag = "moonbeast" })
    if target then game.move_toward(uid, target.x, target.z) end
  end,

  on_attack = function(uid, target_uid)
    local t = game.unit(target_uid)
    if t.tags.moonbeast then game.damage(target_uid, game.unit(uid).atk, uid) end
  end,

  on_owner_sanity_threshold = function(uid, threshold)
    if threshold <= 50 then game.add_tag(uid, "ward", 1) end
  end,
}
```

**`content/cards/core/nyarlathotep_crawling_chaos.lua`** (a Forbidden boss card)
```lua
return {
  id = "core.nyarlathotep", name = "Nyarlathotep, the Crawling Chaos",
  type = "entity", faction = "outer_gods", cost = 9, rarity = "mythic",
  forbidden = { insight_required = 6, sanity_cost = 20 },
  keywords = { "Eldritch", "Nameless", "Ancient(8)" },
  stats = { hp = 60, atk = 8, speed = 2.0, range = 3.0, cooldown = 1.6,
            tags = { eldritch = true } },

  -- Thousand forms: pick a random form on summon (deterministic via game.rand).
  forms = { "black_pharaoh", "haunter_of_the_dark", "bloated_woman" },

  on_summon = function(uid)
    local self_card = game.card("core.nyarlathotep")
    local form = self_card.forms[game.rand(1, #self_card.forms)]
    game.set_form(uid, form)              -- swaps model + ability set
    game.add_doom(2)
    for _, pid in ipairs(game.opponents_of(game.unit(uid).owner)) do
      game.sanity(pid, -10)
    end
  end,
}
```

**`content/cards/api.lua`**: write documentation comments for every `game.*` function here. The mod-kit renders this file as HTML in TkinterWeb.

---

### 7.5 Renderer (pygame + moderngl)

**`render/renderer.py`**
```python
import moderngl
import numpy as np
import glm                      # PyGLM
from pathlib import Path

SHADERS = Path(__file__).parent / "shaders"

class Renderer:
    def __init__(self, size: tuple[int, int]):
        self.ctx = moderngl.create_context()          # uses pygame's GL context
        self.ctx.enable(moderngl.DEPTH_TEST | moderngl.BLEND)
        self.size = size
        self.card_prog = self._program("card")
        self.creature_prog = self._program("creature")
        self.post_prog = self._program("fullscreen", "post_madness")
        self.card_vao = self._make_card_quad()
        self.scene_fbo = self.ctx.framebuffer(
            color_attachments=[self.ctx.texture(size, 4)],
            depth_attachment=self.ctx.depth_renderbuffer(size),
        )
        self.models = {}         # path -> (vao, texture) loaded lazily via model_loader
        self.camera = ...        # orbiting "seated at the table" camera

    def _program(self, vert, frag=None):
        return self.ctx.program(
            vertex_shader=(SHADERS / f"{vert}.vert").read_text(),
            fragment_shader=(SHADERS / f"{frag or vert}.frag").read_text(),
        )

    def _make_card_quad(self):
        # A thin quad with UVs; cards are 63x88mm ratio -> 0.716
        w, h = 0.716, 1.0
        verts = np.array([
            # x,   y,  z,   u, v
            -w/2, 0, -h/2, 0, 0,
             w/2, 0, -h/2, 1, 0,
             w/2, 0,  h/2, 1, 1,
            -w/2, 0,  h/2, 0, 1,
        ], dtype="f4")
        idx = np.array([0, 1, 2, 0, 2, 3], dtype="i4")
        vbo, ibo = self.ctx.buffer(verts), self.ctx.buffer(idx)
        return self.ctx.vertex_array(self.card_prog, [(vbo, "3f 2f", "in_pos", "in_uv")], ibo)

    def draw(self, prev: dict, curr: dict, alpha: float, t: float):
        """Interpolate between two engine snapshots (alpha in 0..1)."""
        self.scene_fbo.use()
        self.ctx.clear(0.02, 0.01, 0.03)
        self._draw_table()
        for card in curr["cards_on_table"]:
            self._draw_card(card, t)                    # burn = 1 - hp/max_hp
        for uid, u in curr["units"].items():
            p = prev["units"].get(uid, u)
            x = p["x"] + (u["x"] - p["x"]) * alpha
            z = p["z"] + (u["z"] - p["z"]) * alpha
            self._draw_creature(u, x, z, t)
        # Post-process: sanity/insight distortion to screen
        self.ctx.screen.use()
        self.post_prog["u_sanity"] = curr["local_player"]["sanity"] / 100.0
        self.post_prog["u_insight"] = curr["local_player"]["insight"]
        self.post_prog["u_time"] = t
        self.scene_fbo.color_attachments[0].use(0)
        ...  # draw fullscreen triangle
```

**`render/shaders/card.frag`**: dissolve and "rift" effects for the living card
```glsl
#version 330
in vec2 v_uv;
out vec4 f_color;

uniform sampler2D u_art;
uniform sampler2D u_noise;
uniform float u_burn;      // 0 = pristine, 1 = fully burned (damage taken)
uniform float u_rift;      // 0..1 while the creature is emerging
uniform float u_time;

void main() {
    vec4 art = texture(u_art, v_uv);
    float n = texture(u_noise, v_uv * 1.5 + vec2(0.0, u_time * 0.02)).r;

    // Burn: tear away card where noise < burn amount, glowing ember edge.
    if (n < u_burn) discard;
    float edge = smoothstep(u_burn, u_burn + 0.05, n);
    vec3 ember = mix(vec3(1.0, 0.35, 0.05), art.rgb, edge);

    // Rift: the art swirls into a portal from the center while summoning.
    vec2 c = v_uv - 0.5;
    float r = length(c);
    float swirl = u_rift * (1.0 - smoothstep(0.0, 0.45, r));
    vec3 portal = vec3(0.25, 0.05, 0.45) * (1.0 + sin(r * 40.0 - u_time * 6.0));
    f_color = vec4(mix(ember, portal, swirl), art.a);
}
```

**`render/shaders/post_madness.frag`**: low Sanity warps the screen
```glsl
#version 330
in vec2 v_uv;
out vec4 f_color;
uniform sampler2D u_scene;
uniform float u_sanity;    // 1 = sane, 0 = mad
uniform float u_insight;
uniform float u_time;

void main() {
    float madness = clamp(1.0 - u_sanity, 0.0, 1.0);
    vec2 uv = v_uv;
    uv += madness * 0.006 * vec2(sin(uv.y * 30.0 + u_time * 2.0),
                                 cos(uv.x * 25.0 + u_time * 1.7));
    // Chromatic aberration grows with madness.
    float ca = madness * 0.004;
    vec3 col = vec3(texture(u_scene, uv + vec2(ca, 0)).r,
                    texture(u_scene, uv).g,
                    texture(u_scene, uv - vec2(ca, 0)).b);
    // Vignette closes in.
    float vig = smoothstep(0.9, 0.3 - madness * 0.2, length(v_uv - 0.5));
    f_color = vec4(col * vig, 1.0);
}
```

**`render/shaders/creature.vert`**: Insight "true-form" displacement (works on any placeholder model)
```glsl
#version 330
in vec3 in_pos; in vec3 in_normal; in vec2 in_uv;
uniform mat4 u_mvp; uniform float u_insight; uniform float u_time; uniform float u_emerge;
out vec3 v_normal; out vec2 v_uv;
void main() {
    vec3 p = in_pos;
    // Writhing: high Insight reveals "true form" via normal-displacement waves.
    float w = sin(p.y * 12.0 + u_time * 3.0) * cos(p.x * 9.0 - u_time * 2.0);
    p += in_normal * w * 0.03 * clamp(u_insight / 10.0, 0.0, 1.0);
    // Emerging: rise out of the card (y scaled from 0 -> 1 during summon).
    p.y *= u_emerge;
    gl_Position = u_mvp * vec4(p, 1.0);
    v_normal = in_normal; v_uv = in_uv;
}
```

---

### 7.6 Main game loop (`main.py`)

```python
import sys
import time
import pygame
from pathlib import Path
from dreamquest.engine.core import World
from dreamquest.engine.scripting import ScriptHost
from dreamquest.engine.events import EventBus
from dreamquest.render.renderer import Renderer
from dreamquest.game.ui import InputController
from dreamquest.ai.policy import OnnxOpponent
from dreamquest.modding.loader import discover_mods

TICK_DT = 0.05

def base_dir() -> Path:
    # Works both from source and from a PyInstaller onedir build.
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))

def exe_dir() -> Path:
    # content/ and mods/ live NEXT TO the exe so players can edit them.
    return Path(sys.executable).parent if getattr(sys, "frozen", False) else base_dir()

def main():
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                    pygame.GL_CONTEXT_PROFILE_CORE)
    size = (1600, 900)
    pygame.display.set_mode(size, pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
    pygame.display.set_caption("Dream-Quest")

    root = exe_dir()
    content_dirs = [root / "content" / "cards"] + discover_mods(root / "mods")
    events = EventBus()
    script = ScriptHost(content_dirs)
    world = World(seed=1234, decks=[...], script=script, events=events)

    renderer = Renderer(size)
    controls = InputController(world, renderer.camera, pid=0)
    cpu = OnnxOpponent(root / "content" / "ai" / "opponent_v1.onnx", pid=1)
    events.subscribe("*", renderer.on_event)       # VFX + audio react to events

    prev = curr = world.snapshot()
    accumulator, last = 0.0, time.perf_counter()
    clock = pygame.time.Clock()

    running = True
    while running:
        now = time.perf_counter()
        accumulator += min(now - last, 0.25)        # avoid spiral of death
        last = now

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            controls.handle(ev)                     # queues Actions

        while accumulator >= TICK_DT:               # fixed-step simulation
            for action in controls.drain():
                world.apply(action)
            world.apply(cpu.act(world))             # CPU decides at sim rate
            prev, curr = curr, None
            world.step()
            curr = world.snapshot()
            accumulator -= TICK_DT

        renderer.draw(prev, curr, alpha=accumulator / TICK_DT, t=now)
        pygame.display.flip()
        clock.tick(144)

        if world.winner() is not None:
            ...  # transition to reward / map screen

    pygame.quit()

if __name__ == "__main__":
    main()
```

---

### 7.7 Story pipeline

All of this runs **offline in `tools/story/`**. Its output is plain JSON shipped in `content/story/`.

**Step 1: Extract and clean the corpus** (`tools/corpus/extract.py`)
```python
"""Split Lovecraft-Complete-Fiction-Print.pdf into one clean .txt per story."""
import re, json
from pathlib import Path
import pymupdf   # pip install pymupdf

PDF = Path(r"C:\Users\pswan\Documents\Books\Lovecraft-Complete-Fiction-Print.pdf")
OUT = Path("data/corpus")

def clean(page_text: str) -> str:
    text = re.sub(r"^\s*\d+\s*$", "", page_text, flags=re.M)   # page numbers
    text = re.sub(r"-\n(\w)", r"\1", text)                       # de-hyphenate
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)                  # unwrap lines
    return text

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(PDF)
    toc = doc.get_toc()          # [(level, title, page), ...] if the PDF has bookmarks
    # Use TOC entries as story boundaries; fall back to heading regex if TOC is empty.
    stories = []
    for i, (lvl, title, start) in enumerate(toc):
        end = toc[i + 1][2] if i + 1 < len(toc) else doc.page_count + 1
        body = "\n".join(clean(doc[p - 1].get_text()) for p in range(start, end))
        slug = re.sub(r"\W+", "_", title.lower()).strip("_")
        (OUT / f"{slug}.txt").write_text(body, encoding="utf-8")
        stories.append({"title": title, "slug": slug, "pages": [start, end - 1]})
    (OUT / "index.json").write_text(json.dumps(stories, indent=2))

if __name__ == "__main__":
    main()
```

**Step 2: Fine-tune a small language model** (`tools/story/finetune.py`)
```python
"""
LoRA fine-tune a small causal LM on the corpus.
Good base choices: distilgpt2 / gpt2 (tiny, CPU-feasible), or a small modern
instruct model (~0.5B-1.5B params) with LoRA on a GPU / Google Colab.
"""
from datasets import load_dataset
from transformers import (AutoTokenizer, AutoModelForCausalLM,
                          DataCollatorForLanguageModeling, Trainer, TrainingArguments)
from peft import LoraConfig, get_peft_model

BASE = "gpt2"  # swap for a stronger small model if you have a GPU

tok = AutoTokenizer.from_pretrained(BASE)
tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(BASE)
model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                                         task_type="CAUSAL_LM"))

ds = load_dataset("text", data_files={"train": "data/corpus/*.txt"}, sample_by="paragraph")
ds = ds.map(lambda b: tok(b["text"], truncation=True, max_length=512),
            batched=True, remove_columns=["text"])

Trainer(
    model=model,
    args=TrainingArguments(output_dir="models/lovecraft-lora", num_train_epochs=3,
                           per_device_train_batch_size=4, learning_rate=2e-4,
                           logging_steps=50, save_strategy="epoch"),
    train_dataset=ds["train"],
    data_collator=DataCollatorForLanguageModeling(tok, mlm=False),
).train()
model.save_pretrained("models/lovecraft-lora")
```

**Step 3: Build an embedding index** (`tools/story/embed.py`)
```python
"""Embed every paragraph so we can (a) retrieve source passages for card lore,
(b) score generated text for 'Lovecraftian-ness' and (c) reject near-duplicates."""
import json, numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")    # small, fast, good enough
paras, meta = [], []
for f in Path("data/corpus").glob("*.txt"):
    for i, p in enumerate(f.read_text(encoding="utf-8").split("\n\n")):
        if len(p) > 200:
            paras.append(p); meta.append({"story": f.stem, "para": i})

emb = model.encode(paras, batch_size=64, normalize_embeddings=True, show_progress_bar=True)
np.save("data/index/emb.npy", emb)
Path("data/index/meta.json").write_text(json.dumps(meta))
np.save("data/index/centroid.npy", emb.mean(axis=0))   # "the Lovecraft direction"
```

**Step 4: Generate, score, and curate** (`tools/story/generate.py`)
```python
"""
Generate flavor text / events / Dreamer journal templates.
Each candidate is scored by:
  style   = cosine(candidate, corpus centroid)       -> sounds like Lovecraft
  grounding = max cosine to passages of the card's source story -> on-theme
  novelty = 1 - max cosine to already-accepted text   -> not repetitive
Top candidates go to data/story/review.jsonl for HUMAN approval
(the Tkinter mod-kit has a review tab), then into content/story/*.json.
"""
PROMPTS = {
    "cat_of_ulthar": "In Ulthar, beyond the river Skai, the cats",
    "zoog_scout":    "Among the twisted trunks of the enchanted wood, the zoogs",
    "event_bazaar":  "At the wharves of Dylath-Leen a merchant in a turban",
}
# for key, prompt in PROMPTS.items():
#     candidates = pipe(prompt, num_return_sequences=20, max_new_tokens=60,
#                       do_sample=True, top_p=0.92, temperature=0.9)
#     scored = sorted(candidates, key=score, reverse=True)[:5]
#     append_to_review_queue(key, scored)
```

> **Tip:** use the model as a **co-writer, not the author.** The best results come from generating many candidates, filtering them automatically, and then editing the top few by hand. Every card's lore can also link back to the *real* Lovecraft passage it was based on, through retrieval.

---

### 7.8 RL opponent

**`tools/rl/env.py`**: a Gymnasium wrapper around the *same* Cython engine
```python
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from dreamquest.engine.core import World

N_HAND, N_RIFTS, N_ABILITIES, N_MOVE_DIRS = 8, 5, 3, 9
# Flat discrete action space (a factored space also works):
#   0                              : no-op
#   play hand[i] on rift[r]        : N_HAND * N_RIFTS
#   possess unit slot k / release  : N_RIFTS + 1
#   move possessed unit dir d      : N_MOVE_DIRS
#   use ability a                  : N_ABILITIES
N_ACTIONS = 1 + N_HAND * N_RIFTS + (N_RIFTS + 1) + N_MOVE_DIRS + N_ABILITIES
OBS_DIM = 256

class DreamQuestEnv(gym.Env):
    """Agent plays pid 1 against an opponent policy (scripted or a frozen past self)."""
    metadata = {"render_modes": []}

    def __init__(self, opponent, decision_every: int = 4):   # 4 ticks = 5 decisions/sec
        self.observation_space = spaces.Box(-1, 1, (OBS_DIM,), np.float32)
        self.action_space = spaces.Discrete(N_ACTIONS)
        self.opponent = opponent
        self.k = decision_every

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.world = World(seed=self.np_random.integers(2**63), decks=sample_decks(),
                           script=make_headless_script_host(), events=NullBus())
        return encode_obs(self.world, pid=1), {}

    def step(self, action):
        self.world.apply(decode_action(action, pid=1))
        before = self.world.players[0].sanity - self.world.players[1].sanity
        for _ in range(self.k):
            self.world.apply(self.opponent.act(self.world, pid=0))
            self.world.step()
        after = self.world.players[0].sanity - self.world.players[1].sanity
        w = self.world.winner()
        reward = 0.01 * (before - after) + (1.0 if w == 1 else -1.0 if w == 0 else 0.0)
        terminated = w is not None
        truncated = self.world.tick > 20 * 60 * 5            # 5-minute cap
        return encode_obs(self.world, 1), reward, terminated, truncated, {}

    def action_masks(self) -> np.ndarray:                    # used by MaskablePPO
        return self.world.legal_action_mask(1)
```

**`tools/rl/train.py`**: self-play with MaskablePPO
```python
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.vec_env import SubprocVecEnv
from env import DreamQuestEnv
from opponents import ScriptedOpponent, PolicyPool

pool = PolicyPool(start=[ScriptedOpponent("aggro"), ScriptedOpponent("control")])

def make_env():
    env = DreamQuestEnv(opponent=pool.sample())
    return ActionMasker(env, lambda e: e.action_masks())

if __name__ == "__main__":
    venv = SubprocVecEnv([make_env for _ in range(8)])
    model = MaskablePPO("MlpPolicy", venv, n_steps=2048, batch_size=512,
                        gamma=0.995, ent_coef=0.01, verbose=1,
                        tensorboard_log="runs/")
    for generation in range(50):
        model.learn(total_timesteps=500_000, reset_num_timesteps=False)
        model.save(f"checkpoints/gen_{generation:03d}")
        pool.add_frozen(model)        # league-style self-play vs. past versions
```

**`tools/rl/export_onnx.py`**: ship the policy without PyTorch
```python
import torch
from sb3_contrib import MaskablePPO

model = MaskablePPO.load("checkpoints/gen_049")
policy = model.policy.eval()

class Actor(torch.nn.Module):
    def __init__(self, p): super().__init__(); self.p = p
    def forward(self, obs):
        feats = self.p.extract_features(obs, self.p.pi_features_extractor)
        latent = self.p.mlp_extractor.forward_actor(feats)
        return self.p.action_net(latent)                 # logits

torch.onnx.export(Actor(policy), torch.zeros(1, 256), "content/ai/opponent_v1.onnx",
                  input_names=["obs"], output_names=["logits"], opset_version=17)
```

**`src/dreamquest/ai/policy.py`**: runtime inference (shipped)
```python
import numpy as np
import onnxruntime as ort

class OnnxOpponent:
    def __init__(self, path, pid, temperature=0.0):
        self.sess = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        self.pid, self.temperature = pid, temperature    # >0 = more human/erratic (easier)

    def act(self, world):
        obs = encode_obs(world, self.pid)[None].astype(np.float32)
        logits = self.sess.run(None, {"obs": obs})[0][0]
        logits[~world.legal_action_mask(self.pid)] = -1e9   # never pick illegal moves
        if self.temperature > 0:                             # difficulty knob
            p = np.exp((logits - logits.max()) / self.temperature); p /= p.sum()
            return decode_action(np.random.choice(len(p), p=p), self.pid)
        return decode_action(int(logits.argmax()), self.pid)
```

**Difficulty tiers:** *Dreamer* (early checkpoint + high temperature), *Initiate* (mid checkpoint), *Elder* (final, temperature 0), *Nyarlathotep* (final + player-modeling counter-deck).

---

### 7.9 Balance analysis (scikit-learn + Gambit)

```python
"""tools/balance/analyze.py: run thousands of headless AI-vs-AI games, then analyze."""
import pandas as pd
from sklearn.linear_model import LogisticRegression
import pygambit as gbt

# 1) Card impact: which cards push win-rate up or down?
df = pd.read_parquet("sim_logs/games.parquet")       # one row per (game, side)
X = df.filter(like="card_")                           # 0/1 inclusion per card
y = df["won"]
clf = LogisticRegression(C=0.5, max_iter=2000).fit(X, y)
impact = pd.Series(clf.coef_[0], index=X.columns).sort_values()
print("Over-performers:\n", impact.tail(10))
print("Under-performers:\n", impact.head(10))

# 2) Faction meta: treat faction-vs-faction win rates as a zero-sum matrix game.
#    The Nash equilibrium mix tells you if one faction is strictly dominant
#    (bad), or if the meta is a healthy rock-paper-scissors.
factions = ["cats", "zoogs", "ghouls", "gugs", "gaunts", "leng"]
M = winrate_matrix(df, factions) - 0.5               # payoff for row player
game = gbt.Game.from_arrays(M, -M, title="Dreamlands meta")
eq = gbt.nash.lcp_solve(game, rational=False).equilibria[0]
for f, prob in zip(factions, eq[game.players[0]]):
    print(f"{f:8s} {float(prob):.2%} of equilibrium play")
# A faction at 0% = never worth playing -> buff it. One at ~100% -> nerf it.
```

---

### 7.10 Modding tools

The libraries split the work like this:

| Tool | Library | Purpose |
|---|---|---|
| **Card Forge** | Tkinter | Main desktop editor: card form, Lua code editor, live card preview, validation |
| **API Docs / Lore panel** | TkinterWeb (`HtmlFrame`) | Renders `api.lua` docs and card lore as HTML inside the Tkinter app |
| **Mythos Lab** | NiceGUI | Dashboard: balance charts, sim runner, AI-text review queue |
| **Desktop wrapper** | PyWebView | `ui.run(native=True)` in NiceGUI opens the dashboard in a native window via PyWebView |

**`tools/modkit/card_forge.py`** (Tkinter)
```python
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterweb import HtmlFrame
from pathlib import Path
from dreamquest.engine.scripting import ScriptHost

FIELDS = ["id", "name", "type", "faction", "cost", "rarity", "hp", "atk", "text"]

class CardForge(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dream-Quest — Card Forge")
        self.geometry("1280x800")

        panes = ttk.PanedWindow(self, orient="horizontal")
        panes.pack(fill="both", expand=True)

        # Left: card list (from content/ + mods/)
        self.tree = ttk.Treeview(panes, columns=("cost", "faction"))
        panes.add(self.tree, weight=1)

        # Middle: form + Lua code editor
        mid = ttk.Frame(panes); panes.add(mid, weight=2)
        self.vars = {f: tk.StringVar() for f in FIELDS}
        for row, f in enumerate(FIELDS):
            ttk.Label(mid, text=f).grid(row=row, column=0, sticky="w")
            ttk.Entry(mid, textvariable=self.vars[f], width=40).grid(row=row, column=1)
        self.code = tk.Text(mid, font=("Consolas", 11), height=20, bg="#120c18", fg="#d8c9ff")
        self.code.grid(row=len(FIELDS), column=0, columnspan=2, sticky="nsew")
        ttk.Button(mid, text="Validate in sandbox", command=self.validate) \
            .grid(row=len(FIELDS) + 1, column=0)
        ttk.Button(mid, text="Save .lua", command=self.save) \
            .grid(row=len(FIELDS) + 1, column=1)

        # Right: HTML preview (rendered card + API docs)
        self.preview = HtmlFrame(panes, messages_enabled=False)
        panes.add(self.preview, weight=2)
        self.code.bind("<KeyRelease>", lambda e: self.refresh_preview())

    def to_lua(self) -> str:
        """Generate a card file from form fields + custom hooks code."""
        ...

    def validate(self):
        """Load the card into a throwaway sandboxed ScriptHost and run a mini sim."""
        try:
            host = ScriptHost(content_dirs=[])
            host.lua.execute(self.to_lua())
            messagebox.showinfo("Card Forge", "The card is valid. The stars are right.")
        except Exception as e:
            messagebox.showerror("Card Forge", f"The ritual failed:\n{e}")

    def refresh_preview(self):
        self.preview.load_html(render_card_html({f: v.get() for f, v in self.vars.items()}))

    def save(self): ...

if __name__ == "__main__":
    CardForge().mainloop()
```

**`tools/modkit/mythos_lab.py`** (NiceGUI + PyWebView)
```python
from nicegui import ui
from balance import run_sims, load_impact, load_review_queue

ui.dark_mode().enable()
ui.label("Mythos Lab").classes("text-3xl")

with ui.tabs() as tabs:
    sim_tab, review_tab = ui.tab("Simulations"), ui.tab("Story Review")

with ui.tab_panels(tabs, value=sim_tab):
    with ui.tab_panel(sim_tab):
        n = ui.number("Games", value=1000)
        ui.button("Run AI-vs-AI", on_click=lambda: run_sims(int(n.value)))
        ui.echart(load_impact_chart_options())     # card impact bar chart
    with ui.tab_panel(review_tab):
        for item in load_review_queue():
            with ui.card():
                ui.label(item["key"]).classes("font-bold")
                ui.markdown(item["text"])
                with ui.row():
                    ui.button("Accept", on_click=lambda i=item: accept(i))
                    ui.button("Reject", on_click=lambda i=item: reject(i)).props("flat")

ui.run(native=True, title="Mythos Lab", window_size=(1200, 800))  # native=True → PyWebView
```

**Mod format** (`mods/<mod_name>/mod.toml`)
```toml
id = "innsmouth"
name = "The Shadow over Innsmouth"
version = "1.0.0"
game_version = ">=0.5"
author = "..."
cards = "cards/"          # *.lua
models = "models/"        # *.glb
textures = "textures/"
load_after = ["core"]
```

---

### 7.11 Tests (pytest)

**`tests/conftest.py`**
```python
import pytest
from pathlib import Path
from dreamquest.engine.core import World
from dreamquest.engine.scripting import ScriptHost
from dreamquest.engine.events import EventBus

CORE = Path(__file__).parents[1] / "content" / "cards" / "core"

@pytest.fixture
def host():
    return ScriptHost([CORE])

@pytest.fixture
def world(host):
    deck = ["core.cat_of_ulthar"] * 20
    return World(seed=42, decks=[deck, deck], script=host, events=EventBus())
```

**`tests/test_engine.py`**
```python
from dreamquest.engine.actions import PlayCard

def test_lucidity_regenerates(world):
    start = world.players[0].lucidity
    for _ in range(20):                      # 1 second
        world.step()
    assert world.players[0].lucidity > start

def test_cannot_play_without_lucidity(world):
    world.players[0].lucidity = 0
    world.players[0].hand = ["core.cat_of_ulthar"]
    world.apply(PlayCard(pid=0, card_id="core.cat_of_ulthar", rift=0))
    assert len(world.units) == 0

def test_sanity_zero_loses(world):
    world.change_sanity(0, -999)
    assert world.winner() == 1
```

**`tests/test_determinism.py`**: the most important test in the project
```python
from hypothesis import given, strategies as st

@given(seed=st.integers(0, 2**32), actions=st.lists(random_action(), max_size=200))
def test_same_seed_same_result(seed, actions):
    a, b = make_world(seed), make_world(seed)
    for act in actions:
        a.apply(act); b.apply(act); a.step(); b.step()
    assert a.snapshot() == b.snapshot()     # replays, RL and rewinds depend on this
```

**`tests/test_mod_sandbox.py`**
```python
import pytest
import lupa

@pytest.mark.parametrize("evil", [
    "os.execute('calc')",
    "io.open('C:/Windows/win.ini')",
    "require('socket')",
    "python.eval('__import__(\"os\")')",
    "while true do end",                    # must hit the instruction budget
])
def test_mods_cannot_escape(host, evil):
    with pytest.raises(lupa.LuaError):
        host.lua.globals().__dq_guard(10_000)
        host.lua.execute(evil)

def test_every_core_card_loads(host):
    assert len(host.cards) > 0
    for cid, card in host.cards.items():
        assert card["cost"] is not None, cid
```

Run with: `pytest -q --cov=dreamquest`

---

### 7.12 Packaging (PyInstaller)

Use a **`onedir`** build, not `onefile`. It starts faster, causes fewer antivirus false positives, and keeps `content/` and `mods/` as **plain folders next to the exe** so players can mod the game.

**`dreamquest.spec`**
```python
# pyinstaller dreamquest.spec
block_cipher = None

a = Analysis(
    ["src/dreamquest/main.py"],
    pathex=["src"],
    binaries=[],
    datas=[("src/dreamquest/render/shaders", "dreamquest/render/shaders")],
    hiddenimports=[
        "dreamquest.engine.core", "dreamquest.engine.rng",   # compiled .pyd modules
        "lupa.lua54", "moderngl", "glcontext",
    ],
    excludes=["torch", "tensorflow", "transformers", "sentence_transformers",
              "stable_baselines3", "sklearn", "nicegui", "matplotlib"],  # keep exe small
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="DreamQuest",
          console=False, icon="assets/icon.ico")
coll = COLLECT(exe, a.binaries, a.datas, name="DreamQuest")
```

**Post-build step** (`tools/build.py`): copy `content/`, `mods/example_mod/`, `CREDITS.md`, `LICENSE.txt`, and `MODDING.md` into `dist/DreamQuest/`, then zip it for itch.io. Optionally build a **separate `CardForge.exe`** from `tools/modkit/card_forge.py`.

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
| **Backstory** (ideology, significant people, treasured possessions...) | **Anchors:** each Dreamer has 3 Anchors (*"My cat, Black Tom"*, *"The old house on Benefit Street"*, *"Faith in reason"*). An Anchor can be **sacrificed once** to fully pass a Composure check. Madness can **corrupt** an Anchor, turning it into a liability (inspired by CoC changing a character's backstory after insanity). | Dreamer cards, run events |
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

**`src/dreamquest/engine/checks.py`** (Cythonize later if profiling shows it's a hot path)
```python
"""
Percentile check system inspired by classic horror RPG mechanics (renamed / adapted).
All randomness goes through world.rand_int -> deterministic, replay-safe.
"""
from dataclasses import dataclass
from enum import IntEnum

class Tier(IntEnum):
    FUMBLE = -1
    FAIL = 0
    SUCCESS = 1
    STRONG = 2      # <= half skill
    SUBLIME = 3     # <= fifth skill

@dataclass(frozen=True)
class CheckResult:
    roll: int
    skill: int
    tier: Tier
    pushed: bool = False

def roll_d100(world, favor: int = 0, dread: int = 0) -> int:
    """Favor/Dread dice: extra tens digits; keep best (Favor) or worst (Dread)."""
    net = favor - dread
    units = world.rand_int(0, 9)
    tens = [world.rand_int(0, 9) for _ in range(1 + abs(net))]
    candidates = [(t * 10 + units) or 100 for t in tens]   # 00 + 0 counts as 100
    return min(candidates) if net > 0 else max(candidates)

def check(world, skill: int, favor: int = 0, dread: int = 0) -> CheckResult:
    r = roll_d100(world, favor, dread)
    fumble_floor = 100 if skill >= 50 else 96
    if r >= fumble_floor:
        tier = Tier.FUMBLE
    elif r <= max(1, skill // 5):
        tier = Tier.SUBLIME
    elif r <= skill // 2:
        tier = Tier.STRONG
    elif r <= skill:
        tier = Tier.SUCCESS
    else:
        tier = Tier.FAIL
    world.events.emit("CheckRolled", roll=r, skill=skill, tier=int(tier))  # renderer shows bone die
    return CheckResult(r, skill, tier)

def spend_fortune(player, result: CheckResult) -> CheckResult:
    """Spend Fortune 1:1 to lower a failed roll to exactly the skill value."""
    need = result.roll - result.skill
    if result.tier == Tier.FAIL and 0 < need <= player.fortune:
        player.fortune -= need
        return CheckResult(result.skill, result.skill, Tier.SUCCESS, result.pushed)
    return result

def parse_dice(expr: str, world) -> int:
    """'3' -> 3, '1d6' -> 1..6, '2d4+1' -> 3..9"""
    ...

def composure_check(world, pid: int, horror: str, creature_kind: str) -> int:
    """
    horror is written 'small / big', e.g. '1 / 1d6'.
    Pass -> lose small; fail -> lose big. Familiarity caps per-kind loss per battle.
    Returns Sanity actually lost.
    """
    p = world.players[pid]
    small, big = (s.strip() for s in horror.split("/"))
    res = check(world, skill=int(p.sanity))                 # roll under current Sanity
    loss = parse_dice(small if res.tier >= Tier.SUCCESS else big, world)

    cap = familiarity_cap(world, pid, creature_kind)        # e.g. max die value of `big`
    already = p.familiarity.get(creature_kind, 0)
    loss = max(0, min(loss, cap - already))
    p.familiarity[creature_kind] = already + loss

    world.change_sanity(pid, -loss)
    p.battle_sanity_lost += loss
    if loss >= 5 and check(world, p.attrs["intellect"]).tier >= Tier.SUCCESS:
        # Like the classic rule: understanding what you saw is what breaks you.
        world.script.call_global("on_fracture", pid, world.rand_int(1, 10))
    if p.battle_sanity_lost >= p.sanity_at_battle_start / 5:
        world.script.call_global("on_affliction", pid)
    return loss

def max_sanity(player) -> int:
    """Forbidden Lore: knowledge erodes the mind's ceiling."""
    return max(10, 100 - 5 * int(player.insight))
```

**Lua: an ability that uses success tiers and Press On** (`content/cards/core/night_gaunt.lua`)
```lua
return {
  id = "core.night_gaunt", name = "Night-gaunt", type = "entity",
  faction = "gaunts", cost = 4, rarity = "uncommon",
  horror = "0 / 1d4",                 -- Composure check when the opponent first sees it
  creature_kind = "night_gaunt",
  stats = { hp = 14, atk = 3, speed = 5.0, range = 1.2, cooldown = 1.2 },

  abilities = {
    {
      key = "abduct", name = "Silent Abduction", skill = 45, cooldown = 8.0,
      -- `res.tier` is one of: "fumble", "fail", "success", "strong", "sublime"
      on_resolve = function(uid, target_uid, res)
        if res.tier == "sublime" then
          game.remove_from_battle(target_uid)            -- carried off to Ngranek
        elseif res.tier == "strong" then
          game.stun(target_uid, 3.0); game.damage(target_uid, 6, uid)
        elseif res.tier == "success" then
          game.stun(target_uid, 1.5)
        elseif res.tier == "fumble" then
          game.stun(uid, 2.0)                            -- tangled in its own wings
        end
      end,
      -- Called only if the player Presses On and the reroll fails again.
      dire_consequence = function(uid)
        game.change_owner(uid)                           -- the gaunt serves Nodens, not you
      end,
    },
  },
}
```

**Lua: Fracture table as moddable data** (`content/cards/core/fractures.lua`)
```lua
return {
  [1]  = { id = "amnesia",   duration = 10, apply = function(pid) game.hide_hand(pid, true) end,
                                             expire = function(pid) game.hide_hand(pid, false) end },
  [2]  = { id = "flight",    duration = 8,  apply = function(pid) game.force_flee(pid) end },
  [7]  = { id = "phobia",    permanent = true,
           apply = function(pid, cause_kind) game.add_phobia(pid, cause_kind) end },
  [10] = { id = "revelation", duration = 0,
           apply = function(pid) game.add_insight(pid, 2); game.reveal_enemy_hand(pid) end },
  -- ... 3–6, 8, 9
}
```

**Tests** (`tests/test_checks.py`)
```python
from dreamquest.engine.checks import check, Tier, max_sanity, composure_check

import pytest

@pytest.mark.parametrize("roll,expected", [
    (10, Tier.SUBLIME), (25, Tier.STRONG), (50, Tier.SUCCESS), (51, Tier.FAIL), (100, Tier.FUMBLE),
])
def test_tiers_follow_skill_fractions(world, monkeypatch, roll, expected):
    monkeypatch.setattr("dreamquest.engine.checks.roll_d100", lambda *a, **k: roll)
    assert check(world, skill=50).tier == expected

def test_forbidden_lore_lowers_max_sanity(world):
    p = world.players[0]
    p.insight = 6
    assert max_sanity(p) == 70

def test_familiarity_caps_repeated_horror(world):
    total = sum(composure_check(world, 0, "1 / 1d6", "night_gaunt") for _ in range(10))
    assert total <= 6                                       # can't lose more than the cap per kind

def test_checks_are_deterministic(world_factory):
    a, b = world_factory(seed=7), world_factory(seed=7)
    assert [check(a, 50).roll for _ in range(100)] == [check(b, 50).roll for _ in range(100)]
```

### 11.5 Updates to the earlier plan

- **§3.2 Resources:** add **Fortune** (per run) and the **max-Sanity cap from Insight**.
- **§3.3 Card types:** add **Tome** (a Talisman read over several map nodes) and **Found Document** (a collectible that holds a Clue).
- **§3.6 Run map:** add **🔍 Investigation** (Clues and Found Documents), **🏃 Pursuit** (chase), and **📖 Study** (keep reading a Tome) node types.
- **§7.8 RL observation:** add the Fortune, Familiarity, active Fracture, and Anchors state so the CPU learns to play around madness. Use the same `check()` code path for the CPU, so it gets no hidden advantages.
- **§7.10 Card Forge:** add a **Skill %** field per ability, a **Horror** field (`small / big`), and a **tier preview** that rolls 1,000 simulated checks and shows the outcome distribution.
- **§9 Store page:** describe the game as *"inspired by classic tabletop horror RPGs and Lovecraft's Dreamlands."* Don't use the *Call of Cthulhu* name in the title, tags, or capsule art.

---

*"We live on a placid island of ignorance in the midst of black seas of infinity, and it was not meant that we should voyage far."* Then again, Carter did voyage. Good luck on the Dream-Quest.
