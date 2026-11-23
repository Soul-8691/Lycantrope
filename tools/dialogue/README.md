# Dialogue tools

Write Morrowind dialogue as readable YAML in [`dialogue/`](../../dialogue), check it, and compile it into a plugin. Nobody has to edit dialogue by hand in the Construction Set, where response order and links are easy to break.

```
dialogue/*.yaml ──validate.py──> compile.py ──> out/tdl_dialogue.json ──tes3conv──> out/tdl_dialogue.esp
        ▲                                   └──> out/voice_lines.csv (for ElevenLabs)
   brief.py → Claude drafts lines → a person edits, marks `reviewed`, locks hand-edited lines
```

## Setup

```bash
pip install -r tools/dialogue/requirements.txt
```

- **tes3conv** (for the `.esp`): download it from [github.com/Greatness7/tes3conv/releases](https://github.com/Greatness7/tes3conv/releases), then set `tes3conv:` in [config.yaml](config.yaml) or the `TES3CONV` environment variable. Without it you still get the JSON.
- **`plugin.data_files`** in config.yaml: your Morrowind `Data Files` folder. Used for the master's file size and the vanilla-topic check.

## Files

| Path | What |
|---|---|
| `dialogue/conventions.md` | The style guide and YAML format. Read this first. |
| `dialogue/bible.md` | What townsfolk know, by place and story state |
| `dialogue/states.yaml` | Globals (e.g. `tdl_ws_arkham`, `tdl_roll`), factions, topics known at the start |
| `dialogue/characters/*.yaml` | One sheet per named NPC (`_TEMPLATE.yaml` to copy) |
| `dialogue/topics/**/*.yaml` | Topics, greetings, voice lines |
| `dialogue/journals/**/*.yaml` | Quest journals |
| `Data Files/MWSE/mods/TheDreamlands/dialogue.lua` | Re-rolls `tdl_roll` (0–3) on every conversation and response |

## Commands

```bash
python tools/dialogue/validate.py                 # check both stories (v1, v2)
python tools/dialogue/validate.py --vanilla       # also flag words that would link to vanilla topics
python tools/dialogue/validate.py --check-locked  # locked lines must match the last commit
python tools/dialogue/compile.py                  # validate, then build (story from config.yaml)
python tools/dialogue/compile.py --story v1
python tools/dialogue/brief.py --topic "Greeting 5" --characters tdl_pell --task "Pell's greetings for each Arkham state"
```

## Writing with Claude

1. **Make a brief:** `brief.py --topic ... --task "..."` writes `out/briefs/<topic>.md`. It contains the conventions, the bible, the states, the character sheets, the existing lines (locked ones marked) and the answer format.
2. **Generate:** in Claude Code, ask: *"Write the lines described in tools/dialogue/out/briefs/greeting_5.md into dialogue/topics/arkham/greetings.yaml."* Or paste the brief into any chat.
3. **Validate** (with `--vanilla`), fix what it flags, and read every line yourself.
4. **Mark lines** `status: reviewed` when they're approved, and `locked: true` when you've hand-edited them. Later generation passes must leave locked lines alone. Run `validate.py --check-locked` before committing to catch accidents.
5. **Compile** and test in game.

Generic dialogue (rumours, greetings, directions, faction routines) can be mostly generated. **Main-quest scenes should be co-written**, one scene at a time.

## How the compiler maps YAML to Morrowind

- **Order:** a topic's responses are written in file order. Several files for one topic merge by their `order:` value, then file name. Morrowind says the **first** response whose conditions match, so specific lines go above general ones. The validator warns when a later line can never be reached.
- **IDs:** each response's ID is a hash of its topic and `key`. Rebuilding never reshuffles IDs, and renaming a key gives a new ID.
- **Linking:** responses are chained with Morrowind's prev/next IDs. The first one has no `prev`, so on a vanilla topic (`latest rumors`, greetings) **our responses sit above all vanilla ones**. End each topic with a fallback filtered to our cells, so vanilla lines never show for our NPCs.
- **Stories:** lines tagged `v1` or `v2` are only compiled for that story; `both` always.
- **Round-trip check:** after building the `.esp`, the compiler converts it back with tes3conv and checks that the records and the response order are identical.

## Why `--vanilla` matters

The mod still loads `Morrowind.esm`, which defines about 1,700 topics, many of them ordinary words: *work*, *wolves*, *ring*, *blades*, *magister*, *bad dreams*. If one of those appears in our text, it may become a clickable link to Morrowind's own dialogue. The check found 8 in the first rumour batch, including **"Magister"**, Armitage's title, which now reads "Master Armitage" in dialogue. Run it on every batch.

## Not done yet

- **Getting the generated dialogue into the main plugin:** for now `tdl_dialogue.esp` is a separate plugin. Later, `tools/build.py` should merge it into `TheDreamlands.esm`.
- **NPC records:** they don't exist yet, so `speaker`, `faction` and `class` filters only take effect once the NPCs are made.
- **OpenMW:** `tdl_roll` needs an OpenMW Lua equivalent of `dialogue.lua` for the port.
