# Lycantrope — under the hood

This file explains how the game works and why it's built the way it is. It skips anything you can learn by
reading a function's name, and spends its time on the parts that are surprising: the tricks that keep
20,000-triangle trees affordable in Python, how assets are generated, and the rules that decide what's in
data versus code. For the design see [IDEAS.md](IDEAS.md); for the plan see [ROADMAP.md](ROADMAP.md).

---

## 1. The shape of the program

- **Python + pygame-ce + moderngl, OpenGL 4.3.** pygame-ce opens the window and reads input; moderngl
  draws everything. 4.3 is needed for the compute shaders used by occlusion culling (§3.5).
- **A fixed 60 Hz simulation, rendering as fast as it can** ([core/timing.py](src/lycantrope/core/timing.py)).
  `FixedStep.advance` banks real time and returns how many 1/60 s steps to run; rendering interpolates
  between the last two steps with `alpha`. One consequence: when frames get slow, the game runs *more*
  simulation steps per frame to catch up, which makes frames slower still (capped by `max_steps`). Keep that
  in mind when profiling: a slow render shows up as a slow update too.
- **The simulation never touches the GPU; the renderer only reads state.** Everything in `world/`
  (actors, combat, stats, inventory, collision) is plain Python and is tested without a window. Everything in
  `render/` and `ui/` draws.
- **Content is data.** Enemies, weapons, armor, poise rules, loot tables, prop placements, sky colours and
  music settings live in JSON under [data/](data/). Code supplies behaviour; the JSON supplies numbers. Most
  tuning never touches Python (the poise fix, for example, is a block in `combat.json`).
- **Coordinates:** the game uses OpenGL's x = east, y = up, z = south. The world generator and the data
  files use [east, north], so every loader flips the sign (`z = -north`). Bearings and the camera's yaw are
  clockwise from north.

`main.py`'s `App` owns everything and runs the loop: handle events → `update` (N fixed steps) → `render`.
The pause menu and Waystone list stop the world simply by making `update` return early.

---

## 2. The world

**Generation (offline).** [tools/worldgen/terrain.py](tools/worldgen/terrain.py) turns
`data/world/layout.json` (biome sites, roads, Waystones, landmarks) into a 4 × 4 km world at 1 m per pixel:
domain-warped biome regions, a different noise recipe per biome, a ring of mountains at the edge, thermal
erosion, roads carved along Catmull-Rom splines, and flat pads under Waystones and landmarks. It writes
16-bit `height.png`, `biome.png`, `road.png`, a water map and `meta.json`. Ground textures are made in
numpy too ([textures.py](tools/worldgen/textures.py)), so the terrain cost no art and no credits.

**Terrain on the GPU** ([render/terrain.py](src/lycantrope/render/terrain.py)). The whole heightmap is one
float texture. The CPU only decides which 64 m chunks are visible and at which of 5 detail levels; all
chunks of one level share a single flat grid mesh that the vertex shader lifts from the height texture.
That's **5 instanced draw calls for the entire terrain**, with skirts hiding the cracks between levels.

**Grass with no CPU cost** ([render/grass.py](src/lycantrope/render/grass.py)). The grass is a grid of
1.5 m cells that follows the camera, snapped to whole cells so tufts don't swim. The vertex shader hashes
each cell's world position for its jitter, turn and size, reads the height, biome, slope, water and road
maps, and shrinks the tuft to nothing where grass shouldn't grow. A large noise field makes tall patches,
and wind bends the tips. Nothing about grass is stored anywhere.

**Props and placement** ([world/props.py](src/lycantrope/world/props.py)). `data/world/placements.json`
is a list of groups anchored to landmarks: single props (`"id"`), lines (fences, walls), random rings
(`"scatter"`, optionally clustered into `"groves"`), and `"shore"` placement along rivers and lakes. Placement
avoids roads, steep ground and other props. A scatter entry can list several models; each placement
picks one at random. Adding a model to a list therefore reshuffles where the existing ones land.

**Collision** ([world/collision.py](src/lycantrope/world/collision.py)). Every prop with a `"collide"` shape
becomes a 2D circle or box on the ground, filed in an 8 m grid (with a margin for the widest character),
so a lookup reads a single cell. Trees use `"top"` so they block the camera only at the trunk.

