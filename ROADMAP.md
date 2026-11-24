# LYCANTROPE — Implementation Roadmap

> Python 3.11+ · pygame-ce + moderngl · Meshy (models) · ElevenLabs (voice, SFX, music) · MIT · free on itch.io

The roadmap refers to ideas by their ID in [IDEAS.md](IDEAS.md) (for example **CMB-08**). When you **deny** an idea in the tracker, the matching tasks are dropped or replaced when the roadmap is next updated. **Awaiting** ideas marked ⭐ are assumed *in* until you say otherwise, because the week can't wait for every decision.

---

## 0. Decisions needed before Day 1

These change code or assets on Day 1–2, so please decide them in the tracker first:

| Decide | Options | Why it matters now |
|---|---|---|
| Rowan's gender and voice | **HER-02** or **HER-03** | Meshy model prompt and ElevenLabs voice design run on Day 1 |
| Where you level up | **STA-02** (anywhere) or **STA-03** (Moonwells only) | Level-up UI and death loop |
| pygame or pygame-ce | **TEC-01** | Install step; pygame-ce is recommended |
| First boss | **BOS-01** Grimtooth (recommended: it reuses the werewolf rig) or another | Asset kitchen queue on Day 2 |
| Asset licence | **REL-01**, **REL-04** | What goes in the public repo |

You also need:
- **API keys** set as environment variables: `MESHY_API_KEY` and `ELEVENLABS_API_KEY`. Never paste them into files that get committed.
- **Git + Git LFS** installed, an empty GitHub repo, an itch.io project page (can be set to draft), and **ffmpeg** on your PATH (used for audio mastering).

---

## 1. Milestones

| Milestone | Target | What "done" means |
|---|---|---|
| **M0 Foundations** | Day 1 | Repo, venv, window with a GL context, fixed-step loop, terrain on screen, asset pipelines running |
| **M1 First Playable** | End of Week 1 (core) + Week 2 (full roster) | Rowan (human + beast form), 4 biomes on one map, **15–20 enemies** with voiced barks at levels 1–16, XP/levels with no NPC, 6 attributes + 8 use-based skills that change combat, Moonwells, one boss, save/load, Windows build on itch |
| **M2 Vertical Slice** | Weeks 3–5 | First Seal dungeon (Wolfwood) with its tool (grappling chain), Brood Queen boss, prologue, the Hunger's voice, music, bestiary, compass |
| **M3 Public Demo** | ~Week 8 | Two Seals, Inquisitor duel #1, polish pass, settings and accessibility, devlog push |
| **M4 Full Game** | Later | Four Seals, Ashen Reach, the Crypts, Eclipse Spire, Lycaon, two endings, NG+ |

**Week 1 is about proving the core.** By Sunday you should have a downloadable build in which Rowan explores four biomes, fights about 12 enemy types, levels up, transforms and kills a boss. **Week 2** finishes the roster to 20, adds the rest of the voice lines, and tunes balance. With the Meshy and ElevenLabs batches running in the background all week, that is ambitious but achievable. The cut list (§6) says what to drop first if a day overruns.

---

## 2. Tech stack

| Purpose | Package | Notes |
|---|---|---|
| Window, input, audio | `pygame-ce` | `import pygame` still works; relative mouse mode; joystick support |
| Rendering | `moderngl` | OpenGL 3.3 core |
| Math | `PyGLM`, `numpy` | glm for per-object math, numpy for bulk work |
| Models | `pygltflib` (+ `trimesh` for offline tools) | GLB meshes, skins, animations |
| Images | `Pillow` | Textures, icons, the biome mask |
| HTTP | `requests` | Meshy and ElevenLabs batch tools (offline only, not shipped) |
| Noise | `numpy` (own implementation) or `opensimplex` | Offline terrain generation |
| Tests | `pytest` (+ `hypothesis` later) | Formulas, data validation, saves |
| Build | `pyinstaller`, `butler` | Windows onedir build → itch.io |

---

## 3. Architecture

