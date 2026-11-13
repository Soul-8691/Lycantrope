# Dream-Quest: Code Templates

The code sketches that go with [DREAM-QUEST.md](DREAM-QUEST.md). They're **descriptive skeletons**: they show the intended shape of each system and the important details. They are not finished code.

Section numbers match the design document. A reference like **§7.3** points to a section in this file, and references to any other section number (§3.2, §12.6, ...) point to DREAM-QUEST.md.

## Contents

- **[Core Systems](#core-systems-dream-questmd-7)** (DREAM-QUEST.md §7)
  - [7.1 Build config](#71-build-config)
  - [7.2 Cython engine core (`engine/core.pyx`)](#72-cython-engine-core-enginecorepyx)
  - [7.3 Lua bridge (`engine/scripting.py`)](#73-lua-bridge-enginescriptingpy)
  - [7.4 Lua card definitions](#74-lua-card-definitions)
  - [7.5 Renderer (pygame + moderngl)](#75-renderer-pygame--moderngl)
  - [7.6 Main game loop (`main.py`)](#76-main-game-loop-mainpy)
  - [7.7 Story pipeline](#77-story-pipeline)
  - [7.8 RL opponent](#78-rl-opponent)
  - [7.9 Balance analysis (scikit-learn + Gambit)](#79-balance-analysis-scikit-learn--gambit)
  - [7.10 Modding tools](#710-modding-tools)
  - [7.11 Tests (pytest)](#711-tests-pytest)
  - [7.12 Packaging (PyInstaller)](#712-packaging-pyinstaller)
- **[Call of Cthulhu RPG Systems](#call-of-cthulhu-rpg-systems-dream-questmd-11)** (DREAM-QUEST.md §11)
  - [11.4 Code template: checks, Composure, Fractures](#114-code-template-checks-composure-fractures)
- **[First-Person Combat](#first-person-combat-dream-questmd-12)** (DREAM-QUEST.md §12)
  - [12.8 Code template: first-person combat](#128-code-template-first-person-combat)
- **[Smart Procedural Environments](#smart-procedural-environments-dream-questmd-13)** (DREAM-QUEST.md §13)
  - [13.4 Code template: procedural environments](#134-code-template-procedural-environments)
- **[Waking-World Horrors](#waking-world-horrors-dream-questmd-14)** (DREAM-QUEST.md §14)
  - [14.9 Code template: Waking-World horrors](#149-code-template-waking-world-horrors)

---

## Core Systems (DREAM-QUEST.md §7)

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

## Call of Cthulhu RPG Systems (DREAM-QUEST.md §11)

*Design: [DREAM-QUEST.md §11](DREAM-QUEST.md#11-ideas-from-the-call-of-cthulhu-rpg)*

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

---

## First-Person Combat (DREAM-QUEST.md §12)

*Design: [DREAM-QUEST.md §12](DREAM-QUEST.md#12-first-person-combat-skyrim--bloodborne)*

### 12.8 Code template: first-person combat

**Attack frame data in Lua** (`content/cards/core/ghoul.lua`, excerpt)
```lua
return {
  id = "core.ghoul", name = "Ghoul", type = "entity", faction = "ghouls", cost = 3,
  horror = "0 / 1d4", creature_kind = "ghoul",
  stats = { hp = 22, atk = 4, speed = 4.0, stamina = 100, poise = 30 },

  body = {
    eye_height = 1.4, fov = 85, head_bob = 0.6,
    senses = "scent_trails",           -- selects post-process shader
    forms = { "upright", "quadruped" },
    dodge = { kind = "burrow", iframes = 14, recovery = 10, stamina = 18, distance = 3.5 },
  },

  -- Frame data at 60 Hz. Hitbox in local space: arc(radius, angle_deg) or capsule.
  moves = {
    upright = {
      light = { startup = 9,  active = 4, recovery = 12, dmg = 5,  poise = 8,
                hitbox = { arc = { r = 1.6, deg = 100 } }, chain = "light2" },
      light2 = { startup = 7, active = 4, recovery = 16, dmg = 6, poise = 10,
                hitbox = { arc = { r = 1.6, deg = 120 } } },
      power = { startup = 24, active = 6, recovery = 26, dmg = 14, poise = 30,
                hitbox = { capsule = { len = 2.4, r = 0.5 } }, knockdown = true },
      transform = { startup = 6, active = 6, recovery = 8, dmg = 7, poise = 15,
                    to_form = "quadruped", hitbox = { arc = { r = 2.0, deg = 180 } } },
    },
    quadruped = {
      light = { startup = 6, active = 3, recovery = 9, dmg = 4, poise = 5,
                hitbox = { arc = { r = 1.3, deg = 70 } }, lunge = 1.5 },
      -- ...
    },
  },

  -- Ghouls feed: devour a fallen card to heal and pull it from the opponent's Abyss.
  utterance = { name = "Meeping Call", cooldown = 25,
                on_use = function(uid) game.fear_cone(uid, 8.0, 60, 2.0) end },

  instincts = {
    { prompt = "FEED", when = "corpse_within_5m", follow_buff = "frenzy_fill_50",
      resist_reward = { sanity = 2 } },
  },
}
```

**Soul Leap and Chorus Chains** (`src/dreamquest/game/soul_leap.py`)
```python
from dataclasses import dataclass, field

CHORUS_WINDOW = 1.5                      # seconds between hits from different hosts
CHORUS_STEPS = [1.0, 1.1, 1.25, 1.5, 1.75, 2.0]
DEATH_THROES = 1.5                       # slow-mo seconds to find a new host

@dataclass
class Chorus:
    links: int = 0
    last_hit_time: float = -99.0
    last_host: int = -1

    def register_hit(self, now: float, host_uid: int) -> float:
        """Return the damage multiplier for this hit."""
        if now - self.last_hit_time > CHORUS_WINDOW:
            self.links = 0
        elif host_uid != self.last_host:          # chain only grows across *different* hosts
            self.links = min(self.links + 1, len(CHORUS_STEPS) - 1)
        self.last_hit_time, self.last_host = now, host_uid
        return CHORUS_STEPS[self.links]

class SoulLeap:
    def __init__(self, world, pid):
        self.world, self.pid = world, pid
        self.chorus = Chorus()
        self.throes_until = None

    def leap(self, target_uid: int):
        w, p = self.world, self.world.players[self.pid]
        target = w.units.get(target_uid)
        if target is None or not target.alive:
            return False
        if target.owner != self.pid and not w.can_dominate(self.pid, target):
            return False
        if p.possessed_uid != -1:
            w.units[p.possessed_uid].echo_order(duration=2.0)   # keep doing last action
            w.units[p.possessed_uid].possessed = False
        target.possessed = True
        p.possessed_uid = target_uid
        w.events.emit("SoulLeap", pid=self.pid, to=target_uid)  # renderer plays leap smear
        self.throes_until = None
        return True

    def on_host_died(self, now: float):
        self.throes_until = now + DEATH_THROES
        self.world.set_time_scale(0.2)

    def update(self, now: float):
        if self.throes_until is not None and now >= self.throes_until:
            self.world.set_time_scale(1.0)
            self.world.change_sanity(self.pid, -8)              # dying in a dream
            self.world.players[self.pid].possessed_uid = -1     # thrown back to the Altar
            self.throes_until = None
```

**Reclaim and Severance** (in `engine/core.pyx` or `engine/combat.pyx`)
```cython
DEF RECLAIM_WINDOW = 3.0
DEF RECLAIM_RATIO = 0.6       # fraction of each hit's damage that's reclaimable

cdef class CombatState:
    cdef public double reclaimable, reclaim_timer, frenzy, stamina, poise
    cdef public int attack_frame, parry_open_until
    cdef public str current_move, form

cpdef void on_damaged(World w, Unit u, int amount):
    u.combat.reclaimable += amount * RECLAIM_RATIO
    u.combat.reclaim_timer = RECLAIM_WINDOW

cpdef void on_hit_landed(World w, Unit attacker, Unit victim, int dmg):
    cdef double back
    # Hitting back during the window wins back health.
    if attacker.combat.reclaim_timer > 0 and attacker.combat.reclaimable > 0:
        back = min(attacker.combat.reclaimable, dmg * 0.5)
        attacker.hp = min(attacker.max_hp, attacker.hp + <int>back)
        attacker.combat.reclaimable -= back
    attacker.combat.frenzy = min(100.0, attacker.combat.frenzy + 8.0)

cpdef bint try_severance_parry(World w, Unit parrier, Unit target):
    """Off-hand hit during the target's wind-up -> stagger -> critical available."""
    if target.combat.current_move is None:
        return False
    move = w.script.move_data(target, target.combat.current_move)
    if target.combat.attack_frame < move["startup"] - move.get("parry_window", 6):
        return False                              # too early
    if target.combat.attack_frame >= move["startup"]:
        return False                              # too late, the attack is active
    w.stagger(target.uid, seconds=1.2, severable=True)
    w.events.emit("SeveranceReady", by=parrier.uid, target=target.uid)
    return True

cpdef void tick_combat(World w, Unit u, double dt):
    u.combat.reclaim_timer -= dt
    if u.combat.reclaim_timer <= 0:
        u.combat.reclaimable = 0                  # orange bar fades away
    u.combat.frenzy = max(0.0, u.combat.frenzy - 6.0 * dt)
    u.combat.stamina = min(u.max_stamina, u.combat.stamina + 45.0 * dt)
```

**First-person render pass with a separate viewmodel and per-creature senses** (`render/renderer.py`, excerpt)
```python
SENSE_SHADERS = {
    "normal": "post_normal", "darkvision": "post_darkvision",
    "scent_trails": "post_scent", "echolocation": "post_echo",
    "vibration": "post_vibration", "reality_warp": "post_warp",
}

def draw_first_person(self, host, world_snapshot, alpha, t):
    body = host["body"]
    eye = glm.vec3(host["x"], body["eye_height"] + self.head_bob(host, t), host["z"])
    view = glm.lookAt(eye, eye + self.look_dir(host["yaw"], host["pitch"]), glm.vec3(0, 1, 0))
    proj = glm.perspective(glm.radians(self.fov_with_punch(body["fov"])),
                           self.aspect, 0.05, 500.0)

    # 1) World pass (the giant tabletop + every other unit)
    self.scene_fbo.use(); self.ctx.clear(0.01, 0.0, 0.02)
    self.draw_world(proj * view, world_snapshot, alpha, t, skip_uid=host["uid"])

    # 2) Viewmodel pass: clear depth only, draw own limbs with own FOV / near plane
    self.scene_fbo.color_mask = (False, False, False, False)   # clear depth only
    self.scene_fbo.clear(depth=1.0)
    self.scene_fbo.color_mask = (True, True, True, True)
    vm_proj = glm.perspective(glm.radians(70.0), self.aspect, 0.01, 10.0)
    self.draw_viewmodel(vm_proj, host, t)          # claws, lantern, held card in off-hand

    # 3) Senses post-process for this creature, then sanity/madness on top
    self.run_post(SENSE_SHADERS[body["senses"]], t, host)
    self.run_post("post_madness", t, world_snapshot["local_player"])
```

**Tests** (`tests/test_combat.py`)
```python
from dreamquest.game.soul_leap import Chorus

def test_chorus_requires_different_hosts():
    c = Chorus()
    assert c.register_hit(0.0, host_uid=1) == 1.0
    assert c.register_hit(0.5, host_uid=1) == 1.0          # same host: no chain
    assert c.register_hit(1.0, host_uid=2) == 1.1          # new host: chain grows
    assert c.register_hit(1.4, host_uid=3) == 1.25

def test_chorus_breaks_after_window():
    c = Chorus()
    c.register_hit(0.0, 1); c.register_hit(1.0, 2)
    assert c.register_hit(5.0, 3) == 1.0

def test_reclaim_restores_health(world, spawn):
    a, b = spawn("core.ghoul", owner=0), spawn("core.ghoul", owner=1)
    world.deal_damage(a.uid, 10, b.uid)
    hp_after_hit = a.hp
    world.resolve_hit(attacker=a, victim=b, move="light")  # hit back within 3 s
    assert a.hp > hp_after_hit

def test_parry_window_is_frame_exact(world, spawn): ...
def test_every_move_has_valid_frame_data(host): ...      # startup/active/recovery > 0, hitbox present
```

---

## Smart Procedural Environments (DREAM-QUEST.md §13)

*Design: [DREAM-QUEST.md §13](DREAM-QUEST.md#13-smart-procedural-environments)*

### 13.4 Code template: procedural environments

**Asset manifest with tags** (`content/models/manifest.json`, excerpt): what the generator and sentence-transformers choose from
```json
[
  { "id": "candle_tall",   "file": "candle_tall.glb",   "tags": "light source, wax, flame, ritual, tall",
    "footprint": [0.3, 0.3], "role": "light",  "license": "CC0", "author": "..." },
  { "id": "book_stack",    "file": "book_stack.glb",    "tags": "ancient tomes, scholarship, cover, cliff",
    "footprint": [2.0, 1.4], "role": "cover",  "license": "CC0", "author": "..." },
  { "id": "onyx_pillar",   "file": "onyx_pillar.glb",   "tags": "black stone, cyclopean, ruin, cold",
    "footprint": [1.0, 1.0], "role": "cover",  "license": "CC0", "author": "..." },
  { "id": "bone_pile",     "file": "bone_pile.glb",     "tags": "ghoul, charnel, underworld, decay",
    "footprint": [1.2, 1.2], "role": "decor",  "license": "CC0", "author": "..." }
]
```

**Stage 1: text to spec** (`tools/worldgen/spec_from_text.py`, offline)
```python
"""
Turn a Lovecraft passage into a validated arena spec.
Use a small *instruct* model for structured output (the Lovecraft-style model from
§7.7 is for prose, not JSON). Generate several specs per passage; invalid JSON is discarded.
"""
import json
from transformers import pipeline

SPEC_SCHEMA_HINT = """Return ONLY JSON with keys:
 name (str), mood (list[str]), palette (list of 3 hex colors), light_level (0-1),
 openness (0-1), verticality (0-1), terrain ("flat"|"hills"|"terraced"|"cavern"),
 landmark (str), prop_themes (list[str]), hazards (list[str]), fog (0-1)"""

ALLOWED_TERRAIN = {"flat", "hills", "terraced", "cavern"}

def validate(spec: dict) -> dict:
    assert isinstance(spec["name"], str) and spec["name"]
    assert spec["terrain"] in ALLOWED_TERRAIN
    for key in ("light_level", "openness", "verticality", "fog"):
        spec[key] = float(min(1.0, max(0.0, spec[key])))          # clamp, don't trust
    assert len(spec["palette"]) == 3
    return spec

def specs_for(passage: str, n: int = 8) -> list[dict]:
    gen = pipeline("text-generation", model="<small-instruct-model>")
    prompt = f"{SPEC_SCHEMA_HINT}\n\nPlace description:\n{passage}\n\nJSON:"
    outs = gen(prompt, num_return_sequences=n, max_new_tokens=300,
               do_sample=True, temperature=0.8, return_full_text=False)
    specs = []
    for o in outs:
        try:
            text = o["generated_text"]
            specs.append(validate(json.loads(text[text.index("{"): text.rindex("}") + 1])))
        except (ValueError, KeyError, AssertionError, TypeError):
            continue                                              # discard malformed output
    return specs

# Example output for the Plateau of Leng:
# {"name": "Plateau of Leng", "mood": ["cold", "desolate", "ancient"],
#  "palette": ["#2b2f3a", "#6d7a8c", "#c9a227"], "light_level": 0.25, "openness": 0.85,
#  "verticality": 0.2, "terrain": "terraced", "landmark": "stone_monastery",
#  "prop_themes": ["black stone", "bones", "bonfires"], "hazards": ["cold_wind"], "fog": 0.6}
```

**Prop selection by meaning** (`tools/worldgen/prop_match.py`, offline; results baked into the spec)
```python
import json
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
assets = json.load(open("content/models/manifest.json"))
asset_emb = model.encode([a["tags"] for a in assets], normalize_embeddings=True)

def choose_props(spec: dict, k_per_role: int = 4) -> dict[str, list[str]]:
    """Rank every asset by similarity to the spec's mood + prop themes, keep top-k per role."""
    query = ", ".join(spec["mood"] + spec["prop_themes"])
    q = model.encode(query, normalize_embeddings=True)
    scores = asset_emb @ q
    by_role: dict[str, list[tuple[float, str]]] = {}
    for a, s in zip(assets, scores):
        by_role.setdefault(a["role"], []).append((float(s), a["id"]))
    return {role: [aid for _, aid in sorted(lst, reverse=True)[:k_per_role]]
            for role, lst in by_role.items()}

# spec["props"] = choose_props(spec)  ->  {"light": [...], "cover": [...], "decor": [...]}
```

**Stage 2: arena recipe in Lua** (`content/arenas/recipes/terraced_ruins.lua`): moddable rules
```lua
-- A recipe receives a spec and a deterministic generator API (`gen`).
-- It returns nothing; it writes into the layout through gen.* calls.
return {
  id = "core.terraced_ruins",
  terrain = { "terraced", "hills" },          -- which spec terrains this recipe handles

  build = function(spec, gen)
    local size = 64                            -- grid cells; 1 cell = 0.5 m at Dream scale
    gen.heightmap{ size = size, octaves = 5, roughness = 0.45 + spec.verticality * 0.3,
                   terrace_steps = 4 }

    -- Rifts: place first so everything else can be validated against them.
    gen.place_rifts{ count = 5, symmetry = spec.boss and "none" or "rotational_2" }

    -- Hand-made landmark goes in the middle, a generated clearing around it.
    gen.place_landmark{ id = spec.landmark, at = "center", clear_radius = 6 }

    -- Modular ruins via Wave Function Collapse in the outer ring.
    gen.wfc{ tileset = "ruins_kit", region = "ring", density = 1.0 - spec.openness }

    -- Scatter: cover, lights, decor. Poisson-disk spacing keeps it natural.
    gen.scatter{ role = "cover", min_dist = 4.0, count = math.floor(30 * (1 - spec.openness)) }
    gen.scatter{ role = "light", min_dist = 7.0, count = math.floor(12 * spec.light_level) + 3 }
    gen.scatter{ role = "decor", min_dist = 1.5, count = 60 }

    -- Lovecraftian twist: occasionally a portal seam that links two far edges.
    if gen.rand() < 0.25 then gen.portal_seam{ from = "west_edge", to = "east_edge" } end

    for _, h in ipairs(spec.hazards) do gen.add_hazard(h) end   -- e.g. "cold_wind"
  end,
}
```

**Stage 2: generators** (`src/dreamquest/worldgen/generators.py`, shipped; Cythonize the hot loops)
```python
"""
Deterministic, ML-free generators exposed to Lua recipes as `gen.*`.
All randomness comes from one seeded numpy Generator -> same seed, same arena.
"""
import numpy as np

class Layout:
    def __init__(self, size: int):
        self.size = size
        self.height = np.zeros((size, size), np.float32)
        self.blocked = np.zeros((size, size), bool)       # walkability grid
        self.light = np.zeros((size, size), np.float32)
        self.instances: list[dict] = []                   # {"asset", "x", "z", "rot", "scale"}
        self.rifts: list[tuple[int, int]] = []
        self.portals: list[tuple[tuple[int, int], tuple[int, int]]] = []

def fbm_heightmap(rng, size, octaves=5, roughness=0.5, terrace_steps=0):
    """Fractal value noise: sum of upsampled random grids at doubling frequencies."""
    h = np.zeros((size, size), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        cells = 2 ** (o + 2)
        grid = rng.random((cells + 1, cells + 1)).astype(np.float32)
        # bilinear upsample grid -> size x size
        xs = np.linspace(0, cells, size)
        x0 = np.floor(xs).astype(int).clip(0, cells - 1); t = xs - x0
        top = grid[x0][:, x0] * (1 - t) + grid[x0][:, x0 + 1] * t
        bot = grid[x0 + 1][:, x0] * (1 - t) + grid[x0 + 1][:, x0 + 1] * t
        h += amp * (top * (1 - t[:, None]) + bot * t[:, None])
        total += amp
        amp *= roughness
    h /= total
    if terrace_steps:
        h = np.round(h * terrace_steps) / terrace_steps   # stepped ruins / plateaus
    return h

def poisson_disk(rng, size, min_dist, count, free_mask, k=30):
    """Bridson's algorithm restricted to free cells; returns up to `count` points."""
    points, active = [], []
    def ok(p):
        x, z = int(p[0]), int(p[1])
        if not (0 <= x < size and 0 <= z < size) or not free_mask[x, z]:
            return False
        return all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 >= min_dist ** 2 for q in points)
    # seed with a random free cell
    free = np.argwhere(free_mask)
    if len(free) == 0:
        return points
    first = free[rng.integers(len(free))].astype(float)
    points.append(tuple(first)); active.append(tuple(first))
    while active and len(points) < count:
        i = rng.integers(len(active)); base = active[i]
        for _ in range(k):
            ang, rad = rng.random() * 2 * np.pi, min_dist * (1 + rng.random())
            cand = (base[0] + np.cos(ang) * rad, base[1] + np.sin(ang) * rad)
            if ok(cand):
                points.append(cand); active.append(cand); break
        else:
            active.pop(i)
    return points

def wave_function_collapse(rng, region_cells, tileset):
    """
    Classic WFC over a grid region:
      1. every cell starts with all tiles possible
      2. collapse the lowest-entropy cell (weighted random tile)
      3. propagate adjacency constraints (tileset["allowed"][tile][direction])
      4. repeat; on contradiction, restart with rng-derived sub-seed (bounded retries)
    Tilesets are defined in Lua/JSON next to the modular kit pieces.
    """
    ...

class GenAPI:
    """The `gen` table handed to Lua recipes. Mirrors the calls used in the recipe above."""
    def __init__(self, seed: int, spec: dict, assets: dict):
        self.rng = np.random.default_rng(seed)
        self.spec, self.assets = spec, assets
        self.layout: Layout | None = None

    def rand(self) -> float:
        return float(self.rng.random())

    def heightmap(self, opts): ...
    def place_rifts(self, opts): ...
    def place_landmark(self, opts): ...
    def wfc(self, opts): ...
    def scatter(self, opts):
        role = opts["role"]
        candidates = self.spec["props"][role]
        pts = poisson_disk(self.rng, self.layout.size, opts["min_dist"], opts["count"],
                           free_mask=~self.layout.blocked)
        for x, z in pts:
            aid = candidates[self.rng.integers(len(candidates))]
            self.layout.instances.append({"asset": aid, "x": x, "z": z,
                                          "rot": float(self.rng.random() * 360),
                                          "scale": float(0.85 + self.rng.random() * 0.3)})
            if role == "cover":
                self.layout.blocked[int(x), int(z)] = True
    def portal_seam(self, opts): ...
    def add_hazard(self, name): ...

def generate(seed: int, spec: dict, recipe, assets) -> Layout:
    gen = GenAPI(seed, spec, assets)
    recipe.build(spec, gen)          # Lua recipe via ScriptHost (sandboxed, §7.3)
    return gen.layout
```

**Stage 4a: hard checks** (`src/dreamquest/worldgen/validate.py`, used by the generator *and* by pytest)
```python
from collections import deque
import numpy as np

def reachable(layout, start) -> np.ndarray:
    """Flood fill over walkable cells (portal seams count as edges)."""
    seen = np.zeros_like(layout.blocked)
    q = deque([start]); seen[start] = True
    portal_map = {a: b for a, b in layout.portals} | {b: a for a, b in layout.portals}
    while q:
        x, z = q.popleft()
        nbrs = [(x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)]
        if (x, z) in portal_map:
            nbrs.append(portal_map[(x, z)])
        for nx, nz in nbrs:
            if 0 <= nx < layout.size and 0 <= nz < layout.size \
               and not layout.blocked[nx, nz] and not seen[nx, nz]:
                seen[nx, nz] = True; q.append((nx, nz))
    return seen

def check(layout) -> list[str]:
    """Return a list of problems; empty list = valid arena."""
    problems = []
    region = reachable(layout, layout.rifts[0])
    if not all(region[r] for r in layout.rifts):
        problems.append("rift_unreachable")
    if layout.blocked.mean() > 0.45:
        problems.append("too_cramped")
    if layout.blocked.mean() < 0.05:
        problems.append("no_cover")
    if any(layout.blocked[r] for r in layout.rifts):
        problems.append("rift_blocked")
    if (layout.light > 0.3).mean() < 0.15:
        problems.append("too_dark_to_play")
    return problems
```

**Stage 4b: AI playtests** (`tools/worldgen/playtest.py`, offline)
```python
def playtest(seed, spec, n_games=200) -> dict:
    """Commander + Duelist bots (§12.6) fight mirrored decks on this arena."""
    results = [run_headless_match(arena=(seed, spec), decks=MIRROR_DECKS, swap_sides=i % 2)
               for i in range(n_games)]
    side_a = sum(r.winner_side == 0 for r in results) / n_games
    return {
        "side_balance": abs(side_a - 0.5),                       # want < 0.05
        "median_length_s": float(np.median([r.duration for r in results])),
        "stall_rate": sum(r.timed_out for r in results) / n_games,
        "leaps_per_min": float(np.mean([r.soul_leaps_per_min for r in results])),  # fun proxy
    }
```

**Stage 4c: CLIP theme score** (`tools/worldgen/clip_score.py`, offline)
```python
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

clip = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").eval()
proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

@torch.no_grad()
def theme_score(thumbnails: list[Image.Image], prompt: str) -> list[float]:
    """Higher = the rendered arena looks more like the prompt."""
    inputs = proc(text=[prompt], images=thumbnails, return_tensors="pt", padding=True)
    return clip(**inputs).logits_per_image[:, 0].tolist()

# Thumbnails come from moderngl.create_standalone_context(): render 3 fixed camera
# angles (Altar view + two first-person spots) per candidate, read the framebuffer to PIL.
```

**Stage 4d: taste model** (`tools/worldgen/taste.py`, offline)
```python
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.cluster import KMeans

def features(layout, playtest_stats, clip_score) -> np.ndarray:
    return np.array([
        layout.blocked.mean(),                      # cover density
        layout.height.std(),                        # verticality
        (layout.light > 0.3).mean(),                # lit fraction
        mean_rift_path_length(layout),
        len(layout.portals),
        playtest_stats["side_balance"],
        playtest_stats["median_length_s"],
        playtest_stats["leaps_per_min"],
        clip_score,
    ], dtype=np.float32)

# 1) You rate ~100 arenas 1–5 in the Curator (below). Train:
taste = GradientBoostingRegressor().fit(X_rated, y_ratings)

# 2) Filter thousands of new candidates, keep the best predicted ones...
keep = candidates[taste.predict(X_new) >= 3.8]

# 3) ...then keep variety: cluster the survivors and take the best few from each cluster.
labels = KMeans(n_clusters=12, n_init="auto", random_state=0).fit_predict(X_new[keep_idx])
```

**Curator** (`tools/worldgen/curator.py`, NiceGUI with `native=True` for PyWebView)
```python
from nicegui import ui

state = {"queue": load_candidates(), "i": 0}

def show():
    c = state["queue"][state["i"]]
    img.set_source(c["thumbnail_path"])
    info.set_text(f'{c["spec"]["name"]} · seed {c["seed"]} · '
                  f'taste {c["pred"]:.2f} · CLIP {c["clip"]:.1f} · balance {c["balance"]:.3f}')

def rate(stars: int):
    save_rating(state["queue"][state["i"]], stars)        # feeds the taste model
    if stars >= 4:
        accept(state["queue"][state["i"]])                # -> content/arenas/<id>.json
    state["i"] += 1; show()

ui.dark_mode().enable()
img = ui.image().classes("w-[900px]")
info = ui.label()
with ui.row():
    for s in range(1, 6):
        ui.button("★" * s, on_click=lambda s=s: rate(s))
    ui.button("Re-roll seed", on_click=lambda: reroll(state)).props("flat")
    ui.button("Play it", on_click=lambda: launch_game_on(state["queue"][state["i"]]))
show()
ui.run(native=True, title="Arena Curator", window_size=(1000, 800))
```

**What ships** (`content/arenas/leng_terraces_0412.json`): a tiny file, rebuilt at load time
```json
{
  "id": "leng_terraces_0412",
  "recipe": "core.terraced_ruins",
  "seed": 918273645,
  "spec": { "name": "Plateau of Leng", "terrain": "terraced", "landmark": "stone_monastery",
            "openness": 0.85, "verticality": 0.2, "light_level": 0.25, "fog": 0.6,
            "palette": ["#2b2f3a", "#6d7a8c", "#c9a227"], "hazards": ["cold_wind"],
            "props": { "light": ["bonfire_small", "candle_tall"],
                       "cover": ["onyx_pillar", "book_stack"],
                       "decor": ["bone_pile", "prayer_flags"] } },
  "generator_version": 3,
  "source_passage": "dream-quest_of_unknown_kadath ¶412"
}
```

**Tests** (`tests/test_worldgen.py`)
```python
import pytest, json
from pathlib import Path
from dreamquest.worldgen import generate, validate

ARENAS = sorted(Path("content/arenas").glob("*.json"))

@pytest.mark.parametrize("path", ARENAS, ids=lambda p: p.stem)
def test_shipped_arenas_are_valid(path, recipes, assets):
    a = json.loads(path.read_text())
    layout = generate(a["seed"], a["spec"], recipes[a["recipe"]], assets)
    assert validate.check(layout) == []

def test_generation_is_deterministic(recipes, assets, sample_spec):
    a = generate(123, sample_spec, recipes["core.terraced_ruins"], assets)
    b = generate(123, sample_spec, recipes["core.terraced_ruins"], assets)
    assert (a.height == b.height).all() and a.instances == b.instances

def test_rotational_symmetry_for_duels(recipes, assets, sample_spec):
    layout = generate(7, sample_spec, recipes["core.terraced_ruins"], assets)
    assert (layout.blocked == layout.blocked[::-1, ::-1]).all()
```

> **Versioning note:** shipped arenas are *seed + spec + recipe*. If you change a generator, every shipped seed produces a different arena. Bump `generator_version`, keep the old generator code path, and have `test_shipped_arenas_are_valid` catch regressions.

---

## Waking-World Horrors (DREAM-QUEST.md §14)

*Design: [DREAM-QUEST.md §14](DREAM-QUEST.md#14-beyond-the-dreamlands-waking-world-horrors)*

### 14.9 Code template: Waking-World horrors

**Shoggoth: mimicry and engulf** (`content/cards/waking/shoggoth.lua`)
```lua
return {
  id = "waking.shoggoth", name = "Shoggoth", type = "entity",
  faction = "elder_things", cost = 7, rarity = "rare",
  source = "At the Mountains of Madness",
  horror = "1d6 / 1d20",                     -- seeing one is a serious shock
  creature_kind = "shoggoth",
  keywords = { "Mimic", "Engulf", "Rebellious" },
  stats = { hp = 70, atk = 6, speed = 3.0, stamina = 140, poise = 80 },

  body = { eye_height = 4.0, fov = 120, senses = "many_eyes",
           dodge = { kind = "reform", iframes = 18, recovery = 14, stamina = 30 } },

  utterance = { name = "Tekeli-li!", cooldown = 20,
                on_use = function(uid) game.fear_cone(uid, 12.0, 120, 2.5) end },

  -- Mimic: whatever move last hit this shoggoth becomes available to it.
  on_damaged = function(uid, source_uid, move_id)
    if move_id then game.grant_move(uid, game.unit(source_uid).card_id, move_id, 15.0) end
  end,

  -- Engulf: absorb a small unit (stats.size < 2) and keep its moveset.
  abilities = {
    { key = "engulf", name = "Engulf", skill = 40, cooldown = 12,
      on_resolve = function(uid, target_uid, res)
        local t = game.unit(target_uid)
        if t.size < 2 and res.tier ~= "fail" and res.tier ~= "fumble" then
          game.absorb(uid, target_uid)        -- target removed, moveset inherited
        end
      end },
  },

  -- Rebellious: if its owner has no Elder Things on the board, it may turn.
  on_tick = function(uid, dt)
    local owner = game.unit(uid).owner
    if not game.has_faction_unit(owner, "elder_things") and game.rand(1, 600) == 1 then
      game.change_owner(uid)
    end
  end,
}
```

**Yithian Mind-Exchange: hooking into Soul Leap** (`content/cards/waking/yithian_archivist.lua`)
```lua
return {
  id = "waking.yithian_archivist", name = "Yithian Archivist", type = "entity",
  faction = "yith", cost = 6, rarity = "rare", source = "The Shadow out of Time",
  horror = "0 / 1d6", creature_kind = "yithian",
  stats = { hp = 40, atk = 3, speed = 1.8, poise = 60 },

  abilities = {
    { key = "mind_exchange", name = "Mind-Exchange", skill = 55, cooldown = 30,
      on_resolve = function(uid, target_uid, res)
        local victim_owner = game.unit(target_uid).owner
        if not game.is_possessed(target_uid) or res.tier == "fail" then return end
        local secs = (res.tier == "sublime") and 12 or 8
        -- The enemy pilots your unit; you're forced into this slow cone body.
        game.swap_minds(uid, target_uid, secs)
        game.sanity(victim_owner, -3)
      end },
  },

  -- Time-skip dodge: rewind this unit's own position/HP by 1.5 s (uses snapshot ring buffer).
  on_dodge = function(uid) game.rewind_unit(uid, 1.5) end,
}
```

**The Colour Out of Space as a Locale** (`content/cards/waking/the_colour.lua`)
```lua
return {
  id = "waking.the_colour", name = "The Colour Out of Space", type = "locale",
  faction = "colour", cost = 0, rarity = "mythic", source = "The Colour Out of Space",
  boss_only = true,

  on_play = function(pid)
    game.set_shader_param("desaturate", 0.0)
    game.blight_seed(game.arena_center(), 3)      -- radius-3 tile blight at the Well
  end,

  -- Every second: spread to neighbouring tiles, drain whatever stands in it.
  on_locale_tick = function(dt)
    game.blight_spread{ chance = 0.08, blocked_by = "cover" }   -- cover contains it
    for _, uid in ipairs(game.units_on_blight()) do
      game.damage(uid, 1, -1)
      game.add_insight(game.unit(uid).owner, 0.02)   -- it is fascinating, too
    end
    game.set_shader_param("desaturate", game.blight_fraction())
  end,
}
```

**Innsmouth "Change" stacks** (`src/dreamquest/engine/statuses.py`)
```python
CHANGE_TURN_THRESHOLD = 3

def apply_change(world, uid: int, stacks: int = 1):
    """Deep One hits add Change. At the threshold the unit (or Dreamer) turns."""
    u = world.units[uid]
    u.tags["change"] = u.tags.get("change", 0) + stacks
    world.events.emit("ChangeStack", uid=uid, total=u.tags["change"])
    if u.tags["change"] >= CHANGE_TURN_THRESHOLD and not u.tags.get("turned"):
        u.tags["turned"] = True
        world.script.call_global("on_unit_turned", uid)   # Lua grants swim moves, gills, etc.
        if u.tags.get("dreamer"):
            # The story's ending as a mechanic: you gain the sea's gifts
            # and permanently lose a slice of your Sanity cap for the run.
            p = world.players[u.owner]
            p.max_sanity_penalty += 15
```

**Run structure with Waking-World alternate layers** (`content/runs/layers.lua`)
```lua
return {
  { layer = 2, routes = {
      { id = "enchanted_wood", weight = 2 },
      { id = "dunwich_hills",  weight = 1, recipe = "core.dunwich_hills",  faction = "whateley" },
      { id = "arkham_campus",  weight = 1, recipe = "core.arkham_campus",  faction = "reanimators" } } },
  { layer = 3, routes = {
      { id = "the_moon",       weight = 2 },
      { id = "innsmouth",      weight = 1, recipe = "core.innsmouth_harbor", faction = "deep_ones" } } },
  { layer = 4, routes = {
      { id = "underworld",     weight = 2 },
      { id = "antarctica",     weight = 1, recipe = "core.antarctic_city", faction = "elder_things" },
      { id = "exham_depths",   weight = 1, recipe = "core.exham_depths",   faction = "rats" } } },
  { layer = 5, routes = {
      { id = "leng",           weight = 2 },
      { id = "yuggoth",        weight = 1, recipe = "core.yuggoth_mines",  faction = "mi_go" },
      { id = "pnakotus",       weight = 1, recipe = "core.pnakotus",       faction = "yith" } } },
  { layer = 6, routes = {
      { id = "kadath",         weight = 1, boss = "core.nyarlathotep" },
      { id = "rlyeh",          weight = 1, boss = "waking.cthulhu",  unlock = "first_win" },
      { id = "sentinel_hill",  weight = 1, boss = "waking.yog_spawn", unlock = "first_win" } } },
  thin_place_chance = 0.15,     -- per map node, any layer
}
```

**Tests** (`tests/test_waking_world.py`)
```python
def test_change_stacks_turn_unit(world, spawn):
    u = spawn("core.cat_of_ulthar", owner=0)
    for _ in range(3):
        apply_change(world, u.uid)
    assert u.tags["turned"] is True

def test_unseen_brother_hidden_until_powder(world, spawn, cast):
    b = spawn("waking.unseen_brother", owner=1)
    assert not world.is_visible_to(0, b.uid)
    cast("waking.powder_of_ibn_ghazi", pid=0)
    assert world.is_visible_to(0, b.uid)

def test_mind_exchange_returns_control(world, spawn, leap, advance):
    mine = spawn("core.ghoul", owner=0); leap(0, mine.uid)
    yith = spawn("waking.yithian_archivist", owner=1)
    world.force_resolve(yith.uid, "mind_exchange", target=mine.uid, tier="success")
    assert world.controller_of(mine.uid) == 1
    advance(seconds=8.1)
    assert world.controller_of(mine.uid) == 0

def test_cover_contains_the_colour(world, arena_with_wall_ring, advance):
    world.play_locale("waking.the_colour")
    advance(seconds=120)
    assert world.blight_fraction() < 0.25            # the wall ring holds it

def test_every_waking_card_cites_a_lovecraft_source(host):
    for cid, card in host.cards.items():
        if cid.startswith("waking."):
            assert card["source"], f"{cid} must cite its Lovecraft story"
```

> The last test enforces the copyright rule: every Waking-World card must cite the Lovecraft story it comes from. Keep a list of allowed source titles in `content/sources.json` so revisions and other authors' material can't slip in.
