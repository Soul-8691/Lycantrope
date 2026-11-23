# THE DREAMLANDS

> *"Three times Randolph Carter dreamed of the marvellous city, and three times was he snatched away while still he paused on the high terrace above it."*
> — H.P. Lovecraft, *The Dream-Quest of Unknown Kadath* (1927)

**The Dreamlands** is a free, non-commercial total-conversion mod for **The Elder Scrolls III: Morrowind**. It is a first-person action adventure set in a **dark-ages version of Lovecraft's world**: a medieval Miskatonic Valley (Arkham, Kingsport, Dunwich) invaded by horrors that pour out of the Dreamlands' cities in the sky. You start as an ordinary shop helper and end as the one who seals the portals. It is built from Morrowind's own assets (re-textured, re-meshed and re-dressed), adds new mechanics through Lua scripting, and uses ElevenLabs voice acting for key characters.

| | |
|---|---|
| **Genre** | First-person action adventure / RPG (total conversion) |
| **Requires** | Morrowind + Tribunal + Bloodmoon (GOTY or any complete edition) |
| **Engine** | Original engine + **MWSE** (Windows), with **OpenMW** support as a goal |
| **Price** | Free. No donations, no paid early access, no Nexus Donation Points |
| **Editors** | Construction Set / OpenMW-CS; `tes3conv` (ESP ⇄ JSON for git); `tes3cmd` (cleaning) |
| **Scripting** | MWSE-Lua (OpenMW Lua for the OpenMW port); vanilla MWScript only where unavoidable |
| **Art** | Blender + the Morrowind NIF plugin (`io_scene_mw`), NifSkope, DDS textures |
| **Voice** | ElevenLabs (designed voices, not clones of real people) → MP3 in `Sound/Vo/` |
| **Writing aid** | Optional offline language model trained on Lovecraft's public-domain fiction |

---

## Table of Contents