```
                 ┌──────────────────────────────────────────┐
                 │ main.py  — fixed 60 Hz sim, render @ vsync│
                 └───────┬──────────────────────┬───────────┘
          InputState     │                      │  read-only state + alpha
                         ▼                      ▼
┌──────────────┐  ┌──────────────────┐   ┌───────────────────────────┐
│ input/       │→ │ SIMULATION       │   │ RENDERER (moderngl)       │
│ kb/mouse/pad │  │ world, actors,   │   │ terrain chunks, instanced │
│ buffer 150ms │  │ combat, AI, rpg  │   │ props, skinned meshes,    │
└──────────────┘  │ (no GL calls)    │   │ sky, shadows, post, UI tex│
                  └───┬──────────┬───┘   └───────────────────────────┘
                 events│          │data
                      ▼          ▼
     ┌──────────────────────┐  ┌──────────────────────────────────┐
     │ EventBus → audio,    │  │ data/*.json (enemies, attacks,   │
     │ VFX, barks, HUD,     │  │ items, loot, biomes, xp) — F5    │
     │ subtitles            │  │ hot-reload in dev                │
     └──────────────────────┘  └──────────────────────────────────┘

 OFFLINE (tools/, never shipped): Meshy batch → normalize GLB → assets/models
                                  ElevenLabs batch → ffmpeg → assets/audio
                                  worldgen → heightmap.npy + biome mask + scatter.json
```

**Rules that apply throughout** (PIL-07, TEC-04 to TEC-07):
1. The simulation never calls the GPU. The renderer only reads state.
2. Every attack, enemy, item and loot table is JSON. Code supplies behaviours, data supplies content.
3. Every bug fix or formula gets a pytest.
4. Offline tools are resumable and cache by content hash. Never pay twice for the same asset.

---

## 4. Project layout

```
Lycantrope/
├── IDEAS.md  ROADMAP.md  IDEAS_STATUS.md  ideas_status.json  CLAUDE.md
├── README.md  LICENSE  ASSETS-LICENSE.md  CREDITS.md
├── run_idea_tracker.bat
├── pyproject.toml  requirements.txt  requirements-tools.txt
├── src/lycantrope/
│   ├── main.py                  ← entry point, loop
│   ├── core/       config.py  events.py  input.py  rng.py  save.py  timing.py
│   ├── render/     renderer.py  camera.py  terrain.py  mesh.py  gltf.py  skinning.py
│   │               instancing.py  sky.py  shadows.py  post.py  particles.py  ui_layer.py
│   │               shaders/*.vert|*.frag
│   ├── world/      heightfield.py  biomes.py  scatter.py  collision.py  moonwells.py  spawns.py
│   ├── combat/     attacks.py  hitbox.py  damage.py  status.py  lockon.py  feel.py (hitstop/shake)
│   ├── actors/     actor.py  player.py  beast.py  enemy.py
│   │   └── ai/     fsm.py  archetypes.py  tokens.py  steering.py
│   ├── rpg/        stats.py  skills.py  leveling.py  inventory.py  loot.py
│   ├── audio/      mixer.py  voice.py  music.py
│   └── ui/         hud.py  menus.py  levelup.py  subtitles.py  fonts.py
├── data/           enemies/*.json  attacks/*.json  items.json  loot.json  biomes.json
│                   xp.json  voices.json  lines.csv  sfx.csv
├── assets/  (Git LFS)  models/  textures/  audio/{vo,sfx,music}/  fonts/  world/
├── tools/
│   ├── idea_tracker.py          ← done
│   ├── meshy/      batch.py  manifest.json  normalize.py  preview.py
│   ├── voice/      design_voices.py  generate.py  sfx.py  music.py  master.py
│   ├── worldgen/   heightmap.py  scatter.py  validate.py  textures.py
│   └── credits.py
└── tests/          test_stats.py  test_damage.py  test_data_schema.py  test_save.py ...
```

---

## 5. Week 1, day by day

Each day has a **code track** and an **asset kitchen** track (batch jobs that run in the background while you code). Day 1 is Monday 23 November. Day 4 falls on US Thanksgiving, so the plan counts days rather than dates and you can shift it.