---

## 3. How 20,000-triangle trees run in Python

Brackenvale has roughly 700 trees around the village. Each HD Tripo tree is 18–20k triangles. Drawn naively,
that's around 14 million triangles of trees alone. Five layers keep it to a fraction of that, and most of
the work happens once, at load time or build time.

### 3.1 One draw call per tree model (instancing)

[render/props.py](src/lycantrope/render/props.py) uploads each model once and draws every copy with a single
instanced call, passing position, rotation, scale, brightness and a height-only "stretch" per instance.
One model therefore gives tall, squat and slim variants for free. Per frame, the CPU only writes the
instance rows that survived culling.

### 3.2 Culling with numpy

Props never move, so each instance's bounding-sphere centre and radius are computed once. Every frame,
for each model:
1. A box around *all* its copies is tested first (`all_far`), so whole species far away cost nothing.
2. Distance and the six frustum planes are tested for all copies at once as numpy array maths. No Python
   loop over instances.

### 3.3 Three versions of every tree, by distance

| Distance | What's drawn | Triangles |
|---|---|---|
| under 90 m | the full model | ~19,000 |
| 90–150 m | a simplified copy built by `tools/props/build.py` | ~6,300 (a third) |
| 150–400 m | a **flat cut-out** (impostor) | 2 |
| beyond 400 m | nothing (dissolved with a dither) | 0 |

**The simplified copy.** `build.py` welds the mesh and runs `fast_simplification` down to a third.
The simplifier throws away texture coordinates, so each new vertex borrows the UV of the nearest original
vertex, found with a KD-tree (`scipy.spatial.cKDTree`). That's crude, but invisible at 90 m.

**The cut-outs** are the biggest win. When the game loads, each tree (any prop whose ID starts with `TRE`)
is rendered from **8 angles** into a strip of pictures by
[impostor_bake.vert/frag](src/lycantrope/render/shaders/): orthographic, 256 px tall, into two textures
at once (multiple render targets):
- **colour**, plus coverage in alpha;
- **the surface normal in that view's frame** (right, up, toward the viewer).

At draw time, [impostor.vert](src/lycantrope/render/shaders/impostor.vert) turns one quad per tree about
the vertical axis to face the camera. [impostor.frag](src/lycantrope/render/shaders/impostor.frag) works
out which way the camera sits *in that instance's own rotated frame*, picks the two nearest captured views
and blends them. It then converts each view's stored normal back to a world normal and **lights it with the
same sun, ambient and fog as the real model**, so a distant oak at sunset matches a near one. Three details
make it hold up:
- Edge pixels are blended with the empty background, which darkens them. The shader divides colour and
  normal by alpha ("premultiplied" recovery) to undo the dark halo.
- The last 15% of the draw distance dissolves with a screen-space dither instead of popping out, because
  the fog is thin (only ~20% at 400 m).
- Cut-outs of every species are drawn together after the real meshes, so the shader program switches once.

Measured on the village view: prop triangles went from 388k to 157k, with no visible difference from
ground level.

### 3.4 Smooth shading that actually comes from the model

Props are drawn from an unindexed vertex stream (`flat_mesh` in props.py). Originally every triangle got
its own face normal, which made HD leaf cards look like hard shards. Now the loader passes each model's
own smooth vertex normals through, and the `flat_shade` setting can still facet everything in the shader
(`dFdx`/`dFdy` of the world position). The same normals feed the cut-out bake.

### 3.5 Hi-Z occlusion culling (compute shaders)

[render/hiz.py](src/lycantrope/render/hiz.py), active when `pixel_scale ≥ 2`. After the 3D pass, the depth
buffer is copied into a "max-depth" mip pyramid: a compute shader keeps the farthest depth of each 2×2
block, level after level. The CPU downloads a small level, and the next frame tests each surviving tree's
nearest point against it. A tree entirely behind a hill or a house is skipped. Because the test uses the
*previous* frame's depth, culling lags one frame, which is invisible at walking speed. Frame 0 culls nothing.

