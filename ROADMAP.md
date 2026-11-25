# LYCANTROPE — Implementation Roadmap

> Python 3.11+ · pygame-ce + moderngl · Meshy (models) · ElevenLabs (voice, SFX, music) · MIT · free on itch.io

The roadmap refers to ideas by their ID in [IDEAS.md](IDEAS.md) (for example **CMB-04**). When you **deny** an idea in the tracker, the matching tasks are dropped or replaced when the roadmap is next updated. **Awaiting** ideas marked ⭐ are assumed *in* until you say otherwise, because the week can't wait for every decision.

---

## 0. Decisions needed before Day 1

These change code or assets on Day 1–2, so please decide them in the tracker first:

| Decide | Options | Why it matters now |
|---|---|---|
| Rowan's gender and voice | Decided: **HER-03**, a man | Meshy model prompt and ElevenLabs voice design run on Day 1 |
| Where you level up | Decided: **STA-02**, anywhere | Level-up UI and death loop |
| pygame or pygame-ce | **TEC-01** | Install step; pygame-ce is recommended |
| First boss | **BOS-01** Grimtooth (recommended: it shares the Werewolf enemy's rig) or another | Asset kitchen queue on Day 2 |
| Asset licence | **REL-01**, **REL-04** | What goes in the public repo |

You also need:
- **API keys** set as environment variables: `MESHY_API_KEY` and `ELEVENLABS_API_KEY`. Never paste them into files that get committed.
- **Git + Git LFS** installed, an empty GitHub repo, an itch.io project page (can be set to draft), and **ffmpeg** on your PATH (used for audio mastering).

---

## 1. Milestones

| Milestone | Target | What "done" means |
|---|---|---|
| **M0 Foundations** | Day 1 | Repo, venv, window with a GL context, fixed-step loop, terrain on screen, asset pipelines running |
| **M1 First Playable** | End of Week 1 (core) + Week 2 (full roster) | Rowan with the Dawnblade, crossbow and Rites, 4 biomes on one map, **20 approved enemies** with voiced barks at levels 1–15, XP/levels with no NPC, 6 attributes + 8 use-based skills that change combat, Waystones, one boss, save/load, Windows build on itch |
| **M2 Vertical Slice** | Weeks 3–5 | Act I opening: farm chores, the mentor, the first incursion at the burying ground with rift sealing, plus the first Crown Shard dungeon (Wolfwood) with its tool (grappling chain), the Brood Queen boss, music, bestiary, compass |
| **M3 Public Demo** | ~Week 8 | The rest of Part I (the waking world): the stone circle and the galley incursions, the Shantak Rider, the second waking-world Crown Shard (Blackmire), the Brackenvale sidequests, relic powers, polish pass, settings and accessibility, devlog push |
| **M4 Full Game** | Later | Part II (the Dreamlands): the descent through sleep, the two Dreamlands Crown Shards, fallen Serannian restored; then the return, the Crypts, Duskhold, Malgrath, the ending that hints at the unseen hand, NG+ |

**Week 1 is about proving the core.** By Sunday you should have a downloadable build in which Rowan explores four biomes, fights about 12 enemy types, levels up, casts a Rite and kills a boss. **Week 2** finishes the roster to all 20, adds the rest of the voice lines, and tunes balance. With the Meshy and ElevenLabs batches running in the background all week, that is ambitious but achievable. The cut list (§6) says what to drop first if a day overruns.

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
                                  worldgen → height.png + biome.png + road.png + meta.json (+ scatter.json)
```

**Rules that apply throughout** (TEC-04 to TEC-07):
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
│   ├── world/      heightfield.py  biomes.py  scatter.py  collision.py  waystones.py  spawns.py
│   │               incursions.py (rifts, waves, sealing: M2)
│   ├── combat/     attacks.py  hitbox.py  damage.py  status.py  lockon.py  feel.py (hitstop/shake)
│   ├── actors/     actor.py  player.py  valor.py  enemy.py
│   │   └── ai/     fsm.py  archetypes.py  tokens.py  steering.py
│   ├── rpg/        stats.py  skills.py  leveling.py  inventory.py  loot.py
│   ├── audio/      mixer.py  voice.py  music.py
│   └── ui/         hud.py  menus.py  levelup.py  subtitles.py  fonts.py
├── data/           enemies/*.json  attacks/*.json  items.json  loot.json  biomes.json  incursions/*.json
│                   xp.json  voices.json  lines.csv  sfx.csv
├── assets/  (Git LFS)  models/  textures/  audio/{vo,sfx,music}/  fonts/  world/
├── tools/
│   ├── idea_tracker.py          ← done
│   ├── meshy/      batch.py  manifest.json  normalize.py  preview.py
│   ├── voice/      design_voices.py  generate.py  sfx.py  music.py  master.py
│   ├── worldgen/   terrain.py  noise.py  scatter.py  validate.py  textures.py
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
- [x] `tools/worldgen/terrain.py` + `data/world/layout.json`: 4 × 4 km world (4096², 1 m/px) with no concept art, built from a layout file. It covers six biomes plus the World's Edge, per-biome noise recipes, the cliff-walled Duskhold crag (about 520 m across), erosion, five graded roads, and flat pads for 11 Waystones and 14 landmarks. Outputs `assets/world/height.png` (16-bit), `biome.png`, `road.png`, `meta.json`, `preview.png`. Tested in `tests/test_worldgen.py`. *(WLD-01, WLD-13)*
- [x] `render/terrain.py`: 64 m chunks drawn as 4 instanced LOD levels with skirts and frustum culling. Splat, slope, snowline, road and shoreline blending of 8 procedural ground textures (`tools/worldgen/textures.py`), plus sky, height fog and water. Free-fly and walk camera, debug overlay, shader hot-reload, `--screenshot`/`--bench`. About 5 ms per frame at 1600×900 on Iris Xe. *(TEC-10, ART-08, TEC-02, TEC-04, TEC-17)*

**Asset kitchen**
- [x] `tools/meshy/batch.py`: text-to-3D **previews** for approved IDs (dry run by default, typed credit confirmation, named sets in `sets.json`, task log in `assets/meshy/tasks.json`, `--model meshy-t2.5` smart topology for hard-edged props, `--full-detail` for foliage). Plus `reduce.py` (local triangle reduction in steps) and `thumbnail.py`. *(ART-01, ART-02, ART-06)*
- [ ] Texturing step: check whether Meshy Retexture accepts our own reduced meshes (10 credits each), else refine the kept previews. Only for previews the user picks.
- [x] Static props in the game: `tools/props/build.py` (scale, pivot, `data/props.json` catalog), `render/props.py` (GLB loading, one instanced draw per prop, culling), `world/props.py` + `data/world/placements.json` (hand-placed items, fence/wall lines with gates, ring scatter). Brackenvale Village and its crossroads are placed with 19 untextured Meshy previews. *(WLD-12, ART-07)*
- [ ] Queue batch 1: **Rowan**, **the Dawnblade** (4 stages, ART-17), Bandit, Goblin, Skeleton, Orc, plus ~12 props (3 tree types per biome, rocks, Waystone, chest, ruined wall).
- [ ] `tools/voice/design_voices.py`: create Rowan and 6 enemy voices with Voice Design. Save `data/voices.json`. *(AUD-02)*

**Done when:** you can fly over a four-biome landscape at 60 fps, and the first Meshy jobs are running.

### Day 2: Rowan moves
**Code**
- [ ] Capsule character controller: ground snapping on the heightfield, slope limit, gravity, jump and auto-jump at ledges, run and sprint. *(TEC-09, WLD-19)*
- [ ] Third-person orbit camera with terrain collision, and lock-on with target switching. *(CMB-01, CMB-02)*
- [ ] Stamina and a dodge roll with i-frames, plus the input buffer. *(CMB-03, CMB-06, CMB-15)*
- [x] `render/gltf.py`: GLB meshes, textures, skins and clips (baked to 30 fps, played in place, retargeted between Meshy biped rigs by joint name). Armor fitting per ARS-05 (Rowan's skin weights copied to the outfit, split into head/arms/torso/legs). *(ART-07, TEC-08)*
- [x] First pass of play mode: third-person orbit camera, camera-relative movement with walk/run/sprint, light ×3 chain, heavy, held block, cast; Rowan wears chainmail set 05 with the Rusty Dawnblade and the Tome of Wards. 10 goblins, 20 wolves and 5 bears around Brackenvale wander, chase, circle and swing (no hitboxes, stats or damage yet). Still to do from this day: capsule controller (slopes, jump), camera collision with props, lock-on, stamina.
- [ ] Controller support through `pygame.joystick`. *(UIX-11)*

**Asset kitchen**
- [ ] Meshy **rigging + animation** for Rowan: idle, walk, run, sprint, roll, light ×3, heavy ×2, block, cast (off hand), hit, death, crossbow aim and shoot. Also queue the Werewolf enemy's rig (shared with Grimtooth). Check the action names in Meshy's current animation library. *(ART-03)*
- [ ] Batch 2 models: Wolf, Rat, Spider, Ooze, Lizardfolk, Troll, Wraith, Yeti, Ogre, Werewolf, Dread Knight, Mimic, Necromancer, Grimtooth.
- [ ] `tools/voice/generate.py` + `data/lines.csv`: Rowan's ~40 lines and the first enemy barks. *(AUD-01, AUD-03, AUD-04)*

**Done when:** Rowan runs, rolls and locks onto a training dummy, and it feels good on both keyboard and mouse and on a gamepad.

### Day 3: Skinning and the combat core
**Code**
- [x] GPU skinning: up to 4 weights per vertex, a 64-joint palette uniform, baked clips with linear interpolation and 0.15 s crossfades. In-place animations, so movement comes from code. *(TEC-08)*
- [ ] `data/attacks/*.json` frame data and `combat/attacks.py` running light and heavy strings with cancel windows. *(CMB-04, CMB-16)*
- [ ] Swept-capsule hitboxes against hurtboxes, and damage resolution. *(CMB-17, CMB-18)*
- [ ] Hit feel: hitstop, camera shake, FOV punch and impact SFX hooks on the event bus (no sparks). *(CMB-14, TEC-06)*
- [ ] Block, guard break, poise and stagger. *(CMB-07, CMB-10)* Rowan's block uses `motion_shield_guard.glb` (custom Meshy motion), with a code-side pose override that raises the left upper arm and forearm so the buckler sits level in front of the face. Meshy's library has no shield guard, and the generated one holds the arm at waist height. Keep the raise angle in data so it can be tuned against the block hit check.
- [ ] The first real enemy: **Bandit Brigand** running the `melee-basic` FSM (idle → alert → approach → strafe → attack → recover, plus stagger and dead). *(ENM-04, TEC-13)*

**If skinning takes more than half a day:** park it and keep going with a rigid "bind pose plus procedural lean and bob" placeholder so combat work isn't blocked. Come back to skinning on Day 5.

**Done when:** you can duel a bandit that blocks, punishes greedy attacks, and staggers under heavy hits.

### Day 4: Stats, XP, leveling and the roster engine
**Code**
- [ ] `rpg/stats.py`: attributes → derived stats with soft caps (§7.2), and `rpg/skills.py`: skills that improve with use, with perks every 10 levels. *(STA-04 to STA-08)*
- [ ] `rpg/leveling.py`: XP curve, level-difference multiplier, and the level-up screen with live stat previews. *(STA-01, STA-02/03, UIX-06)*
- [ ] pytest: formulas, XP curve monotonic, damage never negative, every enemy JSON valid against its schema. *(TEC-18)*
- [ ] Behaviour **archetypes**: melee-basic, pack-circler, ranged-kiter, caster-support, flyer, ambusher, brute, regenerator, phaser, armored-weakpoint. Add attack tokens so only one or two enemies attack at once. *(ENM-24, CMB-27)*
- [ ] Enemy JSONs for **all 20 approved enemies** (archetype + stats + resistances + attacks + barks + loot), plus any `MON-` enemies approved in ENEMIES.md. Get at least 8 working in-game. *(ENM-01 to ENM-22 except the denied ENM-11 and ENM-20)*
- [ ] Barks wired to events (spot, attack, pain, death), with subtitles. *(AUD-03, UIX-10)*

**Asset kitchen:** the remaining enemy barks, then the SFX batch (swings, impacts per material, footsteps per biome, creature noises). *(AUD-05, AUD-06)*

**Done when:** killing rats, wolves, goblins and bandits gives XP, you level up, put a point in Might and see your damage go up.

### Day 5: The world
**Code**
- [ ] `tools/worldgen/scatter.py`: Poisson-disk placement per biome rule (slope, height, density, clearings) → `scatter.json`. Draw it with instancing, culling and two LOD levels. *(WLD-12, TEC-11)*
- [ ] One landmark per biome placed by hand in `data/landmarks.json`, and Duskhold, the Dark Lord's citadel, visible from everywhere. *(WLD-13, WLD-08)*
- [x] Procedural sky: gradient and sun from `data/world/sky.json`, the same sun as the lighting; moon, stars and Duskhold's storm cloud still to come. *(ART-09)*
- [ ] One shadow cascade and per-biome color grading. *(TEC-12, ART-12)*
- [ ] Waystones: rest, heal, refill flasks, respawn enemies, save, fast travel. *(WLD-09, CMB-22, TEC-16)*
- [ ] Spawn tables per biome with fixed level ranges, plus the activation radius. *(STA-10, TEC-14)*
- [ ] Death loop: the "AND SO THE LEGEND ENDED… or did it?" screen, respawn at a Waystone, dropped essence you can recover. *(UIX-09, CMB-30)*

**Done when:** you can run from Brackenvale to the Frostfang foothills, meet enemies of the right level along the way, die, and get your XP back.

### Day 6: Rites, HUD and sound
**Code**
- [ ] Rites cast from the off hand, each on its own cooldown with a HUD timer: 2–3 starter Rites (for example a short ward and a marking sigil). Faith scales radiant damage and shortens cooldowns. Their visuals are Meshy effect meshes (VFX-02 to VFX-04) drawn with a glowing, see-through shader and animated in code. *(CMB-29, CMB-34, STA-20, ART-19)*
- [ ] HUD: bars, quick slots, lock reticle, enemy plates, boss bar. Draw it with pygame and upload it as a texture. *(UIX-01, UIX-04, UIX-05, UIX-13)*
- [ ] Hand crossbow (aim mode, bolts) to bring down fliers. *(CMB-20)*
- [ ] Positional audio, per-biome ambience, and music if it's generated. *(AUD-08, AUD-07)*
- [ ] Remaining enemies from the roster in-game (aim for 12+ total by tonight).

**Asset kitchen:** ElevenLabs Music: one exploration track per biome + one combat layer + the boss theme. Finish batch voice takes and run `master.py`. *(AUD-07, AUD-10)*

**Done when:** you can clear a goblin camp mixing sword combos, the crossbow and a Rite, and time your next fight around its cooldown.

### Day 7: Boss, save, build, ship
**Code**
- [ ] **Grimtooth** boss in a Wolfwood clearing: two phases (duel, then howl-summon + tree leaps). *(BOS-01)*
- [ ] Save/load (JSON with a version number), a title screen, pause menu, and a minimal settings screen. *(TEC-16, TEC-23, UIX-07)*
- [ ] PyInstaller onedir build. Test it on a machine without Python, then `butler push` to itch (set to restricted or draft if you're not ready to make it public). *(TEC-21, REL-08)*
- [ ] Push to GitHub: README with controls, CREDITS.md generated from the logs, AI disclosure. *(TOL-06, REL-02, REL-03)*

**Done when:** a friend can download the zip and play for 20–40 minutes.

---

## 6. If a day overruns: cut in this order

1. Music (use ambience only) → 2. shadows → 3. fast travel → 4. crossbow (fliers come down lower instead) → 5. a second and third Rite → 6. enemies 13–20 (move to Week 2).
**Never cut:** hit feel (CMB-14), lock-on, dodge, block and stagger, XP and leveling. Those *are* the game.

---

## 7. Starting numbers (tune them in JSON)

### 7.1 XP
```
xp_to_next(L)     = round(100 * L ** 1.5)                 # L1→2: 100, L10→11: 3162, L20→21: 8944
enemy_xp(lvl)     = round(12 * lvl ** 1.35)               # rat L1: 12, spider L5: 106, golem L16: 512
level_mult(d)     = clamp(1 + 0.12 * d, 0.25, 2.0)        # d = enemy_level - player_level
elite             = x2,   boss = x10,   Shadow Moon = x1.5
```

### 7.2 Attributes → derived stats (all attributes start at 10)
```
soft(x) = x if x <= 20 else 20 + (x-20)*0.6 if x <= 40 else 32 + (x-40)*0.25
HP          = 300 + 30 * soft(Vigor)
Stamina     = 90  + 3  * soft(Endurance)
EquipLoad   = 40  + 1.5 * Endurance
Crit chance = 5% + 0.8% * soft(Fortune)
Attack recovery = base * (1 - 0.004 * soft(Dexterity))       # up to ~15% faster recovery (STA-16)
Radiant damage mult = 1 + soft(Faith) / 40                   # Dawnblade light, holy water, blessed bolts (STA-20)
Rite cooldown = base * max(0.6, 1 - 0.01 * soft(Faith))       # CMB-34
Lifewater heal = base * (1 + soft(Faith) / 80)
```

### 7.3 Damage
```
raw   = weapon.base * motion_value * (1 + scaleMight*soft(Might)/40 + scaleDex*soft(Dexterity)/40 + scaleFaith*soft(Faith)/40)
        * (1 + skill_level/200)                                  # use-based skill bonus
after = raw * raw / (raw + target.defense)                       # flat defence falls off on big hits
final = after * (1 - target.resist[type]) * crit(2.0)
poise_damage = attack.poise * (1 + soft(Might)/60)
```

### 7.4 Skills improve by use
Each skill goes from 1 to 100. `skill_xp_needed(s) = 25 + 2.5*s`. XP per event: a hit is +1 (+2 on a crit), a successful block +1, a dodge that avoids a hit +2, a Rite that lands +2, a sprint second +0.2 (Athletics). Perk choices at 10, 20, …, 100.

---

## 8. Data shapes

**`data/enemies/bandit_brigand.json`**
```json
{
  "id": "bandit_brigand", "name": "Bandit Brigand", "archetype": "melee_basic",
  "level": 3, "biomes": ["vale", "roads"], "model": "models/bandit.glb",
  "stats": { "hp": 220, "poise": 30, "defense": 25, "stamina": 100 },
  "resist": { "slash": 0.0, "strike": 0.0, "pierce": 0.0, "fire": 0.0, "frost": 0.0, "radiant": 0.0 },
  "ai": { "aggro_range": 18, "reaction_ms": 380, "block_chance": 0.35, "flee_hp": 0.0 },
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
  "damage": { "type": "slash", "motion_value": 1.0 }, "poise": 12,
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
bandit_pain_01,bandit,"[grunts] Argh — lucky shot!",,2
```

---

## 9. Asset budget for the First Playable

| Kind | Count | Source |
|---|---|---|
| Rowan + the Dawnblade (4 stages) | 1 rigged character + 4 sword models | Meshy image-to-3D or text-to-3D, plus rigging and animation |
| Enemies | 20 (+ Grimtooth) | Meshy. Humanoids rigged by Meshy; animals and creatures animated in code (ART-04) |
| Props | ~45 ⭐ objects from [OBJECTS.md](OBJECTS.md) (145 listed in total) | Meshy |
| Terrain textures, sky, color-grading LUTs | all | Python scripts and shaders (ART-08, ART-09, ART-12) |
| Effects (Rites, flames) | ~8 ⭐ meshes from OBJECTS.md §13 | Meshy (ART-19) |
| Voice lines | Rowan ~40, enemy barks ~14 × 12 voiced types ≈ 170, ×2–3 takes | ElevenLabs TTS |
| SFX | ~80 | ElevenLabs Sound Effects |
| Music | 4 biome tracks + 1 combat layer + 1 boss | ElevenLabs Music (or ambience only) |

Check your Meshy and ElevenLabs credit balances against this list on Day 1. Generate **previews** first and refine only the ones you keep.

---

## 10. After Week 1

| Phase | Focus | Key ideas |
|---|---|---|
| **Week 2: Finish M1** | All 20 approved enemies plus approved MON- enemies, every bark, settings, accessibility, bug fixes | ENM list, ENEMIES.md, UIX-12 |
| **Weeks 3–5: M2 Vertical slice** | Act I opening: Rowan's dream of Serannian, farm chores, Aldric arrives (the horror in the jar), Mindspeak, training with Captain Thorne. Rift sealing and incursions as data. The first incursion at the burying ground, fused with the village prologue (zoogs, Men of Leng, Oswin wounded on his doorstep), and its fight, the Unwritten Gate. Then the Wolfwood Crown Shard dungeon (kit + grappling chain), Brood Queen, compass, bestiary, music layers | DRM-03, DRM-10, DRM-11, DRM-06, DRM-16, DRM-18, DRM-19, DRM-12, DRM-54, DRM-35, DRM-36, STY-14, STY-15, WLD-14, WLD-15, BOS-02, UIX-02, UIX-08, AUD-07 |
| **Weeks 6–8: M3 Demo** | Second incursion at the stone circle (ghasts and light, cultists, the Apprentice at the Stones). Third incursion, the galley from the clouds (moon-beasts), ending on the rift that can't be closed from this side, and the Shantak Rider. The Blackmire Crown Shard + Old Mother Mire. Brackenvale sidequests from the public-domain tales, with their creatures. Found documents with clues. Relic powers, Seer's Lens, perks, armor sets | DRM-13, DRM-55, DRM-37, DRM-38, DRM-14, DRM-39, DRM-15, DRM-40, BOS-03, DRM-17, DRM-48, DRM-49, DRM-50, DRM-51, DRM-52, DRM-64, DRM-26, VAL-03, VAL-06, STA-08, ARMOR.md |
| **Later: M4, Part II** | The descent through sleep (the seventy steps, the Cavern of Flame, the Gate of Deeper Slumber). Then the Enchanted Wood (the Hostage-Keeper), Ulthar and its cats, Dylath-Leen (the Factor chase), Celephaïs (Carter, Kuranes and the Silver Key), Ngranek (the night-gaunts), the Underworld (ghouls, gugs, the Gug Warlord, dholes), Leng (the High Priest, the spider). Then Serannian restored (the Wound over Serannian). The two Dreamlands Crown Shards replace two of the original dungeons: Frostfang becomes the ghouls' vault of fallen things, and Ashen Reach becomes Serannian. Optional: the Quarry of Inganok, Kuranes' Dream. | DRM-27, DRM-56, DRM-44, DRM-57, DRM-30, DRM-24, DRM-58, DRM-41, DRM-42, DRM-43, DRM-59, DRM-46, DRM-60, DRM-45, DRM-31, DRM-61, DRM-28, DRM-29, DRM-74, DRM-75 |
| **Later: M4, the end** | The return, the Drowned Coast and its Deep Ones, the Crypts, Duskhold, Malgrath as the final boss, allies who remember coming back for the finale, the Dawnblade's origin (grandfather was the fisherman who found it in his net), the testament frame, and the closing hints that Nyarlathotep arranged everything (never met, never named). Armor swaps, mount, Lua mods | BOS-11, DRM-53, DRM-29, DRM-07, DRM-09, DRM-08, DRM-76, HER-07, CMB-32, TEC-20 |
| **Much later** | Player beast forms: the Dream-Shapes (cat, ghoul, night-gaunt) | DRM-25 |

### 10.1 Story decisions (answered 2026-11-25)

- **The Dawnblade's origin:** grandfather was the fisherman who found it in his net, so STY-14, HER-09 and DRM-07 all hold.
- **The Apprentice is Sir Calder** (STY-19, DRM-08). His appearances are the Apprentice's fights: the Stones, the Factor chase, the High Priest of Leng.
- **Moon-beasts** get a simpler fighting style instead of swelling and shrinking: a plain heavy melee enemy that commands the Men of Leng.
- **The Dreamlands shards:** Frostfang → the ghouls' vault, Ashen Reach → Serannian. BOS-04 (the Wyvern) and BOS-05 (the Colossus) need new homes or replacements.
- **The time loop:** no travel into the past. The Silver Key's last use lets Rowan play through the eyes of the hero of old, who passes something on to the sword. The new ideas are DRM-77 to DRM-82, awaiting your decision. Its daily rewind (DRM-24) restores position and HP only, because Dread was denied.
- **Beast forms (DRM-25)** are allowed but saved for much later, and CLAUDE.md now says so.
- **Deep Ones (DRM-53)** stay, on the Drowned Coast.
- **No Black Tongue lesson** in Act I and no replacement (DRM-10).

**Still awaiting a decision, so not scheduled yet:** the boss framework ideas BOS-12 to BOS-17 (one idea per boss, phase beats, non-kill bosses, retry at the arena door, bosses as data, scripted moves), the bosses BOS-18 (the Thing in the Cellar), BOS-19 (Old Corwin), DRM-66 to DRM-70 (Grandmother Zoog, the Drum-Master's Galley, the Gug Sentinel, the Shantak Roost, the Moon-Beast Admiral), DRM-77 to DRM-82 (the Silver Key and the hero of old), and TOL-08 (teleport to any boss). If BOS-16 is approved, build it before M2's first incursion boss, because every later boss uses it.

---

## 11. Risks

| Risk | What to do |
|---|---|
| Python too slow with many skinned enemies | GPU skinning, numpy for animation sampling, activation radius, cap of about 25 active enemies. Profile before optimising (TEC-19). |
| Meshy rigs or animations don't import cleanly | Normalize every GLB in `normalize.py`. Test the import on Day 2 with Rowan before batching the rest. Fall back to procedural animation (ART-04). |
| AI models don't look like they belong together | One style suffix, shared fog and color grading (ART-02, ART-12). Re-roll the outliers. |
| Combat doesn't feel good | Tune hitstop, wind-ups and the input buffer *before* adding content. Playtest every day. |
| Credit burn | Previews first, caching by hash, never re-generate a line whose text hasn't changed. |
| Asset terms change | Log plan and date per asset; re-read both services' terms before each public release (REL-04). |
| The Dreamlands roughly double the game | Part II is M4 work. Ship the waking-world half (M3) as a complete demo first, and reuse rigs wherever possible: rats for the rats in the walls, the goblin rig for the Lurking Fear, the Brood Queen for the Spider of Leng, one cat model for allies, Ulthar and Saturn. |
| Many new creatures need procedural rigs | Ghasts, moon-beasts, Shantaks, dholes and Things from Beyond are animated in code (ART-04). Prototype one hopper (the ghast) and one big flyer (the Shantak) early in M3, before committing to the rest. |
| Scope creep | Anything not ⭐ waits until M1 ships. Add new ideas to IDEAS.md, where they start as Awaiting. |