### Day 1: Foundations, and start the kitchen
**Code**
- [ ] `git init`, `.gitignore` (venv, `.env`, `__pycache__`, `*.tmp`), `git lfs track "*.glb" "*.png" "*.ogg" "*.wav" "*.npy"`, MIT `LICENSE`, README stub. *(REL-01, REL-05, REL-06)*
- [ ] venv + `pip install pygame-ce moderngl PyGLM numpy pygltflib Pillow pytest`. *(TEC-01 to TEC-03)*
- [ ] `main.py`: pygame window with an OpenGL 3.3 core context, a moderngl context, a fixed 60 Hz loop with an accumulator and interpolation alpha, and a debug text overlay. *(TEC-04, TEC-17)*
- [ ] `tools/worldgen/heightmap.py`: 2048² heightmap from fBm and ridged noise, with a hand-paintable `biome_mask.png` (4 colours = Vale, Wolfwood, Blackmire, Frostfang) that shapes the height. Outputs `assets/world/height.npy` + `mask.png`. *(WLD-01, TOL-05)*
- [ ] `render/terrain.py`: 64 m chunk meshes, slope/height/mask splatting with procedural textures from `tools/worldgen/textures.py`, and a free-fly camera. *(TEC-10, ART-08)*

**Asset kitchen**
- [ ] `tools/meshy/batch.py` + `manifest.json`: text-to-3D preview → refine → remesh → download. Cache key = hash(prompt + settings). Resumable from a `jobs.json`. *(ART-01, ART-02, ART-06)*
- [ ] Queue batch 1: **Rowan (human)**, **Rowan beast form**, Bandit, Goblin, Skeleton, Orc, plus ~12 props (3 tree types per biome, rocks, Moonwell, chest, ruined wall).
- [ ] `tools/voice/design_voices.py`: create Rowan, the Hunger and 6 enemy voices with Voice Design. Save `data/voices.json`. *(AUD-02)*

**Done when:** you can fly over a four-biome landscape at 60 fps, and the first Meshy jobs are running.

### Day 2: Rowan moves
**Code**
- [ ] Capsule character controller: ground snapping on the heightfield, slope limit, gravity, jump and auto-jump at ledges, run and sprint. *(TEC-09, WLD-19)*
- [ ] Third-person orbit camera with terrain collision, and lock-on with target switching. *(CMB-01, CMB-02)*
- [ ] Stamina and a dodge roll with i-frames, plus the input buffer. *(CMB-03, CMB-06, CMB-15)*
- [ ] `render/gltf.py`: load static GLB meshes and textures, with Rowan shown in a bind pose. Add `tools/meshy/normalize.py` (scale, axis, pivot at the feet). *(ART-07)*
- [ ] Controller support through `pygame.joystick`. *(UIX-11)*

**Asset kitchen**
- [ ] Meshy **rigging + animation** for Rowan: idle, walk, run, sprint, roll, light ×3, heavy ×2, block, parry, hit, death, crossbow aim and shoot. Also queue the werewolf rig. Check the action names in Meshy's current animation library. *(ART-03)*
- [ ] Batch 2 models: Wolf, Rat, Spider, Ooze, Harpy, Lizardfolk, Troll, Wraith, Yeti, Ogre, Warden Knight, Golem, Grimtooth.
- [ ] `tools/voice/generate.py` + `data/lines.csv`: Rowan's ~40 lines and the first enemy barks. *(AUD-01, AUD-03, AUD-04)*

**Done when:** Rowan runs, rolls and locks onto a training dummy, and it feels good on both keyboard and mouse and on a gamepad.

### Day 3: Skinning and the combat core
**Code**
- [ ] GPU skinning: up to 4 weights per vertex, a joint palette in a UBO, clip sampling with linear/slerp interpolation and 0.15 s crossfades. In-place animations, so movement comes from code. *(TEC-08)*
- [ ] `data/attacks/*.json` frame data and `combat/attacks.py` running light and heavy strings with cancel windows. *(CMB-04, CMB-16)*
- [ ] Swept-capsule hitboxes against hurtboxes, and damage resolution. *(CMB-17, CMB-18)*
- [ ] Hit feel: hitstop, camera shake, FOV punch, spark particles, impact SFX hooks on the event bus. *(CMB-14, TEC-06, ART-13)*
- [ ] Block, guard break, the parry window → riposte, poise and stagger. *(CMB-07, CMB-08, CMB-10)*
- [ ] The first real enemy: **Bandit Brigand** running the `melee-basic` FSM (idle → alert → approach → strafe → attack → recover, plus stagger and dead). *(ENM-04, TEC-13)*

**If skinning takes more than half a day:** park it and keep going with a rigid "bind pose plus procedural lean and bob" placeholder so combat work isn't blocked. Come back to skinning on Day 5.