### 3.6 Keeping Git LFS small

Tripo's textures are 2K JPEGs (~0.9 MB). trimesh re-saves textures as PNG (~4.4 MB), and the simplified
copy carried a second copy. `build.py` now:
- writes the **source JPEG bytes back into the built GLB untouched** (`jpeg_textures` rewrites the GLB's
  binary chunk and buffer views directly), so there's no quality loss;
- gives the simplified copy a 4×4 placeholder texture, since the game draws it with the main model's
  texture anyway.

The result is ~3.4 MB of LFS per tree instead of ~9 MB. The loader's mesh cache (`assets/cache/*.npz`) is
keyed on file size and modified time, so rebuilt models are picked up automatically.

---

## 4. Characters

- **Clips are baked at load** ([render/gltf.py](src/lycantrope/render/gltf.py)): every animation becomes a
  table of joint world matrices at 30 fps, so playing a clip is one interpolation per frame. Skinning
  happens in the vertex shader (up to 64 joints).
- **Retargeting by joint name.** Meshy's humanoids share a 24-joint rig, so clips move between characters
  by copying rotations and scaling the hips' translation by the ratio of hip heights. Root motion is
  stripped; code moves the character.
- **Procedural animation for what has no clip** ([render/procedural.py](src/lycantrope/render/procedural.py)):
  swimming and mirrored (left-handed) moves are posed by aiming bones in the character's own frame and
  saved as an ordinary looping clip.
- **Armor is split by bone weights.** An outfit mesh is fitted onto Rowan's skeleton, each triangle is
  assigned to head, arms, torso or legs by which joints move it, and body parts under armor aren't drawn.
  Fitted results are cached in `assets/cache/`.
- **Enemies** run a small state machine (wander → chase → attack → recover) in
  [world/actors.py](src/lycantrope/world/actors.py). A shared pool of 2 attack tokens stops a pack from
  all biting at once.

---

## 5. Combat, stats and items

- **Damage** ([world/stats.py](src/lycantrope/world/stats.py)) is `atk² / (atk + def)` per damage type,
  never less than 10% of the attack, so armor matters without making anything immune. A swing hurts only
  during its "active" window (a fraction of the clip, from `combat.json` `"moves"`), once per target.
- **Poise.** Every hit chips poise; at zero the target staggers. Three rules keep packs from stun-locking
  Rowan, all tunable in `combat.json` `"poise"`:
  - poise refills gradually 1 s after the last hit;
  - after a stagger Rowan can't be staggered again for 1.5 s (enemies get no such grace, so combos still
    work on them);
  - hits during his own swing do half poise damage.

  This was tuned with a scripted fight against a 5-wolf pack in the real game. Before, 60–75% of Rowan's
  swings were cut short; after, none were, while standing still in a pack still gets him staggered.
- **Requirements never block equipping.** Below a weapon's requirements it loses all scaling and every
  attack costs 25% more stamina (WPR-03). Under-requirement armor gives half defence and poise and weighs
  50% more (ARS-01). Equip load sets the roll class (fast / medium / slow).
- **Inventory** ([world/inventory.py](src/lycantrope/world/inventory.py)) builds one item catalogue from
  `combat.json` (weapons, shields, armor, food) plus `data/items.json` (currency, materials, rarities,
  descriptions). The backpack holds 20 stacks; currency lives in a separate purse. `Progress.food`,
  `.armor` and `.shield` are read-only views onto the inventory, so older code kept working unchanged.
- **Loot** comes from `data/loot.json` tables (one per enemy type, plus chest tiers); each entry rolls
  independently. A chest is a placed prop with a `"chest"` block and only exists once its model is built.

---

## 6. Saving, dying and resting

- A save is Rowan's **progress snapshot** (level, XP, attributes, flask, discovered places, opened chests,
  inventory) plus a respawn point ([core/save.py](src/lycantrope/core/save.py)).
- **Dying loads the last save** (STA-28): XP isn't lost; it rolls back. The same snapshot is kept in
  memory, so a death never reads the disk.
- **Resting at a Waystone** heals fully, refills the flask, respawns every enemy (the same reset the death
  reload uses, `respawn_enemies`) and saves. Fast travel saves at the destination, so you wake there.