1. [Things to Settle First](#1-things-to-settle-first)
2. [Plan by Phase](#2-plan-by-phase)
3. [Game Design](#3-game-design)
4. [Creative Ideas](#4-creative-ideas)
5. [Mod Architecture](#5-mod-architecture)
6. [Project Layout](#6-project-layout)
7. [Voiceover Ideas (ElevenLabs)](#7-voiceover-ideas-elevenlabs)
8. [Assets and Licensing](#8-assets-and-licensing)
9. [Releasing](#9-releasing)
10. [Risks and How to Handle Them](#10-risks-and-how-to-handle-them)
11. [Ideas from the Call of Cthulhu RPG](#11-ideas-from-the-call-of-cthulhu-rpg)
12. [Combat: Morrowind × Bloodborne](#12-combat-morrowind--bloodborne)
13. [Procedural Help for Dungeons](#13-procedural-help-for-dungeons)
14. [Beyond the Dreamlands: Waking-World Horrors](#14-beyond-the-dreamlands-waking-world-horrors)
15. [Storyline, Part I: The Demo](#15-storyline-part-i-the-demo)
16. [Making 3D Models (Claude and Meshy)](#16-making-3d-models-claude-and-meshy)

> **Note:** [CODE_TEMPLATES.md](CODE_TEMPLATES.md) was written for the old Python card game and no longer applies. It can be deleted or replaced with MWSE-Lua templates.

---

## 1. Things to Settle First

### 1.1 Bethesda's mod rules
- Bethesda allows mods that **use Morrowind's assets** as long as they are **free** and **require the player to own Morrowind**. The mod ships only *your* files (ESM/ESP, new meshes, textures, sounds, scripts). It never ships Bethesda's BSAs, ESMs or original assets.
- **Not allowed:** a standalone game built from Morrowind assets, even a free one; porting Morrowind assets into another game or engine release that doesn't need Morrowind; and taking money for it in any form (sales, paywalled early access, donation-gated content).
- OpenMW is fine. It's a reimplementation of the engine that still loads the player's own Morrowind data files.

### 1.2 Public-domain scope
- Lovecraft's own fiction is generally treated as public domain in the US. His characters and creatures are safe to use: Randolph Carter, Nyarlathotep, the Cats of Ulthar, Pickman, night-gaunts, Deep Ones and others. See §14.2 for the details per story.
- **Not automatically safe:** material added by later authors (August Derleth's "Elder Gods vs. Great Old Ones," creatures invented by other writers, see §14.2) and anything specific to Chaosium's *Call of Cthulhu* RPG (rules text, stat blocks, scenarios, art). See §11.1.
- **Bending the lore is fine.** Public-domain material can be changed freely: a medieval Arkham, horrors from sky cities instead of outer space, and so on. The changes this mod makes are listed in §15.1.

### 1.3 Engine target
- **Recommendation:** build for the **original engine + MWSE** first. MWSE's Lua API is the most complete for what this mod needs (custom UI bars, dialogue hooks, combat events, timed voice playback). Keep scripts modular so an **OpenMW Lua** port is possible later.
- Write down which engine features each system needs, so the port has a checklist.

### 1.4 World placement
Morrowind has one exterior worldspace. The options:
- **A new landmass** far out in the exterior cell grid for the Dreamlands (the approach big landmass mods use). It gets real weather, day/night and travel.
- **Interior cells flagged "behave like exterior"** for smaller places: Ulthar, Innsmouth, the Underworld, R'lyeh.
- **Recommendation:** the **Miskatonic Valley** (the waking world, where the demo takes place) as the main exterior landmass. The **Dreamlands** become a second landmass far out in the cell grid, reachable only by portal and, later, the sky-city spell. Small or strange places (Innsmouth, R'lyeh, the Underworld, the sky cities' interiors) are "exterior-like" interiors.

### 1.5 Scope
A total conversion is a huge project. **Build a vertical slice first:**
> The Arkham shop prologue → the Archsage's visit → the first lessons → the first incursion (§15.3). One town, the Sanity system, the sealing mechanic, three enemy types, about 30 voiced lines.

Add regions only once the slice is fun to play.

---

## 2. Plan by Phase

| Phase | Goal | Deliverable | Key tools |
|---|---|---|---|
| **0. Foundations** | Repo, tooling | `tes3conv` JSON in git, a build script that turns JSON back into an ESP, MWSE installed | tes3conv, git |
| **1. Corpus** | Clean Lovecraft text | Stories split into files with metadata, for reference and the optional writing aid | PyMuPDF |
| **2. Core systems** | Sanity, Insight, Composure checks, Fractures | MWSE-Lua modules with a HUD bar and a debug console | MWSE-Lua |
| **3. Vertical slice** | Playable opening | Arkham shop prologue, the Archsage, first lessons, first incursion (§15.3); first voiced lines | CS, Blender, Meshy, ElevenLabs |
| **4. Combat feel** | Bloodborne-style fights | Dodge, Reclaim, Severance (§12), portal sealing (§15.4) | MWSE-Lua |
| **5. The demo (Part I)** | The Miskatonic Valley | Arkham, Kingsport, Dunwich, Aylesbury; three incursions; sidequests; the demo boss (§15) | CS, Blender, Meshy |
| **6. Part II** | After the demo | The portal into the Dreamlands, the sky cities, Carter's Dreamlands (§3.5), more waking-world regions (§14); new creatures Morrowind lacks ([CREATURES.md](CREATURES.md)) | CS, Blender, Meshy |
| **7. Voice pass** | Full VO | All planned lines generated, mastered and hooked in (§7) | ElevenLabs, ffmpeg |
| **8. Polish** | Feel | Shaders (MGE XE / OpenMW post-processing), music, ambient sound, MCM settings menu | MGE XE, MWSE MCM |
| **9. Release** | Ship it | Nexus Mods + ModDB pages, installation guide, OpenMW notes | — |

**Rules that apply throughout:**
- **The plugin is source code.** Commit it as `tes3conv` JSON so diffs and merges work. Build the ESP from the JSON.
- **Clean every plugin** with `tes3cmd clean` before release (no accidental edits to vanilla records).
- **Lua over MWScript** for anything new. MWScript is only for small object scripts the Lua code can't replace.

---

## 3. Game Design

### 3.1 The core idea
You are an ordinary **shop helper** in a dark-ages Arkham, a walled town on the Miskatonic river. Since childhood you have dreamed of a city in the clouds. That dreaming is why the valley's greatest wizard, the **Archsage**, comes looking for you: a mind that already wanders the Dreamlands can withstand what is coming. Horrors from the Dreamlands' **sky cities** are about to pour into the waking world through portals, and only someone who can **seal** them has a chance. Your mind is your most important resource: what you see, read and do changes you. The full opening is in §15.

### 3.2 Custom stats (on top of Morrowind's attributes and skills)

| Stat | Inspiration | Rules |
|---|---|---|
| **Sanity** | CoC, Darkest Dungeon | 0–99. Lost by witnessing horrors, reading forbidden tomes and casting Mythos spells. Recovered slowly by resting in safe places. At 0 you are **Lost** (see §3.5). Thresholds at 75/50/25 give **Afflictions** or **Revelations**. |
| **Insight** | Bloodborne | Gained by witnessing Great Old Ones and reading tomes. High Insight **reveals hidden things** (invisible creatures, secret doors, true forms) but makes enemies stronger and lowers maximum Sanity (§11.2). |
| **Doom** | Arkham Horror | A world-state clock. Certain main-quest failures and choices raise it. Higher Doom changes weather, spawns and NPC dialogue, and unlocks harder endings. |
| **Luck** | Morrowind's own attribute | Doubles as CoC-style luck: spend Luck "points" (a temporary drain) to turn a failed check into a pass. |

### 3.3 Character creation
Replace Morrowind's prison-ship opening with **the general goods shop in Arkham** (§15.3). Character creation happens during the shop work, as Morrowind's census office does: the shopkeeper's ledger asks your name, the town clerk records where you were born (race), and the Archsage reads your sign.
- **Races** are re-skinned humans of the valley and the lands around it (Bretons, Imperials and Nords as valley folk, hill folk and northern sailors). Dreamlands peoples (zoog-kin, cat-favoured, ghoul-blooded) are NPC-only or unlocked in Part II.
- **Classes = Callings** (§11.2): you start as an untrained shop helper. At the end of your first lessons, the teachers' reports pick a class from how you trained (as Morrowind's class quiz does), or you choose one: Sellsword, Hedge-Witch, Scribe, Sailor, Poacher, Friar, Alchemist, Watchman.
- **Birthsigns = Dream-Signs:** *The Silver Key*, *The Cat*, *The Lamp*, *The Onyx Gate*, *The Pallid Moon*, and so on, each with a small bonus and drawback.

### 3.4 Factions (joinable)

| Faction | Source | What joining gives |
|---|---|---|
| **The Cats of Ulthar** | *The Cats of Ulthar*, *Dream-Quest* | Cat allies on call, night vision, help against Moon-beasts |
| **The Ghouls of the Vaults** | *Pickman's Model*, *Dream-Quest* | Pickman as patron, safe passage in the Underworld, ghoul companions |
| **The Court of Kuranes** | *Celephaïs*, *Dream-Quest* | Dream-noble rank, galley travel, Celephaïs housing |
| **The Miskatonic Collegium** | Miskatonic University, re-imagined as a monastery-college | Library access, spell training, Tome translation |
| **The Arkham Watch** | Original | Weapon training, bounties, the first allies in incursions |
| **Esoteric Order of Dagon** *(evil path)* | *The Shadow over Innsmouth* | Deep One powers at the cost of your humanity (*The Change*, §14.3) |
| **The Cult of the Crawling Chaos** *(evil path)* | *Nyarlathotep*, *Dream-Quest* | Forbidden spells; leads to a dark ending |

Enemy-only factions: **Zoogs** (tricksters; can become allies), **Moon-beasts & Men of Leng**, **Gugs**, **Ghasts**.

### 3.5 Main quest outline

**Part I: the Waking World (the demo).** The shop, the Archsage, training, and three incursions across the Miskatonic Valley, ending with a boss. See §15.

**Part II: the Dreamlands (after the demo).** You cross through a portal that can't be sealed and follow the invasion back to its source. Time runs differently in dreams, so **Randolph Carter**, **Kuranes** and other dreamers from far-future ages can appear as allies. The route loosely follows Carter's journey and ends in the sky:

```
 Act 1  The Seventy Steps → Cavern of Flame (the priests Nasht and Kaman-Thah)
 Act 2  The Enchanted Wood → Ulthar → Dylath-Leen
 Act 3  Celephaïs → Mount Ngranek (learn the sky-city spell)
 Act 4  The Underworld (Vaults of Zin, the Gugs, the Ghouls)
 Act 5  The Plateau of Leng → Inganok
 Act 6  The sky cities: the Moon-beasts' towers and fallen Serannian (§15.1)
 Act 7  Unknown Kadath: Nyarlathotep
```

- **When Sanity hits 0** you are not killed. Your mind slips toward the Dreamlands, and the Archsage drags it back over the telepathic link (§15.2). You wake at the last shrine or inn you rested at. Something stays behind (an item, some Luck), and Doom rises. Truly dying (HP 0) is a normal Morrowind death.

---

## 4. Creative Ideas

1. **Sanity distorts the world, not just a number.** At low Sanity, NPC greetings swap to sinister alternate versions (§7.4), Morrowind's journal entries get scribbled over, shadows move at the edge of the screen, and fake enemies appear and vanish when you swing at them. Include an MCM toggle to turn these off.
2. **Insight reveals true forms.** At high Insight, creatures swap to "true-form" meshes (extra eyes, tentacles). Under the hood this is a second creature record swapped in by Lua.
3. **The Necronomicon as a lore journal.** A custom journal tab that fills with notes from the real story passage each place or creature comes from (*"Source: The Cats of Ulthar"*).
4. **Nyarlathotep learns.** Across the game, Lua records which spells, weapons and tactics you use most. The final fight's form (the Black Pharaoh, the Haunter of the Dark, the Bloated Woman) is chosen to counter them, and he comments on it in his voice lines.
5. **The Silver Key.** A unique item that **rewinds the last few seconds** once per day: Lua keeps a short buffer of your position, health and Sanity.
6. **Dream-Shapes (the werewolf system, reused).** Bloodmoon's werewolf transformation becomes **dream-shifting**: drink the right draught and become a **cat**, **ghoul** or **night-gaunt** for a while, each with its own movement, senses and attacks (§12.5).
7. **Reading takes time.** Tomes must be read over several in-game days (Morrowind's rest/wait system). You lose Sanity at each stage and gain Insight and a spell when you finish.
8. **Found Documents.** Letters, sealed writs, diary pages and broadsheets as readable books on an aged-paper style. Many are voiced by their writer (§7.3) and hold **Clues** for quests.
9. **The Dreamwarden.** A hidden "director" in Lua watches your Sanity, Doom and recent fights, and decides when to stage an ambush, when to allow quiet, and which whispers to play.
10. **Cats vs. Moon-beasts.** As in the book. Join the Cats and Moon-beasts become your sworn enemies; cats come to help when you fight them.
11. **Your journal in Lovecraft's voice.** Quest journal entries are written in first person by your Dreamer, in Lovecraft's style (drafted with the optional writing aid and then edited by hand).
12. **Audio.** Droning ambient music that gains dissonant layers as Doom rises. "The piping of Azathoth" is a flute line detuned in real time near Kadath.

### 4.1 Morrowind assets that fit Lovecraft

| Lovecraft place or creature | Morrowind / Tribunal / Bloodmoon starting point |
|---|---|
| Elder Thing cities (*Mountains of Madness*) | **Dwemer ruins** under Bloodmoon's snow and ice |
| Kadath's onyx castle, Inganok | **Daedric ruins** and **Mournhold** architecture, re-textured in black onyx |
| Celephaïs, Ulthar, Dylath-Leen | **Mournhold** and **Imperial** towns, re-textured |
| Arkham, Innsmouth, Dunwich | **Imperial** and **Bloodmoon (Raven Rock / Skaal)** buildings with new New England textures (gambrel roofs) |
| The Plateau of Leng | **Ash wastes** and **ash storms**, with colder fog |
| Yuggoth's fungal towers | **Telvanni** mushroom architecture |
| The Colour, the Innsmouth taint | The **Sixth House / corprus** visual language |
| Ghouls, ghasts | **Ash ghouls** and **corprus stalkers**, re-meshed |
| Night-gaunts | **Winged twilights**, with faces removed and new wings |
| Gugs | **Ogrims**, scaled up, with a vertical mouth |
| Deep Ones | **Dreugh** and **Argonian** bodies |
| Zoogs | **Scamps**, scaled down, with fur |

The full creature-by-creature mapping, with match ratings, 4thUnknown's remodels and effort estimates, is in [CREATURES.md](CREATURES.md).

---

## 5. Mod Architecture

```
  Morrowind.esm, Tribunal.esm, Bloodmoon.esm   (player's own files, never shipped)
               │
               ▼
  TheDreamlands.esm  ← world, NPCs, creatures, items, dialogue, quests
               │
               ├── TheDreamlands_Voice.esp   (optional: voiced-line hooks)
               └── TheDreamlands_OpenMW.omwscripts (later: OpenMW Lua port)

  MWSE/mods/TheDreamlands/  (Lua)
     main.lua        → event registration
     sanity.lua      → Sanity/Insight/Doom state, saved in tes3.player.data
     checks.lua      → Composure checks, Fractures (§11)
     combat.lua      → dodge, Reclaim, Severance (§12)
     voice.lua       → plays voiced lines, picks Sanity variants (§7)
     director.lua    → the Dreamwarden (§4 idea 9)
     ui.lua / mcm.lua→ HUD bars, settings menu
```

**Main rules:**
- **The ESM holds data; Lua holds behaviour.** Creatures, NPCs, cells and dialogue live in the ESM. Anything with logic lives in Lua.
- **Save data lives in `tes3.player.data`** (MWSE) so it travels with the save game.
- **Events, not polling:** hook `damaged`, `attack`, `spellCast`, `activate`, `infoGetText`, `cellChanged` and similar events instead of running per-frame scripts on every object.

---

## 6. Project Layout

```
The Dreamlands/
├── THE_DREAMLANDS.md                ← this file
├── src/
│   └── TheDreamlands.esm.json       ← tes3conv source of the plugin
├── Data Files/                      ← exactly what gets packaged
│   ├── TheDreamlands.esm            ← built from src/
│   ├── Meshes/tdl/                  ← .nif
│   ├── Textures/tdl/                ← .dds
│   ├── Icons/tdl/
│   ├── Sound/tdl/                   ← ambient, creature sounds
│   ├── Sound/Vo/tdl/                ← voiced lines (§7)
│   ├── Music/tdl/
│   └── MWSE/mods/TheDreamlands/     ← Lua (§5)
├── dialogue/                        ← dialogue as YAML, bible, character sheets (tools/dialogue)
├── tools/
│   ├── build.py                     ← JSON → ESM, clean, package
│   ├── dialogue/                    ← validate + compile dialogue YAML → plugin, generation briefs
│   ├── voice/                       ← script CSV, ElevenLabs batch script, mastering
│   └── corpus/                      ← Lovecraft text extraction (public domain only)
├── art_src/                         ← .blend files, texture sources
└── CREDITS.md                       ← every asset, voice, tool + license
```

Prefix every record ID and asset path with **`tdl_`** / **`tdl/`** so nothing collides with other mods.

---

## 7. Voiceover Ideas (ElevenLabs)

Morrowind voices only greetings, combat barks and a few key lines; everything else is text. Follow that tradition. **Voice what gives the world a mood, and leave the long quest dialogue as text.** It keeps the budget sane and lets you change writing without regenerating audio.

### 7.1 What to voice

| Tier | What | Rough line count |
|---|---|---|
| **1. Signature characters** | Nyarlathotep, Randolph Carter, Kuranes, Pickman, Zadok Allen, Wilbur Whateley, the Mi-Go voice | 20–60 lines each |
| **2. Narrator** | Journal updates, act openings, the Seventy Steps descent | 100–200 |
| **3. Generic NPC greetings** | Per region and type (Ulthar villager, Innsmouth fisherman, Miskatonic scholar) | 10–20 per type |
| **4. Barks** | Combat, pain, death, "I see you," Sanity-break screams | 10–15 per voice |
| **5. Whispers** | Sanity-driven ambient voices (§7.4) | 100+ short clips |

### 7.2 Character voice ideas

| Character | Source | Voice direction |
|---|---|---|
| **The Archsage** | Original (§15.2) | Your most-heard voice, almost always **inside your head**. Old, warm, patient, a little tired, with the accent of the Drowned Coast he grew up on. Close-mic'd and dry, as if spoken an inch from your ear. When he talks about the cult he once led, a **second, deeper, wet voice** bleeds in under his own. He is always fighting it. |
| **The Shopkeeper** | Original | Gruff, practical, secretly fond of you. The first voice you hear. |
| **Nyarlathotep** | *Nyarlathotep*, *Dream-Quest*, *Witch House* | One "actor," several forms. **The Black Pharaoh:** warm, courteous, amused, never raises his voice. **The Haunter of the Dark:** the same lines, pitched down with a slow echo and played only in darkness. **The Black Man of the witch-cult:** dry and formal. He speaks to the player as an old acquaintance, with lines changed by your class and faction (§4 idea 4). |
| **Randolph Carter** | *Dream-Quest*, *The Silver Key* | A tired, gentle Boston gentleman in his fifties. Polite and old-fashioned, with flashes of wonder. |
| **King Kuranes** | *Celephaïs* | A wistful English gentleman who longs for Cornwall. Regal in court; soft and homesick in his cottage. |
| **Richard Upton Pickman** | *Pickman's Model*, *Dream-Quest* | Two layers: a Boston artist's drawl, and the ghoul he has become underneath (wet, clicking consonants). |
| **Zadok Allen** | *The Shadow over Innsmouth* | A 96-year-old drunk New England fisherman. The long monologue about Obed Marsh is a **showpiece**: one long take, with fear rising as he notices the sea. Use v3 audio tags for slurring, coughing and terror. |
| **Wilbur Whateley** | *The Dunwich Horror* | Too-deep, oddly resonant, careful speech, as if the mouth isn't quite human. |
| **The Unseen Brother** | *The Dunwich Horror* | Only one scene: Sentinel Hill. The crying out to its father, from the story's public-domain text (*"HELP! HELP! … ff—ff—ff—FATHER! FATHER! YOG-SOTHOTH!"*), split into a huge low voice layered with a human one. |
| **Henry Armitage** | *The Dunwich Horror* | An elderly librarian: precise and dry, but brave. Your Miskatonic quest-giver. |
| **Herbert West** | *Herbert West: Reanimator* | Small, cold and clinical; talks about corpses like lab equipment. |
| **Joseph Curwen** | *Charles Dexter Ward* | Archaic 1700s diction in a hoarse whisper. |
| **Keziah Mason & Brown Jenkin** | *The Dreams in the Witch House* | Keziah cackles and bargains. Brown Jenkin "titters" in a tiny human voice with a rat's squeak underneath. |

### 7.3 Creature and people sounds (Lovecraft gives you the clues)

- **Ghouls meep and glibber.** Write a short "ghoulish" vocabulary of sounds and let ElevenLabs perform them, layered with wet clicks. Subtitles show the translation once you join the Ghouls.
- **Zoogs speak in a fluttering language.** Fast, whispered syllables mixed with wing-flutter sound effects (generated with ElevenLabs Sound Effects).
- **Cats.** Carter speaks the language of cats, and so can you. Real cat sounds with subtitled meaning.
- **Night-gaunts are silent.** Make the silence the effect: when one is near, ambient sound and music duck out. The only thing you hear is wings.
- **Gugs:** no words. Breath, footfalls and sub-bass grunts you feel more than hear.
- **Mi-Go buzzing voices.** *The Whisperer in Darkness* describes a buzzing voice imitating human speech. Generate the line, then run it through a ring modulator / vocoder with an insect drone.
- **Brain-cylinder voices.** Captive minds speaking through the Mi-Go machine: thin, mechanical, desperate.
- **Shoggoths:** the piping *"Tekeli-li! Tekeli-li!"* from *At the Mountains of Madness*, layered through a wet, resonant filter.
- **Deep Ones:** croaking, bubbling chant. The R'lyeh phrase from *The Call of Cthulhu* (*"Ph'nglui mglw'nafh Cthulhu R'lyeh wgah'nagl fhtagn"*) as the core of their ritual chant.
- **Erich Zann** never speaks (he is mute in the story). His viol music is his voice.

### 7.4 Voice-driven systems

1. **Sanity whispers.** A pool of short whispered lines (public-domain Lovecraft phrases plus your own writing) played positionally around the player. How often, how loud and how clear they are depends on Sanity. At low Sanity some whispers use **NPCs' own voices**, so you can't tell what's real.
2. **Unreliable greetings.** Every voiced greeting has a **"wrong" variant**: the same voice saying something quietly sinister. At low Sanity, Lua sometimes plays the wrong one, and the subtitle shows the *normal* text.
3. **The narrator reads your journal.** Each journal update plays a short narrated line in your Dreamer's voice. Offer two narrator voices (male and female) chosen at character creation.
4. **Found Documents read aloud.** Akeley's letters, Thurston's notes and clippings are read by their writer when opened. *Henry Akeley's* later letters are read by a slightly wrong voice, because they aren't really from him.
5. **The singing stone.** A medieval stand-in for the phonograph record in *The Whisperer in Darkness*: a carved stone that replays a woodland ritual, a human voice and a buzzing voice, when you hold it to your ear.
6. **Dream acoustics.** Dreamlands voices get a soft, wide reverb; Waking-World voices are dry and close. Players feel which world they're in.
7. **Insight-only voices.** At high Insight you hear what creatures are *really* saying: a second subtitled layer on top of their barks.
8. **Doom changes the town.** As Doom rises, greeting pools swap to frightened, then hollow versions.
9. **The Archsage in your head (Mindspeak, §15.8).** His lines play with no visible speaker, panned slightly to one side. He comments on what you do: unprompted remarks when you enter a new town, find a cult symbol or read a forbidden book. At low Sanity his voice glitches, and sometimes a line is **not really him**, but something on the other side wearing his voice.
10. **Portal voices.** Unsealed portals mutter. The closer you get, the clearer the words, in the enemy's language. As you seal a portal, the voice rises into a scream and cuts off.

### 7.5 Production pipeline

```
 tools/voice/lines.csv  →  generate.py (ElevenLabs API)  →  master.sh (ffmpeg)  →  Data Files/Sound/Vo/tdl/...
 (id, speaker, voice_id,      batch, retries, caches         loudness-normalise,       hooked in by voice.lua
  text, tags, context)        by text hash                   trim, mono MP3
```

- **Design voices, don't clone them.** Use ElevenLabs **Voice Design** (a voice from a text description) or the voice library. **Never clone a real person** without written consent. That includes Morrowind's original voice actors and well-known audiobook narrators. Nexus Mods removes AI voice work that copies real actors without consent.
- **Keep a voice registry** (`voices.json`: character → voice ID, model, settings) so re-generated lines match.
- **Pronunciation:** add alias rules or phonetic respellings for Mythos names (Nyarlathotep, Kadath, Ulthar, Celephaïs, Yog-Sothoth, Ngranek, Inganok) and fix them once, centrally.
- **Expressive tags:** the expressive model supports audio tags like `[whispers]`, `[laughs]`, `[coughs]`. Use them for Zadok, the whispers and Nyarlathotep's amusement.
- **Generate several takes** of every important line and pick the best by ear. Store the takes outside `Data Files/`.
- **Mastering:** normalise loudness consistently across all lines, trim silence, export **mono MP3** at 44.1 kHz. Morrowind moves NPC mouths from the volume of the audio, so clean starts and ends matter.
- **Hooking it in:** MWSE `tes3.say` (with a subtitle) from `voice.lua`, triggered by dialogue events. Vanilla `Say` in a dialogue result works as a fallback. OpenMW Lua has an equivalent `say` call for the port.
- **Subtitles always on** for voiced lines, plus an MCM option to turn voiceover off.

---

## 8. Assets and Licensing

- **Bethesda assets:** re-use, re-texture and modify freely *inside this mod*. Never ship the original BSA/ESM files, and never take assets out of Morrowind into a standalone release (§1.1).
- **Other modders' assets:** many Morrowind modders allow re-use with credit, but **check each readme**. Some require permission, and some forbid use in total conversions.
- **New assets:** CC0 or CC-BY sources, converted to NIF in Blender. Check that each license allows redistribution inside a mod.
- **ElevenLabs:** keep your subscription active while generating (your plan's terms cover the output you generate under it). Record which plan and date each batch was made under in `CREDITS.md`.
- **Meshy.ai (Pro):** approved for 3D models and textures (§16.4). Under a paid plan the models are private and yours to use. Keep them out of the public Meshy Community, and upload only images and models you have the rights to. Record the plan, date and prompt for each model in `CREDITS.md`.
- **AI disclosure:** Nexus Mods requires tagging content that uses AI-generated assets. Say plainly that the voices are AI-generated with designed (not cloned) voices, which 3D models and textures were generated with Meshy, and which text was AI-assisted.
- **Call of Cthulhu books:** use them as **reading for inspiration only**. Don't copy their text, stat blocks, art or invented names into the mod (§11.1).
- **`CREDITS.md`:** every asset, author, URL, license, and date, kept from day one.
- **Your own license:** consider releasing the **Lua code** under MIT so other modders can learn from it, while the mod's content stays "free to download, ask before re-using."

---

## 9. Releasing

1. **Where:** **Nexus Mods** (opt **out** of Donation Points) and **ModDB**. Keep the Lua source on GitHub.
2. **Devlog early:** short clips of the descent down the Seventy Steps, the Sanity effects and Nyarlathotep's voice are the hook.
3. **Release the vertical slice as a demo** (Acts 1–2) to get feedback on combat and Sanity before building everything.
4. **Mod page checklist:** requirements (Morrowind + expansions, MWSE version, optional MGE XE), install steps, load order, known conflicts (it's a total conversion: say "use on a clean install / separate profile"), AI disclosure, credits, and a content note (§14.2).
5. **No monetization of any kind:** no Patreon tiers for early access, no paid "supporter builds." This keeps you inside Bethesda's rules.

---

## 10. Risks and How to Handle Them

| Risk | Mitigation |
|---|---|
| Total-conversion scope | Vertical slice first (§1.5). Each act should be playable on its own. |
| Engine limits (one worldspace, old AI, dice-roll combat) | Lua for new systems; interior "exterior-like" cells for Waking-World regions; test combat changes early (§12). |
| Plugin merge pain in git | `tes3conv` JSON as the source; one person edits a given region at a time. |
| Dirty edits to vanilla records | `tes3cmd clean` before every release. |
| MWSE vs. OpenMW split | Keep logic in plain Lua modules with a thin engine layer, so only the layer changes for a port. |
| Voice consistency over months | A voice registry, fixed model/settings, and keep every generated take. |
| AI voice policy changes | Designed voices only, consent for anything else, keep records of when and how each line was made. |
| Asset licenses | `CREDITS.md` from day one; re-check before release. |
| AI-generated models look out of place (too detailed, mixed styles, broken topology) | Remesh to Morrowind budgets, downscale and paint over textures, one shared prompt style, and test every model next to vanilla assets in game (§16.4). |
| Copyrighted RPG material creeping in | Write from Lovecraft's text; check names against §14.2 before using them. |

---

## 11. Ideas from the Call of Cthulhu RPG

Chaosium's *Call of Cthulhu* (1981–today, now in its 7th edition) is the tabletop RPG that defined how Lovecraftian *games* feel: fragile investigators, sanity as a resource you spend, and knowledge that destroys you. Morrowind is already a percentile-skill RPG with Luck as an attribute, so many of these ideas fit naturally.

### 11.1 What you can and can't take

| ✅ Safe to borrow (game mechanics and general ideas) | ❌ Avoid (Chaosium's protected expression and trademarks) |
|---|---|
| Roll-under percentile checks with success tiers | The name **"Call of Cthulhu"** in your title or promotion in a way that implies affiliation |
| Sanity that drops when you witness horrors and comes back slowly | Copying rulebook text, tables, Sanity-loss values, or monster stat blocks |
| Knowledge of the Mythos lowering maximum sanity | Chaosium's art, logos, trade dress or character sheet layout |
| Pushing a failed roll at a risk | Chaosium's scenarios (*Masks of Nyarlathotep*, *The Haunting*, etc.) and the NPCs they invented |
| Skills that improve when used (Morrowind already does this) | Their exact terms ("Cthulhu Mythos skill," "Keeper," "Bout of Madness"). Use your own words, as below. |

> **Note:** game mechanics are not copyrightable in the US, but their *written expression* is. Chaosium has released its **Basic Roleplaying (BRP)** system under the **ORC License**, and also publishes a fan-use policy. If you ever want to use their terms directly, read those first. Everything below is renamed so you don't need them.

### 11.2 Mechanics to adapt

| CoC RPG idea | The Dreamlands version | How it works in Morrowind |
|---|---|---|
| **Percentile checks** with Regular / Hard / Extreme success | **Success tiers** on scripted checks: **Fumble**, **Fail**, **Success**, **Strong** (≤ ½ skill), **Sublime** (≤ ⅕ skill) | Lua rolls against the player's skill (Speechcraft, Mysticism, Security...) for quest and dialogue checks; tiers give better results |
| **Pushing a roll** | **Press On:** retry a failed scripted check once; fail again and a **Dire Consequence** fires (an ambush, a Sanity loss, a hostile NPC) | Dialogue choice after a failed check |
| **Luck points** | **Luck** (the attribute) as a spendable pool: drain it temporarily to pass a check | Restore it by resting at a Hearth (safe inn or shrine) |
| **Sanity loss on witnessing horror** (smaller on a pass, larger on a fail) | **Horror rating** on each creature, e.g. `1 / 1d6`. First sight triggers a **Composure check** against Willpower + Sanity | Fired when a creature enters line of sight for the first time in a cell |
| **Becoming used to horrors** | **Familiarity:** the Sanity you can lose to one *kind* of creature per day is capped | Tracked per creature type |
| **Temporary and indefinite insanity** | **Fractures** (§11.3) on big losses in one go; **Afflictions** on losing ⅕ of your Sanity in a day | Timed Lua effects |
| **Mythos knowledge lowers max Sanity** | **Insight** lowers max Sanity: **max Sanity = 99 − 5 × Insight** | Shown on the HUD bar |
| **Occupations** | **Waking Lives** = classes (§3.3) with a unique starting item each | Character creation |
| **Backstory** | **Anchors:** three personal anchors chosen at creation (*"My grey cat," "The old house on Benefit Street," "Faith in reason"*). Sacrifice one once to pass a Composure check automatically. Madness can **corrupt** an Anchor. | Dialogue + Lua state |
| **Mythos tomes** | **Tomes** read over several in-game days (§4 idea 7) | Rest/wait hooks |
| **Spells cost magic and Sanity** | **Mythos spells** cost Magicka **and** Sanity, even when the cast fails | `spellCast` event |
| **Chases** | **Pursuits:** scripted chase sequences where something follows you through a cell (the Unseen Brother, the Hound) | Scripted AI + timers |
| **Clues and handouts** | **Clues** in Found Documents (§4 idea 8) unlock dialogue options and weaken bosses | Journal + global variables |
| **The Game Master** | **The Dreamwarden** (§4 idea 9) | `director.lua` |
| **Eras** | **Dream Eras:** an optional New Game+ setting (*The Dark Age* default, *Gaslight Dreams*, *Jazz-Age Sleep*) that swaps NPC clothing and some items | Global variable read by Lua |

### 11.3 Fractures (short-lived madness)

When a **Fracture** happens, roll on this table (stored as editable Lua data):

| d10 | Fracture | Effect (20–40 s) |
|---|---|---|
| 1 | **Amnesia** | The HUD map and compass disappear; journal entries are unreadable. |
| 2 | **Flight** | You can't attack; movement speed +30%; the camera pulls away from the threat. |
| 3 | **Hysteria** | Screen shake, laughter whispers; Fatigue regenerates faster. |
| 4 | **Paranoia** | Fake enemies appear around you and vanish when struck. Real ones hide among them. |
| 5 | **Catatonia** | You can't move for a few seconds, then are slowed. |
| 6 | **Violent Outburst** | +50% weapon damage, but allies and NPCs nearby can be hit and may turn hostile. |
| 7 | **Phobia** (lasting) | You gain a phobia of the creature type that caused it. Seeing it always costs +1 Sanity. |
| 8 | **Mania** (lasting) | A compulsion, e.g. "must rest in darkness" or "must carry a cat figurine," with a Sanity penalty for ignoring it. |
| 9 | **Whispers** | Dialogue text rewrites itself; one NPC's greeting voice becomes wrong (§7.4) until you rest. |
| 10 | **Revelation** | *Good:* +1 Insight, and you see invisible creatures for the rest of the day (with the max-Sanity cost). |

---

## 12. Combat: Morrowind × Bloodborne

Morrowind's combat is a hidden dice roll, which modern players often find unsatisfying. MWSE can change it, and many combat mods prove it's possible. The goal: **aggressive, readable, skill-based melee** that still respects Morrowind's character skills.

### 12.1 Bloodborne-style aggression

| Mechanic | How it works | Why it matters |
|---|---|---|
| **Hits always land when they connect** | Weapon skill scales damage and stagger instead of hit chance | Removes the "swing and miss" problem |
| **Reclaim** | When you take damage, part of it stays as a **fading orange segment** on the health bar for 3 s. Hitting enemies during that time wins it back. | Getting hit makes you want to attack |
| **Resolve Reclaim** | The same for **Sanity**: Sanity lost to a Horror reveal can be reclaimed by **killing** that creature within 10 s | Face your fears, literally |
| **Quickstep** | A fast dodge (double-tap a direction) with brief invulnerability, costing Fatigue | Movement is defense; shields are rare in the Dreamlands |
| **Severance** (parry → critical) | Hit an enemy with an off-hand crossbow bolt or an Elder Sign flash **during its wind-up** to stagger it, then attack for a heavy critical | High risk, high reward |
| **Frenzy** | Builds with hits, drains when passive. At full: +30% damage, but you take +30% damage and slowly lose Sanity | Keeps you pushing forward |

### 12.2 Skyrim-style touches

- **Power attacks:** holding attack already exists in Morrowind; add directional effects (forward = lunge, back = sweep).
- **Utterances:** short eldritch words with long cooldowns (a cat-yowl fear cone; a Dreamer's word that dispels wards), written in an invented "Aklo-like" script.
- **Stealth matters:** darkness and light sources affect detection more strongly than vanilla; sneak attacks are deadly.
- **Optional finisher close-ups:** short and skippable.

### 12.3 Ranged weapons

Crossbows, slings and throwing weapons, plus rare, unreliable **hand-cannons** brewed up by the Collegium's alchemists (slow reload, very high damage, sometimes misfire). They are mostly used as **parry tools** (Severance), not main weapons.

### 12.4 Enemy AI

Morrowind's AI is simple. Use Lua to give important enemies **readable wind-ups** (an animation + sound cue before big attacks), **groups that flank**, and **retreat at low health**. Bosses get scripted phases (§14.7).

### 12.5 Dream-Shapes: playing as monsters

Using the Bloodmoon werewolf framework (§4 idea 6), each shape changes **movement, senses and attacks**. Senses use MGE XE / OpenMW post-processing shaders.

| Shape | Movement | Senses (shader) | Signature move |
|---|---|---|---|
| **Cat of Ulthar** | Fast, high jumps, silent | **Darkvision:** dark areas lift to blue-grey | Pounce-and-pin |
| **Ghoul** | Hunched, fast in tunnels | **Scent trails:** wounded creatures leave red trails | Feed on a corpse to heal |
| **Night-gaunt** | Levitation-based flight | **Faceless:** you see by echo-outlines; silent things are invisible | Silent Abduction: lift an enemy and drop it |
| **Deep One** (Innsmouth path) | Fast swimming, water breathing | Underwater clarity; land view **blurs as you dry out** | Drag an enemy underwater |

**Instinct Prompts:** in a Dream-Shape, urges flash on screen (*"FEED," "FLEE THE LIGHT," "HUNT THE SMALL ONE"*). Follow one within a few seconds for a buff, or resist it to keep a little Sanity.

### 12.6 Settings

MCM options for: vanilla vs. new combat, dodge input, Frenzy on/off, screen shake, finisher close-ups, shader intensity.

---

## 13. Procedural Help for Dungeons

Most of the world should be **hand-built** in the Construction Set: that's where Morrowind mods get their character. Procedural tools help with the **large, repetitive spaces**: the Underworld's caverns, the depths below Exham Priory, the tunnels under the Antarctic city.

### 13.1 Approach

```
 Lovecraft passage → layout spec (JSON) → generator (Python) → tes3conv JSON cell → merge into ESM → hand-polish in CS
```

- **The generator runs offline** and writes cells as `tes3conv` JSON: which Morrowind dungeon pieces go where (Dwemer, cave, Daedric kits are already modular).
- **Wave Function Collapse** over Morrowind's modular kit pieces, with adjacency rules for which pieces fit together.
- **Validators:** every exit reachable, no gaps between pieces, enough light sources and hiding spots, a maximum distance between safe places.
- **Then a human passes over it:** add landmarks, clutter, story items and lighting by hand. Fully generated dungeons all look alike.

### 13.2 Design guidelines

- **One hand-made landmark per area**, generated corridors around it.
- **Non-Euclidean as a feature:** doors that lead back into the same room, stairs that loop, rooms bigger inside than outside. In Morrowind these are just **teleport doors** placed carefully, which makes the Witch House and R'lyeh cheap to build.
- **Optional ML helpers:** a language model can draft the layout spec from Lovecraft's description of a place, and sentence-transformers can match tagged Morrowind meshes to the mood of the spec. Keep these offline and only use them on public-domain text.

---

## 14. Beyond the Dreamlands: Waking-World Horrors

The Dreamlands are only part of Lovecraft. His best-known horrors live in the **Waking World**: Innsmouth, Dunwich, Arkham, Antarctica, the hills of Vermont, and sunken R'lyeh.

### 14.1 Story frame: the Wall of Sleep is breaking

- **Nyarlathotep is weakening the Wall of Sleep** (from *Beyond the Wall of Sleep*). The sky cities' armies come through **portals** that open where the Wall is thin (**Thin Places**), and on the waking side **Cthulhu's cult** helps open them, hoping their own god will wake when the Wall falls.
- The waking world is a **dark-ages** version of Lovecraft's New England and the lands beyond it. The regions below are where the story can go:

| When | Waking-World region |
|---|---|
| **Demo (Part I)** | **Arkham**, **Kingsport**, **Dunwich hills**, **Aylesbury** (§15.6). Innsmouth's gates are shut: you see it only from a distance. |
| **Part II** | **Innsmouth & Devil Reef**; **the Drowned Coast**, the Archsage's homeland near where R'lyeh lies sunk |
| **Part II (later)** | **The Mountains of Madness** (the frozen north), **Exham Priory** (across the sea), **the hills of the Mi-Go**, **Pnakotus** |
| **Endgame** | **R'lyeh Rising** or **The Dunwich Gate** |

### 14.2 Copyright notes for these works

| Status | Works |
|---|---|
| **Public domain by date** (published 1930 or earlier) | *Dagon* (1919), *Herbert West: Reanimator* (1922), *The Rats in the Walls* (1924), *The Hound* (1924), *The Festival* (1925), *The Colour Out of Space* (1927), *The Call of Cthulhu* (1928), *The Dunwich Horror* (1929), *The Lurking Fear* (1923), *The Music of Erich Zann* (1922), *Beyond the Wall of Sleep* (1919) |
| **Widely treated as public domain** (the general view is that copyright renewals were never validly filed, and many games use these freely, but the date alone doesn't settle it) | *The Whisperer in Darkness* (1931), *The Dreams in the Witch House* (1933), *From Beyond* (1934, written 1920), *At the Mountains of Madness* (1936), *The Shadow over Innsmouth* (1936), *The Shadow out of Time* (1936), *The Haunter of the Dark* (1936), *The Thing on the Doorstep* (1937), *The Case of Charles Dexter Ward* (1941) |
| **⚠ Not Lovecraft. Avoid unless you've checked the specific case** | **Revisions and collaborations** (*The Mound*, *The Curse of Yig*, *Medusa's Coil*, *Out of the Aeons*, *The Horror in the Museum*), whose rights may involve the co-author's estate. **Other authors' creatures:** Hounds of Tindalos (F.B. Long), Tsathoggua (C.A. Smith), Byakhee, Cthugha, and the Derleth "Elder Gods" (August Derleth), Dark Young (later RPG material), Shudde M'ell (Brian Lumley). |

> **Rule of thumb:** use the creature *as Lovecraft described it in his own story*, not later RPG or fan versions. For example, Shub-Niggurath appears in Lovecraft only as an invoked name ("the Black Goat of the Woods with a Thousand Young"), so build her from that phrase, not from later stat blocks.

> **Content note:** several of these stories contain Lovecraft's racism, including the xenophobia of *Innsmouth* and the way *The Call of Cthulhu* describes its cultists. Adapt the *cosmic* horror, not the prejudice: cults are cults of every background, Innsmouth's horror is the sea and inheritance, and leave out *The Horror at Red Hook* and *Arthur Jermyn* entirely. This applies to voice direction too: no accents used as shorthand for "sinister."

### 14.3 Waking-World enemies and factions

| Faction | Source | How they fight | Notable NPCs / items | Signature mechanic |
|---|---|---|---|---|
| **Deep Ones & the Esoteric Order of Dagon** | *Dagon*, *The Shadow over Innsmouth* | Ambush from water, heal in water | Deep One raiders, Innsmouth hybrids, Father Dagon, Mother Hydra, Obed Marsh's gold | **The Change:** their hits apply stacks; at 3 stacks the player begins to **turn** (water breathing, swim speed, lower max Sanity, NPCs react). Curable until a point of no return. **Rising Tide** in Innsmouth's flooded streets. |
| **Cult of Cthulhu & the Spawn** | *The Call of Cthulhu* | Rituals, numbers | Cultists, the Spawn of Cthulhu, the stone idol | **Dreaming Pressure:** in R'lyeh, Sanity drains slowly the whole time. |
| **Elder Things & Shoggoths** | *At the Mountains of Madness* | Elder Things are scholars, shoggoths are unstoppable | Elder Thing ruins, shoggoths, blind albino penguins | **Shoggoth Mimicry:** shoggoths copy the last attack type used on them and resist it. |
| **Mi-Go** | *The Whisperer in Darkness* | Flying, surgical, capture | Mi-Go surgeons, brain cylinders, the voice machine, Akeley's letters | **Brain Cylinders:** captured NPCs can be talked to in their cylinders. **Unphotographable:** Mi-Go don't show on the local map. |
| **The Great Race of Yith** | *The Shadow out of Time* | Slow, powerful, lightning weapons | Yithian archivists, the Library of Pnakotus | **Mind-Exchange:** you're thrown into a Yithian body for a scripted sequence. |
| **Flying Polyps** | *The Shadow out of Time* | Invisible wind attacks | Basalt trapdoors | Only visible at Insight ≥ 4; otherwise you hear whistling and see dust. |
| **The Dunwich Whateleys** | *The Dunwich Horror* | Summoning, an invisible giant | Wilbur, Old Whateley, Lavinia, the Unseen Brother, whippoorwills | **The Unseen Brother:** an invisible giant that leaves **footprints and crushed fences**. The *Powder of Ibn Ghazi* reveals it. **Whippoorwills** gather when someone is about to die. |
| **Reanimators** | *Herbert West: Reanimator* | Unstable undead | Herbert West, reanimated subjects, West's reagent | **Reanimation:** fallen enemies may rise frenzied and attack anyone, including other enemies. |
| **Witches & Familiars** | *The Dreams in the Witch House* | Theft, impossible angles | Keziah Mason, Brown Jenkin, the witch-cult's Black Man | **Brown Jenkin** steals items from your inventory. The **Witch House** is full of looping doors (§13.2). |
| **Necromancers** | *The Case of Charles Dexter Ward* | Raise and dismiss the dead | Joseph Curwen, the essential Saltes, the Things in the Pits | **Saltes:** dust of the dead, raised by formula. The *Formula of Dismissal* (a spell) destroys any raised creature instantly. |
| **Body-Thieves** | *The Thing on the Doorstep* | Possession | Ephraim and Asenath Waite | **Body Theft** (a boss mechanic, §14.7). |
| **The Rats and the Priory** | *The Rats in the Walls* | Endless swarms; deeper is worse | Exham Priory, the twilit grotto | **Descent:** each level of the dungeon is worse than the last; you hear the rats in the walls before you see them. |
| **The Colour Out of Space** | *The Colour Out of Space* | A spreading area, not a creature | The blasted heath, the well | **Blight:** a spreading zone that **drains** health and **desaturates** the world (shader). It can't be killed, only contained or escaped. |
| **Things Glimpsed Beyond** | *From Beyond* | Insight punishment | Tillinghast's resonator | **Always There:** jelly-like beings exist everywhere but stay harmless until your Insight is high enough to see them. Then they attack. |
| **Lurkers** | *The Lurking Fear* | Tunnel ambushes in storms | The Martense mansion | **Lightning Reveal:** lurkers are only visible during lightning flashes (thunderstorm weather). |
| **The Hound's Curse** | *The Hound* | A stalker that follows you across the game | The jade amulet | **Nemesis:** wearing the jade amulet makes you stronger, but **the Hound hunts you** in random places, stronger each time, until you return the amulet to its grave. |

### 14.4 Waking-World NPCs and companions (all Lovecraft characters)

> **Dark-ages casting:** these are 1920s characters in Lovecraft. Use them as **medieval versions with the same names and roles** (Armitage as the Collegium's librarian, Legrasse as a watch captain, Herbert West as a grave-robbing barber-surgeon) or as **their ancestors**. Families like the Whateleys, Marshes and Curwens work especially well as old bloodlines.

| Character | Source | Role | What they offer |
|---|---|---|---|
| **Dr. Henry Armitage** | *The Dunwich Horror* | Miskatonic quest-giver | The *Powder of Ibn Ghazi*; Tome translation |
| **Francis Wayland Thurston** | *The Call of Cthulhu* | Ally, Clue source | His collected clippings (Found Documents) |
| **Inspector John Raymond Legrasse** | *The Call of Cthulhu* | Companion | Bonus damage against cultists |
| **Professor William Dyer** | *At the Mountains of Madness* | Expedition leader | Gear and passage to Antarctica |
| **Albert N. Wilmarth** | *The Whisperer in Darkness* | Quest-giver | The singing stone (§7.4) |
| **Nathaniel Wingate Peaslee** | *The Shadow out of Time* | Ally | Protection against Mind-Exchange |
| **Walter Gilman** | *The Dreams in the Witch House* | Companion | Can use the Witch House's looping doors |
| **Dr. Marinus Bicknell Willett** | *The Case of Charles Dexter Ward* | Quest-giver | The *Formula of Dismissal* spell |
| **Daniel Upton** | *The Thing on the Doorstep* | Ally | The blade that matters in the Body Theft fight |

### 14.5 Waking-World artifacts and spells

- **The Necronomicon** *(Tome)*: by far the most powerful Tome. Reading it takes several in-game days and gives **+4 Insight, −30 Sanity**, and a Mythos spell.
- **Powder of Ibn Ghazi** *(consumable)*: reveals invisible creatures for a short time.
- **The Voorish Sign** *(spell)*: see invisible things yourself.
- **West's Reagent** *(consumable)*: raise a fallen enemy as a frenzied ally (§14.3).
- **Brain Cylinder** *(misc item)*: holds a captive mind you can talk to.
- **Lightning Projector** *(weapon)*: Yithian beam weapon; hits invisible creatures.
- **The Jade Amulet** *(amulet)*: big bonuses, plus the Hound's Curse.
- **Tillinghast's Resonator** *(misc item)*: +2 Insight while active; the jelly-things become visible and hostile.
- **Obed Marsh's Gold** *(misc item)*: very valuable, but carrying it adds *Change* stacks over time.
- **The Shining Trapezohedron** *(misc item)*: in darkness, calls the Haunter of the Dark. In full light, the Haunter can't appear.

### 14.6 Waking-World regions

| Region | Built from | Key features |
|---|---|---|
| **Innsmouth harbor** | Imperial/Bloodmoon buildings, new textures | Decaying fishing town, Devil Reef offshore, flooded lower streets |
| **The Antarctic city** | Dwemer ruins under Bloodmoon ice | Cyclopean ruins, dark tunnels, shoggoth hunts |
| **Yuggoth outpost (Vermont hills)** | Telvanni fungal pieces, Bloodmoon forests | Glowing fungi, Akeley's farmhouse |
| **Dunwich hills** | Bloodmoon forests, stone circles | Round hills, Sentinel Hill, a decaying farmhouse, footprint trails |
| **Arkham & Miskatonic** | Imperial town pieces, new textures | Gambrel roofs, the Collegium library, graveyards |
| **The Witch House** | Imperial interiors, slanted | A repeating attic room with looping doors |
| **Exham Priory** | Imperial/Daedric ruins → caves | Floors that get worse the deeper you go |
| **R'lyeh** | Daedric ruins, green-stained, distorted scale | Wrong angles, wet green stone, rising water |
| **The blasted heath** | Ascadian Isles farmland, desaturated | The Blight spreading from the well |

### 14.7 Bosses

| Boss | Where | Mechanics |
|---|---|---|
| **Nyarlathotep** (final, Act 6) | Kadath's onyx hall | His form is chosen by how you played (§4 idea 4). Each form has its own phases, voice treatment (§7.2) and weaknesses found through Clues. |
| **Cthulhu: R'lyeh Rising** | R'lyeh | **Phase 1:** stop the cultists' chant before it finishes. **Phase 2:** Cthulhu rises; Dreaming Pressure drains Sanity. **Phase 3:** as in the story, Cthulhu **comes back together** after being "destroyed." You have a short window to scatter the pieces before he reforms, then you must escape. |
| **The Dunwich Gate: Yog-Sothoth's Spawn** | Sentinel Hill | The Unseen Brother charges up the hill. Throw the Powder of Ibn Ghazi, then defend Armitage's party while they chant the counter-formula. |
| **Ephraim Waite** | Crowninshield house | He steals your body. You fight him from a weaker body, and landing a Severance (§12.1) on your own body brings you back. |
| **The Colour** (cannot be killed) | The blasted heath | Survive and contain the Blight for 3 minutes; the outcome depends on how much of the heath you saved. |

---

## 15. Storyline, Part I: The Demo

An ordinary shop helper in a dark-ages Arkham is told by the valley's greatest wizard that they must train to stop an invasion from the Dreamlands. The training keeps getting cut short by attacks. Between attacks you train, travel, take sidequests and grow stronger. The demo ends with a boss fight at Kingsport. The portal into the Dreamlands and the spell to reach the sky cities come later.

> **The full plot** (Part I and Part II) is written up in [STORY.md](STORY.md), with game-design notes in [ANNOTATIONS.md](ANNOTATIONS.md). It follows the recommended options below, with one change: **the ancient warrior is the player**, through a time loop at the end of Part II (ANNOTATIONS.md ^6, ^53–55), instead of option (C) "the bloodline." The tooling that drafts prose in Lovecraft's voice is in [tools/story/](tools/story/README.md).

### 15.1 Lore changes (bending Lovecraft)

| In Lovecraft | In this mod | Why it fits |
|---|---|---|
| The horrors come from outer space | They come from **the sky cities of the Dreamlands** | In *Dream-Quest*, the Moon-beasts' **black galleys** already sail off the edge of the world and up through the sky to the Moon. A sky-borne invasion is a small step. |
| **Serannian**, the pink-marble city in the clouds where King Kuranes spends half of each year (*Celephaïs*, *Dream-Quest*) | **Fallen Serannian:** seized by the Moon-beasts, its marble turned black, its harbour now a dock for black galleys | A beautiful Lovecraft place corrupted makes a stronger final destination than an invented one. |
| The Moon-beasts' cities on the Moon | **The second sky city**, where the galleys are built and the armies gather | Canon already puts them in the sky. |
| Nyarlathotep, the Moon-beasts' master | **Still the one directing everything**, from Kadath | Canon. |
| Arkham, Kingsport, Dunwich in 1920s New England | **Medieval towns of the Miskatonic Valley** | Morrowind's assets are medieval anyway. |
| Thin places, the Wall of Sleep | **Portals** that open where the Wall is thin, and must be **sealed** | Gives the game its core verb. |
| Cthulhu's cult | **Still in the waking world.** The Archsage once led it, and cultists help open portals from this side | Human enemies beside bandits, and a personal story for the Archsage. |
| The Elder Sign | **The sealing sign** the Archsage teaches you | Lovecraft mentions it; your version of it is original. |

### 15.2 Main characters

**The player.** An ordinary shop helper, any race or sex. Why are they "destined"? Choose one, or combine:
- **(A) The dreamer** *(recommended core)*: you have dreamed of a cloud city since childhood. It is Serannian, and your mind already half-lives in the Dreamlands. That makes you resistant to madness and able to seal portals that would kill anyone else.
- **(B) The prophecy:** the ancient warrior (below) left a prophecy that the Archsage has been waiting on for decades.
- **(C) The bloodline:** a late reveal that you descend from the ancient warrior.

**The Archsage** *(name to be decided; placeholder ideas: Corwin Sallow, Ezra Keel, Thaddeus Wren)*.
- **Origin:** born on a reef-isle on **the Drowned Coast**, the nearest dry land to where R'lyeh lies sunk. Make this an **invented place**. Avoid Lovecraft's real-world Pacific islands (such as Ponape in *Innsmouth*), which he wrote about with racist assumptions.
- **Past:** rose to **high priest of Cthulhu's cult**. On the night of a great ritual, an **ancient warrior** broke the rite, defeated him, and **spared his life**. That mercy broke his faith. He spent the rest of his life learning to fight what he once served.
- **Why he matters:** he still knows **the enemy's black magic**. That is how he can teach you to seal portals, and why he is the only one who saw the invasion coming.
- **Why he won't help in person.** Choose one:
  - **(A) He is holding something back** *(recommended)*: his body sits in a trance at his tower, keeping a ward over the coast against R'lyeh's dreaming. If he leaves, Cthulhu's dreams flood the valley. This also sets up Part II.
  - **(B) An oath:** he swore to the warrior who spared him that he would never again raise his hand in violence.
  - **(C) He'd be seen:** the cult would sense him the moment he used his power, and come for him.
- **Telepathy (Mindspeak):** you can talk to him anywhere through a power he gives you (§15.8). He advises, teaches, warns and comments, but he can't fight for you.
- **A thread to pull later:** the old wet voice under his (§7.2). Is he fully free of Cthulhu? Leave the question open in the demo.

**The ancient warrior.** Who spared the Archsage. Ideas:
- Their **sword hangs over the shop counter**, unsold for years. Nobody knows what it is. It's part of why the Archsage comes to *this* shop. You earn the right to carry it at the end of the demo.
- In Part II you might meet them in the Dreamlands, as a dreamer who never woke up.

**Others in the demo.**
- **The Shopkeeper:** your employer. Gruff and kind; gives the tutorial errands. Put them in danger during the first incursion so the stakes are personal.
- **Trainers** (since the Archsage won't train you in person): **the Captain of the Arkham Watch** (weapons), **a Collegium magister** (wards and spells, an early Armitage figure), **an old Kingsport mariner** (ranged weapons, and lore about the sky).
- **The Apprentice:** the Archsage's **former apprentice from his cult days**, now a priest who opens portals from the waking side. They are the human face of the enemy in the demo, they escape at the end, and they become a recurring villain.

### 15.3 Demo structure

```
 Prologue    Ordinary Days ............ the shop (tutorial)
 Chapter 1   The Archsage Comes ........ the warning; Mindspeak
 Chapter 2   First Lessons ............. Steel; the Sign (sealing)
 Chapter 3   The First Incursion ....... Arkham (training cut short)
 Interlude   Warding ................... resume training; open world; sidequests
 Chapter 4   The Second Incursion ...... the Dunwich hills
 Interlude   The Black Tongue .......... an enemy spell; travel; sidequests
 Chapter 5   The Galley from the Clouds  Kingsport; the demo boss
```

**Prologue: Ordinary Days.** Opening the shop teaches the basics, and character creation is woven in: stock the shelves (inventory), sell to a haggling customer (barter), deliver an order across town (map and travel), and chase something out of the cellar (combat). Townsfolk gossip about strange lights in the clouds.

**Chapter 1: The Archsage Comes.** He arrives at dusk and asks about your dreams before you tell him anything. He tests you by showing you a **horror trapped in a jar**: your first Composure check and your first Sanity loss. He explains what is coming, gives you the **Mindspeak** power, and leaves for his tower.

**Chapter 2: First Lessons.**
- **The Lesson of Steel** with the Captain of the Watch: weapons, dodging and parrying (§12).
- **The Lesson of the Sign** from the Archsage over Mindspeak, late at night: how to **seal a portal**. He's rushing, and he says it's "too early."
- **The Lesson of Warding** begins the next day, and is **interrupted**.

**Chapter 3: The First Incursion (Arkham).** The sky tears open above the old burying ground. **Zoog swarms** and **Men of Leng raiders** pour into the streets. You have one weapon, the sealing sign, and the Watch beside you. Save townsfolk, reach the portal and seal it. The shop is damaged and the Shopkeeper is hurt. Arkham changes afterwards: barricades, refugees, frightened greetings.

**Interlude: Warding.** Training resumes: the Collegium teaches a **ward spell** and a **calming draught** (Sanity tools). The map opens up: the road to Aylesbury, bandits, wolves, faction joining, shops and the first major sidequests (§15.6).

**Chapter 4: The Second Incursion (the Dunwich hills).** A portal opens inside a hilltop **stone circle**. **Ghasts** (who die in sunlight, so the fight is at night and torches matter) and **cultists** guarding the portal from this side. You meet **the Apprentice**, and learn that someone in the waking world is opening the portals.

**Interlude: The Black Tongue.** The Archsage reluctantly teaches you **one spell from the enemy's own black magic**. It is very strong and costs Sanity to cast. His voice is at its strangest here. Travel to Kingsport; more sidequests.

**Chapter 5: The Galley from the Clouds (Kingsport).** A **black galley** descends out of the sea-mist over Kingsport's cliffs. **Moon-beasts** and their **Leng slaves** raid the harbour while **three portals** open across town. Seal them while the galley hangs overhead, then climb toward **the Strange High House** on the cliff-top for the boss.

**The demo boss.** Choose one:
- **(A) The Shantak Rider** *(recommended)*: a Moon-beast overseer riding a **Shantak**, the huge scaled bird of *Dream-Quest*. Phase 1 is in the air: bring it down with bolts and spells while it dives at you. Phase 2 is on foot, on the cliff edge, against the overseer and the wounded Shantak. It matches the sky theme.
- **(B) The Apprentice transformed:** the Apprentice channels Cthulhu's dreaming and becomes something tentacled. This spends your recurring villain early.
- **(C) A Gug pushed through the great portal:** a huge, slow brute. It works better as a mid-game fight.

**Ending.** The boss falls. The Archsage looks through your eyes over Mindspeak and goes silent. Out on the water, one portal is still open, far bigger than the others, and it **cannot be sealed from this side**. Through it, for a moment, you see the city you've always dreamed of, in black marble. *End of Part I.*

### 15.4 Incursion mechanics (portals and hordes)

- **Portals** are activators that spawn **waves** on a timer while open. Lua tracks each portal's state.
- **Sealing:** stand in the portal's circle and **channel** (hold the cast key). Progress fills over a few seconds. Damage knocks some of it back. Each seal costs Magicka and a little Sanity. Higher Mysticism seals faster.
- **Ignore a portal too long** and Doom rises, the area around it corrupts, and named NPCs can die for good.
- **Underpowered on purpose:** before each incursion you are weaker than you'd like. The game makes up for it with **allies** (the Watch, villagers), **light** (torches, braziers against ghasts) and **traps** you can set off, so smart play beats grinding.

| Incursion | Where | Enemies | What it teaches |
|---|---|---|---|
| **1** | Arkham, the old burying ground | Zoog swarms, Leng raiders | Sealing, Sanity, fighting with allies |
| **2** | The Dunwich hills, a stone circle | Ghasts, cultists | Light and darkness; human enemies guarding portals |
| **3 (finale)** | Kingsport, harbour and cliffs | Moon-beasts, Leng slaves, the Shantak Rider | Several portals at once, flying enemies, a boss |

### 15.5 Training

| Lesson | Teacher | Unlocks | When |
|---|---|---|---|
| **Steel** | Captain of the Watch | Weapon basics, dodge and parry (§12) | Chapter 2 |
| **The Sign** | The Archsage (Mindspeak) | Portal sealing | Chapter 2, the night before the attack |
| **Warding** | Collegium magister | Ward spell, calming draught, Composure tricks | Starts in Chapter 2, cut short; finished in the first Interlude |
| **The Black Tongue** | The Archsage | One enemy spell (strong, costs Sanity) | Second Interlude |
| **The Sky Road** | ? | The spell that reaches the sky cities | **After the demo** (Part II) |

### 15.6 The demo's world and sidequests

**Towns:**

| Town | What it is | Built from (§4.1) |
|---|---|---|
| **Arkham** | Walled market town on the Miskatonic; the shop, the Collegium, the old burying ground | Imperial town pieces, new textures |
| **Kingsport** | Fishing port under huge sea-cliffs; the Strange High House on the cliff-top | Imperial + Bloodmoon (Raven Rock) |
| **Dunwich** | A decaying hamlet in round, wooded hills full of stone circles | Bloodmoon forests and Skaal pieces |
| **Aylesbury** | A crossroads market town in bandit country | Imperial pieces |
| **Innsmouth** | Gates shut; seen only from the coast road. A tease for Part II | — |

**Major sidequests** (based on public-domain stories, all pre-1930 unless marked):
- **The Terrible Old Man** (Kingsport; *The Terrible Old Man*, 1921). Three thieves plan to rob an ancient sea-captain who talks to bottles. Join them or warn him. Whoever goes into his house is found dead in the morning.
- **The Statement** (Arkham; *The Statement of Randolph Carter*, 1920). A scholar goes down into a tomb under the burying ground while you stay above holding a **speaking-cord** (a medieval stand-in for the story's telephone). His voice gets more frantic, and then something else answers.
- **The Viol on the Steep Street** (Arkham; *The Music of Erich Zann*, 1922). A mute viol player's music holds something back at his window. Protect him or listen to his music, at a cost.
- **The Festival** (Kingsport; *The Festival*, 1925). A midwinter procession goes down into the hill under the church. It leads to the cult, and to the Apprentice.
- **The Strange High House** (Kingsport; *The Strange High House in the Mist*, published 1931, widely treated as public domain). Climb to the house on the cliff and meet its occupant. Sets up the finale and the sky.
- **The Hill Farm** (Dunwich). Missing cattle, an old family nobody talks about, and footprints too big for any animal. Plants seeds for *The Dunwich Horror* in Part II.

**Minor quests and open-world content:**
- Shop errands and debts; collecting from customers who won't pay.
- Bandit bounties on the Aylesbury Pike; wolf and bear culls; rats in the Collegium's cellars (a nod to *The Rats in the Walls*).
- *The Unnamable* (1925): a graveyard rumour in Arkham that two scholars argue about.
- *The Tomb* (1922): a sealed family tomb in the woods that someone keeps sleeping beside.
- Faction intro quests for the Watch, the Collegium, the merchants and the thieves.
- Ordinary fantasy enemies everywhere: bandits, wolves, bears, rats, skeletons and goblins, using vanilla and Bloodmoon creatures re-textured.

### 15.7 Voice priorities for the demo

Voice these first (§7.5 pipeline): the **Archsage** (arrival scene, every Mindspeak lesson, reactions), the **Shopkeeper**, the **Captain of the Watch**, the **Apprentice**, Arkham greetings (normal and frightened, from before and after the first incursion), portal voices (§7.4), and barks for zoogs, Leng raiders, ghasts, Moon-beasts and the Shantak.

### 15.8 Implementation notes

- **Mindspeak:** a Power the Archsage gives you. Using it opens the dialogue window with the Archsage's NPC record, which is kept in a hidden cell, through MWSE. His topics are filtered by journal stage, so he always has something relevant to say. In combat, Mindspeak gives short hints only.
- **Story state:** one journal per chapter, plus global variables for incursion state, Doom and the Shopkeeper's fate.
- **Incursions:** `incursion.lua` handles portal activators, wave spawning (`tes3.createReference`), sealing channels and timers. Each incursion's waves are a data table, so they're easy to tune.
- **Demo gate:** a single `tdl_demo` flag blocks the Dreamlands portal and the Sky Road spell, and shows an "End of Part I" screen after the boss.

---

## 16. Making 3D Models (Claude and Meshy)

### 16.1 Short answer

The project uses two tools that do different jobs:

- **Meshy.ai (Pro subscription)** generates models and textures from a text prompt or an image. Use it for **organic, sculpted and one-off assets**: new creatures, idols, statues, rocks, fungi, trees, landmarks.
- **Claude writes Blender Python (`bpy`) scripts.** Use it for **anything with rules and repetition**: modular kits that snap to the grid, buildings, portals, collision. It also automates the pipeline that turns Meshy's output into Morrowind-ready NIFs.

Neither produces finished Morrowind assets. Everything still goes through Blender: reduce the polygons, fix the scale, bake the textures, set up collision, rig, and export to NIF.

**What Claude does well:**
- Builds models from code: architecture, props and kit pieces.
- Changes existing Morrowind meshes with scripts (scale, bend, add parts, merge pieces).
- Automates the pipeline: batch import of Meshy exports, decimation, texture baking, batch NIF export, naming, collision meshes, texture paths and checks.
- Reviews screenshots you share and suggests fixes.
- Builds procedural material node setups in Blender for stone, slime and rot.

**What Claude can't do:** sculpt organic creatures, paint textures, or see a model unless you show it a render. Meshy now covers the first two.

**Recommendation:**
- Meshy for **creatures Morrowind lacks** (cats, shoggoths, Elder Things, the Great Race, the Spider of Leng; see [CREATURES.md](CREATURES.md)), **replacement heads and parts** (a ghast's face, a Gug's vertical mouth, the Shantak's horse head), and **unique statics**.
- Claude's scripts for **architecture, kits and tooling**.
- For creatures Morrowind *can* cover, still **kitbash vanilla** first: it's faster and matches the game's look.

### 16.2 Which tool for which asset

| Asset | Tool | Approach |
|---|---|---|
| **New creatures** (cat of Ulthar, shoggoth, Elder Thing, Yithian, Spider of Leng, Mi-Go) | **Meshy** | Generate, remesh, and rig onto the closest vanilla skeleton (§16.4) |
| **Replacement creature parts** (noseless ghast head, Gug head with a vertical mouth, horse-headed Shantak, Moon-beast snout) | **Meshy** + kitbash | Generate the part only, then attach it to a vanilla body in Blender |
| **NPC heads and hair** (Men of Leng, Deep Ones, Innsmouth hybrids) | **Meshy** | Generate a head, fit it to the vanilla head bone and neck seam |
| **Idols, statues, altars, relics** (the Dagon idol, Bokrug, Kadath carvings, the jade amulet) | **Meshy** | The best use of Meshy: detailed, organic and one-off |
| **Rocks, cliffs, monoliths, standing stones** | **Meshy** | Landscape-dressing statics; generate a few variants of each and reuse them rotated |
| **Fungi, strange trees, growths** (the Enchanted Wood, Yuggoth's fungi, tentacles) | **Meshy** or a Claude curve script | Meshy for hero pieces, scripts for many variations |
| **Huge landmarks** (Ngranek's carved face, Kadath's peak, the sky cities seen from afar) | **Meshy** for the shape, then hand work | Split into pieces, keep a low-detail distant version |
| **Weapons, armour pieces, clutter, market goods** | **Meshy** | Small, low-poly; must fit vanilla grips and armour bones |
| **Portal frames, sealing circles** | Claude script | A ring of rune-stones, an emissive sigil plane, a swirling disc |
| **Cyclopean blocks, R'lyeh's wrong angles** | Claude script, Meshy for surface detail | Skewed, non-square blocks; Meshy texturing for weathering |
| **Fallen Serannian modules, Arkham houses** | Claude script | Parametric kits that snap to the Construction Set grid. Meshy shells don't snap. |
| **The black galley** | Kitbash + Meshy details | Vanilla ship hull lengthened by script; Meshy figurehead, ram and fittings |
| **Creature variants of vanilla** (Ogrim → Gug, scamp → zoog, twilight → night-gaunt) | Claude script | Scale and deform the vanilla mesh |

### 16.3 Worldspaces: what Meshy can and can't do

**Meshy makes objects, not worlds.** In Morrowind, a worldspace is three things:

1. **Terrain:** the landscape heightmap and its texture painting. **Meshy can't help here.** Sculpt it in the Construction Set or OpenMW-CS, or draw heightmaps in an image editor and import them with a heightmap tool (e.g. TESAnnwyn). Claude can script heightmap generation from a sketch.
2. **Statics placed on the terrain:** rocks, trees, ruins, buildings, landmarks. **This is where Meshy helps most.** A region's look comes mostly from a small set of reused statics. About 10–20 good Meshy rocks, cliffs and trees per region (Leng's black stone, Dunwich's domed hills, the Enchanted Wood) go a long way.
3. **Buildings and interiors:**
   - Morrowind's exterior buildings are **closed shells with a load door**; the interior is a separate cell. A Meshy model can serve as a **one-off shell** (the Strange High House, Kadath's gate, a temple in Ulthar), with the door added as a separate object.
   - Interiors and repeated town buildings must **snap to the grid** and join cleanly, so build those with modular kits (vanilla or Claude-scripted), not Meshy.

**Collision is never the Meshy mesh.** Every walkable or solid static gets a simple, hand-made or script-made `RootCollisionNode` (boxes or a convex hull). Generated meshes are too dense and irregular for collision.

### 16.4 Meshy → Morrowind pipeline

```
prompt or image → Meshy (generate, Remesh, texture) → export FBX/GLB → Blender: scale, clean, bake,
collision, rig → io_scene_mw NIF export → NifSkope check → test in game next to vanilla assets
```

1. **Generate.** Text-to-3D, or image-to-3D from concept art you have the rights to: your own drawings, or images from a tool whose terms allow it. Multi-view images give more consistent results. Keep a **shared style suffix** in every prompt (for example *"low-poly, hand-painted texture, muted earthy palette, late-1990s RPG style"*) so assets match each other and Morrowind.
2. **Remesh in Meshy:** **triangle** topology with a **fixed target** close to the budgets in §16.5. Generated models start with far too many polygons and irregular topology.
3. **Texture:** use Meshy's AI texturing, then in Blender:
   - **Bake the base colour** to a single diffuse texture.
   - **Downscale** to 256–1024 px, depending on size.
   - **Paint out baked-in lighting** and push the colours toward Morrowind's palette.
   - Save as DDS (DXT1, or DXT5 with alpha).
   - Optional: keep the normal map as an `_n.dds` for OpenMW's normal mapping. The original engine ignores it.
4. **Clean in Blender:**
   - Scale against a vanilla reference mesh (§16.5).
   - Set the forward axis and put the pivot at the base.
   - Recalculate normals, remove floating fragments, and check the UVs.
   - A Claude-written `bpy` script can batch all of this.
5. **Rig (creatures and parts):**
   - **Don't use Meshy's auto-rig skeleton for creatures.** Morrowind creatures need the vanilla bone names and hierarchy to reuse the vanilla `.kf` animations.
   - Fit the Meshy mesh to the closest vanilla skeleton instead and weight-paint it, with at most 4 bones per vertex:
     - Guar for ghasts
     - Ogrim for gugs
     - Cliff racer for the Shantak
     - Nix-hound for cats and the Hound
     - Kwama forager for dholes
   - Creatures with no matching skeleton (shoggoth, Elder Thing) need new animations. Keep these to idle, move, attack, hit and death, and treat them as the most expensive assets.
6. **Collision:** a simple `RootCollisionNode` (§16.3).
7. **Export** with `io_scene_mw`, check in NifSkope, and test in game **next to vanilla assets**. If it looks out of place, simplify the texture before adding polygons.

**Tooling:** the Pro plan includes API access, so this can be scripted like the voice pipeline (§7):
- A `tools/meshy/` folder with a prompt list, a generation script, and a headless Blender script that does steps 2–7 in batch.
- Keep the API key in an environment variable, **never in git**.
- Download every model you keep into the repo's source-art folder; don't rely on Meshy storing it.

### 16.5 Limits to give Claude and Meshy every time

- **Scale:** about 70 Morrowind units per metre (64 per yard). An exterior cell is 8192 units across. Check the scale and forward axis against a vanilla mesh before batch work.
- **Polygon budgets** (rough guidelines for the old engine; OpenMW handles more):
  - Small props: up to a few hundred triangles.
  - Large props and kit pieces: 1–3k.
  - Buildings and landmarks: a few thousand, with a low-detail distant version for huge ones.
  - Creatures: 1–4k (up to ~6k for bosses).
  - Use these as Meshy's Remesh targets.
- **Textures:** DDS, power-of-two sizes, under `Textures/tdl/`.
- **Collision:** a simplified `RootCollisionNode` mesh for anything the player can walk on or bump into.
- **Creatures:** reuse vanilla skeletons and `.kf` animations. Keep to 4 bone weights per vertex.
- **Naming and pivots:** `tdl_` prefix; pivot at the base for anything placed on the ground.

### 16.6 Licensing

- **Claude:** Anthropic's terms let you use what Claude produces, including scripts and the models they generate.
- **Meshy (Pro):**
  - According to Meshy's pricing and help pages, models made on a paid plan are **private, owned by you, and usable commercially**. This mod isn't commercial, so it is well within that.
  - Conditions:
    - Don't publish the models to the **public Meshy Community**.
    - Upload only material you have the rights to.
    - Models made after a downgrade to the free plan fall under **CC BY 4.0**, which needs credit to Meshy.
  - Re-check Meshy's terms before release.
- **What not to upload to Meshy:**
  - **Bethesda's meshes or textures.** Bethesda's mod rules (§1.1) cover use inside Morrowind mods, not uploading to third-party AI services. Generate new parts and combine them with vanilla assets locally in Blender.
  - **Other modders' assets**, including 4thUnknown's (see [CREATURES.md](CREATURES.md)), without their permission.
  - **Call of Cthulhu RPG art** or any other copyrighted art used as an image prompt (§11.1).
  - **Images of real people** for NPC heads.
- **Meshes derived from Bethesda's** (vanilla kitbashes, including Meshy parts attached to vanilla bodies) stay under Bethesda's mod rules: Morrowind mods only.
- **Records:** log every Meshy model in `CREDITS.md` with its prompt or source image, the plan and the date.
- **Disclosure:** tag Meshy-generated models and textures as AI-generated on the Nexus page, alongside the voice disclosure (§8).

---

*"We live on a placid island of ignorance in the midst of black seas of infinity, and it was not meant that we should voyage far."* Then again, Carter did voyage. Good luck in the Dreamlands.