**Done when:** you can duel a bandit that blocks, punishes greedy attacks, and can be parried.

### Day 4: Stats, XP, leveling and the roster engine
**Code**
- [ ] `rpg/stats.py`: attributes → derived stats with soft caps (§7.2), and `rpg/skills.py`: skills that improve with use, with perks every 10 levels. *(STA-04 to STA-08)*
- [ ] `rpg/leveling.py`: XP curve, level-difference multiplier, and the level-up screen with live stat previews. *(STA-01, STA-02/03, UIX-06)*
- [ ] pytest: formulas, XP curve monotonic, damage never negative, every enemy JSON valid against its schema. *(TEC-18)*
- [ ] Behaviour **archetypes**: melee-basic, pack-circler, ranged-kiter, caster-support, flyer, ambusher, brute, regenerator, phaser, armored-weakpoint. Add attack tokens so only one or two enemies attack at once. *(ENM-24, CMB-27)*
- [ ] Enemy JSONs for **all 20** (archetype + stats + resistances + attacks + barks + loot). Get at least 8 working in-game. *(ENM-01 to ENM-20)*
- [ ] Barks wired to events (spot, attack, pain, death), with subtitles. *(AUD-03, UIX-10)*

**Asset kitchen:** the remaining enemy barks, then the SFX batch (swings, impacts per material, footsteps per biome, creature noises). *(AUD-05, AUD-06)*

**Done when:** killing rats, wolves, goblins and bandits gives XP, you level up, put a point in Might and see your damage go up.

### Day 5: The world
**Code**
- [ ] `tools/worldgen/scatter.py`: Poisson-disk placement per biome rule (slope, height, density, clearings) → `scatter.json`. Draw it with instancing, culling and two LOD levels. *(WLD-12, TEC-11)*
- [ ] One landmark per biome placed by hand in `data/landmarks.json`, and the Eclipse Spire visible from everywhere. *(WLD-13, WLD-08)*
- [ ] Sky with sun, moon phases and stars, height fog, one shadow cascade, and per-biome grading. *(ART-09, TEC-12, ART-12)*
- [ ] Instanced grass with wind. *(ART-10)*
- [ ] Moonwells: rest, heal, refill flasks, respawn enemies, save, fast travel. *(WLD-09, CMB-22, TEC-16)*
- [ ] Spawn tables per biome with fixed level ranges, plus the activation radius. *(STA-10, TEC-14)*
- [ ] Death loop: the "THE MOON TURNS AWAY" screen, respawn at a Moonwell, dropped essence you can recover. *(UIX-09, CMB-30)*
- [ ] `tools/worldgen/validate.py`: every Moonwell reachable, no spawns on slopes you can't climb. *(WLD-21)*

**Done when:** you can run from Brackenvale to the Frostfang foothills, meet enemies of the right level along the way, die, and get your XP back.

### Day 6: Beast form, HUD and sound
**Code**
- [ ] Bloodlust meter (shown as the scar glow and on the HUD), the transform with a camera swap, the beast moveset, feeding, and silver vulnerability. *(WLF-01 to WLF-03, WLF-08, WLF-13, HER-04)*
- [ ] HUD: bars, quick slots, lock reticle, enemy plates, boss bar. Draw it with pygame and upload it as a texture. *(UIX-01, UIX-04, UIX-05, UIX-13)*
- [ ] Hand crossbow (aim mode, bolts) to bring down fliers. *(CMB-20)*
- [ ] Positional audio, per-biome ambience, and music if it's generated. *(AUD-08, AUD-07)*
- [ ] Remaining enemies from the roster in-game (aim for 12+ total by tonight).

**Asset kitchen:** ElevenLabs Music: one exploration track per biome + one combat layer + the boss theme. Finish batch voice takes and run `master.py`. *(AUD-07, AUD-10)*

**Done when:** you can transform mid-fight, tear through a goblin camp, and feed to stay transformed.