- Old saves without an inventory are rebuilt from Rowan's starting kit.
- **Test runs never write saves:** `--bench` and `--screenshot` skip the disk write.

---

## 7. Drawing the interface

All UI (HUD, compass, map, menus, loot labels) is drawn with plain pygame onto small surfaces, uploaded as
textures and shown through one tiny overlay shader ([ui/overlay.py](src/lycantrope/ui/overlay.py)). Each
element is redrawn only when what it shows changes (the HUD compares bar lengths in whole pixels; the
compass redraws when the yaw moves half a degree). The **world map is generated from the heightfield at
load**: biome colours, hill shading from the height gradient, a contour every 50 m, water, roads, and a
parchment tint. No map art exists.

**Pixel look** ([render/pixelbuffer.py](src/lycantrope/render/pixelbuffer.py)): with `pixel_scale ≥ 2` the
3D scene renders to a smaller framebuffer and is scaled up (nearest or smooth). The UI is drawn afterwards
at full resolution, so text stays crisp.

---

## 8. How the assets are made

API keys (`MESHY_API_KEY`, `ELEVENLABS_API_KEY`) are only ever environment variables or `.env`; no tool
prints them. Every paid tool is a **dry run by default**: it lists what it would make and the credit
estimate, and only `--send` spends. `batch.py` (Meshy) and `npc_lines.py` (voice lines) also make you type
the credit total before sending.

### 8.1 3D models: Tripo3D through the Tripo MCP (current pipeline for trees)

Claude Code talks to Tripo Studio through the Tripo MCP server (`tripo_text_to_model` and friends), which
spends the Studio account's credits.