### Day 7: Boss, save, build, ship
**Code**
- [ ] **Grimtooth** boss in a Wolfwood clearing behind a silver mist gate: two phases (duel, then howl-summon + tree leaps). *(BOS-01, BOS-08)*
- [ ] Save/load (JSON with a version number), a title screen, pause menu, and a minimal settings screen. *(TEC-16, TEC-23, UIX-07)*
- [ ] PyInstaller onedir build. Test it on a machine without Python, then `butler push` to itch (set to restricted or draft if you're not ready to make it public). *(TEC-21, REL-08)*
- [ ] Push to GitHub: README with controls, CREDITS.md generated from the logs, AI disclosure. *(TOL-06, REL-02, REL-03)*

**Done when:** a friend can download the zip and play for 20–40 minutes.

---

## 6. If a day overruns: cut in this order

1. Music (use ambience only) → 2. grass → 3. shadows → 4. fast travel → 5. crossbow (fliers come down lower instead) → 6. feeding → 7. enemies 13–20 (move to Week 2).
**Never cut:** hit feel (CMB-14), lock-on, dodge, the parry, beast form, XP and leveling. Those *are* the game.

---

## 7. Starting numbers (tune them in JSON)

### 7.1 XP
```
xp_to_next(L)     = round(100 * L ** 1.5)                 # L1→2: 100, L10→11: 3162, L20→21: 8944
enemy_xp(lvl)     = round(12 * lvl ** 1.35)               # rat L1: 12, spider L5: 106, golem L16: 512
level_mult(d)     = clamp(1 + 0.12 * d, 0.25, 2.0)        # d = enemy_level - player_level
elite             = x2,   boss = x10,   Blood Moon = x1.5
```

### 7.2 Attributes → derived stats (all attributes start at 10)
```
soft(x) = x if x <= 20 else 20 + (x-20)*0.6 if x <= 40 else 32 + (x-40)*0.25
HP          = 300 + 30 * soft(Vigor)
Stamina     = 90  + 3  * soft(Endurance)
EquipLoad   = 40  + 1.5 * Endurance
Crit chance = 5% + 0.4% * soft(Finesse) + 0.6% * soft(Fortune)
Bloodlust gain mult = 1 + 0.02 * soft(Spirit);  beast duration = 20 s + 0.5 s * soft(Spirit)
```

### 7.3 Damage
```
raw   = weapon.base * motion_value * (1 + scaleMight*soft(Might)/40 + scaleFinesse*soft(Finesse)/40)
        * (1 + skill_level/200)                                  # use-based skill bonus
after = raw * raw / (raw + target.defense)                       # flat defence falls off on big hits
final = after * (1 - target.resist[type]) * crit(2.0 / backstab 2.5 / riposte 3.0)
poise_damage = attack.poise * (1 + soft(Might)/60)
```

### 7.4 Skills improve by use
Each skill goes from 1 to 100. `skill_xp_needed(s) = 25 + 2.5*s`. XP per event: a hit is +1 (+2 on a crit), a successful block +1, a dodge that avoids a hit +2, a parry +5, a kill in beast form +3. Perk choices at 10, 20, …, 100.

---

## 8. Data shapes

**`data/enemies/bandit_brigand.json`**
```json
{
  "id": "bandit_brigand", "name": "Bandit Brigand", "archetype": "melee_basic",
  "level": 3, "biomes": ["vale", "roads"], "model": "models/bandit.glb",
  "stats": { "hp": 220, "poise": 30, "defense": 25, "stamina": 100 },
  "resist": { "slash": 0.0, "strike": 0.0, "pierce": 0.0, "fire": 0.0, "frost": 0.0, "silver": 0.0 },
  "ai": { "aggro_range": 18, "reaction_ms": 380, "block_chance": 0.35, "parry_chance": 0.0, "flee_hp": 0.0 },
  "attacks": ["bandit_slash", "bandit_overhead", "bandit_shield_bash"],
  "barks": { "spot": "bandit_spot_*", "attack": "bandit_effort_*", "pain": "bandit_pain_*", "death": "bandit_death_*" },
  "loot": "bandit_common", "xp_mult": 1.0
}
```

**`data/attacks/rowan_ls_light1.json`** (frames at 60 Hz)
```json
{
  "id": "rowan_ls_light1", "anim": "attack_light_1", "stamina": 14,
  "windup": 9, "active": 5, "recovery": 16,
  "cancel": { "into_light": [18, 30], "into_dodge": [20, 30] },
  "hitbox": { "bone": "hand_r", "shape": "capsule", "radius": 0.12, "from": [0, 0, 0], "to": [0, 1.05, 0] },
  "damage": { "type": "slash", "motion_value": 1.0 }, "poise": 12, "parryable": true,
  "hitstop_ms": 60, "shake": 0.15, "sfx": "swing_light"
}
```

**`assets/manifest.json` (Meshy)**
```json
{ "style": "stylized dark-fantasy, hand-painted textures, chunky readable silhouette, muted earthy palette, game-ready low-poly",
  "items": [
    { "id": "rowan_human", "kind": "character", "prompt": "...", "polycount": 25000, "rig": "humanoid",
      "animations": ["idle", "walk", "run", "roll", "attack_light_1", "..."] },
    { "id": "tree_wolfwood_pine_a", "kind": "prop", "prompt": "...", "polycount": 1500 }
  ] }
```

**`data/lines.csv` (ElevenLabs)**
```
id,speaker,text,tags,takes
rowan_levelup_01,rowan,"Stronger. Doesn't mean better.",,3
bandit_spot_01,bandit,"[shouting] Oi! Nice coat — I'll take it!",,2
hunger_feed_01,hunger,"[whispers] Go on. You're hungry. I can feel it.",,3
```

---

## 9. Asset budget for the First Playable

| Kind | Count | Source |
|---|---|---|
| Rowan (human + beast) | 2 rigged characters | Meshy image-to-3D or text-to-3D, plus rigging and animation |
| Enemies | 20 (+ Grimtooth) | Meshy. Humanoids rigged by Meshy; animals and creatures animated in code (ART-04) |
| Props | ~40 (6–8 per biome, plus shared items) | Meshy |
| Terrain textures, sky, grass, particles, LUTs | all | Python scripts (ART-08 to ART-13) |
| Voice lines | Rowan ~40, enemy barks ~14 × 12 voiced types ≈ 170, ×2–3 takes | ElevenLabs TTS |
| SFX | ~80 | ElevenLabs Sound Effects |
| Music | 4 biome tracks + 1 combat layer + 1 boss | ElevenLabs Music (or ambience only) |

Check your Meshy and ElevenLabs credit balances against this list on Day 1. Generate **previews** first and refine only the ones you keep.

---

## 10. After Week 1

| Phase | Focus | Key ideas |
|---|---|---|
| **Week 2: Finish M1** | All 20 enemies, elites, every bark, balance sim, settings, bug fixes, devlog #1 | ENM-01 to ENM-25, TOL-04, UIX-12, REL-07 |
| **Weeks 3–5: M2 Vertical slice** | Prologue, the Hunger, Wolfwood Seal dungeon (kit + grappling chain), Brood Queen, compass, bestiary, music layers | STY-05, STY-06, WLD-14, WLD-15, BOS-02, UIX-02, UIX-08, AUD-07 |
| **Weeks 6–8: M3 Demo** | Blackmire Seal + Old Mother Mire, Inquisitor duel #1, Blood Moon nights, moon phases, scent senses, perks | BOS-03, BOS-06, STY-11, WLF-04, WLF-05, STA-08 |
| **Later: M4** | Frostfang and Ashen Seals, the Crypts, Spire, Lycaon, endings, armor swaps, mount, fishing, Lua mods | STY-08, BOS-04, BOS-05, BOS-07, HER-07, CMB-32, WLD-22, TEC-20 |

---

## 11. Risks

| Risk | What to do |
|---|---|
| Python too slow with many skinned enemies | GPU skinning, numpy for animation sampling, activation radius, cap of about 25 active enemies. Profile before optimising (TEC-19). |
| Meshy rigs or animations don't import cleanly | Normalize every GLB in `normalize.py`. Test the import on Day 2 with Rowan before batching the rest. Fall back to procedural animation (ART-04). |
| AI models don't look like they belong together | One style suffix, the same toon ramp and rim light, shared fog and grading (ART-02, ART-15). Re-roll the outliers. |
| Combat doesn't feel good | Tune hitstop, wind-ups and the input buffer *before* adding content. Playtest every day. |
| Credit burn | Previews first, caching by hash, never re-generate a line whose text hasn't changed. |
| Asset terms change | Log plan and date per asset; re-read both services' terms before each public release (REL-04). |
| Scope creep | Anything not ⭐ waits until M1 ships. Add new ideas to IDEAS.md, where they start as Awaiting. |