**Settings used:** HD family, model `v3.1-20260211`, texture on at `standard` (2K), `delight: true`
(removes baked-in lighting so the game's sun lights the model), triangles (`quad: false`), `face_limit`
20,000. Smart Mesh (Nexus) was tried and rejected: clean, but leaves came out as flat angular shards.

**Prompt template:**
```
A single <species> standing alone, <trunk: shape, bark>, <crown: shape>, <foliage described as
"distinct/separate leaf clusters with gaps between them", leaf shape readable at the edges>,
<one or two distinguishing details>. Stylized semi-realistic fantasy style, hand-painted textures,
<palette>. No ground plane, no base, no background.
```
Example (the HD Brackenvale Oak):
```
A single broad old English oak tree standing alone, thick gnarled trunk splitting into several heavy
twisting limbs, wide rounded canopy made of many distinct layered leaf clusters with visible gaps where sky
shows through, individual leaf shapes readable on the cluster edges, deeply furrowed grey-brown bark with
moss on the lower trunk, exposed roots at the base. Stylized semi-realistic fantasy style, hand-painted
textures, muted earthy greens and browns. No ground plane, no base, no background.
```
Lessons so far:
- "Separate clusters with gaps" is what stops canopies from coming out as solid clumps.
- Small decorative extras (blossom, berries, "thorny") made the hawthorn fail three times; the plain
  version worked first time. The apple tree's apples were fine.
- Tripo fails a task now and then and refunds it. Retry with a **new** idempotency key (reusing the old key
  just returns the failed task).
- If the connection drops mid-submit, look the task up by its idempotency key before sending again, so
  nothing is charged twice.

**From Tripo to the game:**
1. Tripo delivers a meshopt-compressed GLB (`EXT_meshopt_compression`), which the loader can't read.
   Decompress it with `npx -y gltfpack@0.22.0 -i source_meshopt.glb -o model.glb -noq -kn -km -ke`.
2. Save as `assets/models/meshy/<ID>/tripo/v<N>/model.glb` (the folder name is historical; Tripo and Meshy
   models share it).
3. Add an entry to [data/props.json](data/props.json): source, height, and a trunk collision circle
   measured from the mesh (the radius at 8–18% of its height).
4. `.venv\Scripts\python.exe tools/props/build.py <key>`: scales to height, puts the pivot at the bottom
   centre, writes the full and simplified versions with the JPEG texture kept.
5. Add the key to a scatter list in `placements.json`.

### 8.2 3D models: Meshy (characters, buildings, older props)

[tools/meshy/batch.py](tools/meshy/batch.py) is the Meshy front end:
- Prompts come from the tracker files (OBJECTS.md and the rest), and **only approved IDs are sent**.
- Every prompt gets the shared style line appended: *"stylized dark-fantasy, hand-painted textures,
  chunky readable silhouette, muted earthy palette, game-ready low-poly"*.
- `preview` makes the untextured mesh, `texture` refines it at 2K, and `animate` runs texture → rig →
  animation clips for characters.
- Every task is recorded in `assets/meshy/tasks.json`, so later steps reuse preview task IDs. If a submit
  times out, `find_recent_task` looks for a matching task created since the submit started before
  resubmitting.

Results land in a git-ignored drafts folder. [keep.py](tools/meshy/keep.py) copies only what the game
actually uses into the tracked folder, so LFS doesn't fill with rejects. Also in `tools/meshy/`:
[reduce.py](tools/meshy/reduce.py) (free local decimation to a budget), [thumbnail.py](tools/meshy/thumbnail.py)
and [animsheet.py](tools/meshy/animsheet.py) (offscreen renders for checking models and clips), and
[use_textures.py](tools/meshy/use_textures.py) (switches props to textured versions and rebuilds them).

### 8.3 Sound: ElevenLabs

- **Voices** ([design_voices.py](tools/voice/design_voices.py)): designed from text descriptions, never
  cloned. It makes previews; `keep` saves the chosen one and records its ID in `data/voices.json`.
- **Lines** ([npc_lines.py](tools/voice/npc_lines.py)): `assets/audio/vo/manifest.json` remembers the text
  each file was made from, so editing one line remakes just that line.
- **Sound effects** ([voice/sfx.py](tools/voice/sfx.py)) and **music** ([music/make.py](tools/music/make.py)):
  the music prompt files are the API request bodies as-is.

In game, [audio/sfx.py](src/lycantrope/audio/sfx.py) turns what characters do (a new attack clip, a
footfall timed to the walk cycle, a splash) into positional cues, and
[audio/music.py](src/lycantrope/audio/music.py) crossfades a combat layer in when enemies give chase.

### 8.4 Made in code (no credits)

Terrain, ground textures, sky, water, grass, the world map and the Rite effect are all procedural.
[tools/props/plants.py](tools/props/plants.py) can still build small plants from primitives (the ferns and
reeds); the code-made flowers and brambles were removed from the world for clashing with the HD trees.

---

## 9. Working on the game

- **Run:** `.venv\Scripts\python.exe -m lycantrope`
- **Test flags:** `--bench N` (frame timing), `--screenshot FILE --frames N`, `--cam X,Z,YAW,PITCH,HEIGHT`
  (free-fly start), `--time 13`, and `--act <action>` for scripted setups (`fight`, `inventory`, `loot`,
  `waystone`, `map`, `levelup`, `teleport:X,Z`). Benchmarks are only comparable with nothing else using the
  GPU; a screen recorder alone added ~12 ms per frame.
- **Shaders hot-reload** with F5 in free-fly mode; `#include "common.glsl"` shares lighting and fog.
- **Tests:** `.venv\Scripts\python.exe -m pytest -q`. Everything under `world/` is covered without a
  window.
- **The idea tracker** ([tools/idea_tracker.py](tools/idea_tracker.py)) is the source of truth for what's
  approved: `ideas_status.json`, read by both the GUI and `batch.py`.

---

## 10. Gotchas

- Changing a scatter list reshuffles every placement in that group (one seeded RNG per group).
- The full-model distance (90 m), cut-out distance (150 m) and tree draw distance (400 m) are constants at
  the top of `render/props.py`. Raising the draw distance is cheap now, at 2 triangles per tree.
- Occlusion culling only runs when `pixel_scale ≥ 2`, because it needs the low-res depth texture.
- Equipment changes stats only; Rowan's visible outfit and held sword come from `characters.json`
  (HER-07 swaps come later).
- Only Brackenvale Crossroads has a Waystone model; the other Waystones work, but there's nothing to see.
