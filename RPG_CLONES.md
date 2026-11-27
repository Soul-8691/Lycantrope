# RPG Clone Risks — Fable and RuneScape

This document reviews the approved ideas against two games that are outside Lycantrope's stated inspirations: **Fable** (specifically Fable 1, 2003) and **RuneScape** (specifically the 2000s era that most players remember). Neither game is on the inspiration list (OoT / MM / TP / MW / OB / SK / DS1–3), and both are well-known enough that players will name them on first association.

The goal is not to sanitize everything that overlaps — most RPG features overlap with something. The goal is to identify combinations and framings that would make a player say *"this is basically Fable"* or *"this is 3D RuneScape"* on first impression, and to propose specific wording or design changes that make the same features feel like they come from the right places.

---

## 1. Fable

### 1.1 The story structure is Fable 1's story structure

**Ideas involved:** PIL-09, STY-13, STY-14, STY-20, STY-21, HER-09, STY-15

Fable 1 opens on a peaceful rural English village. A young protagonist does a small errand for a family elder. Bandits raid the village. The protagonist grabs a weapon and flees. A wise mentor takes them in and trains them. The sword the protagonist carries grows more powerful with them. The mentor falls mid-game. A dark, ancient power is behind everything. The hero is a "nobody" who becomes "a legend" (Fable's literal tagline).

Lycantrope's current structure hits every beat:
- STY-21: morning chore on the farm, then goblins raid the village, Rowan grabs the sword off the hearth
- STY-14: prologue, the village burns, mentor Aldric finds Rowan
- STY-20 / NPC-04: Farmer Oswin, the gruff guardian
- PIL-09: "From nobody to legend"
- STY-15: Aldric, the wise mentor who falls mid-game
- STY-13: the Dark Lord's return as the driving threat

None of these is fatal alone. Combined, they are a plot-beat-for-plot-beat retelling of Fable's first act.

**Remedy — the structure:**

The core fix is making Aldmoor feel *already lost* before Rowan gets involved, rather than making Rowan's village its own peaceful starting point that the raid destroys. Dark Souls opens in an asylum after the world has been failing for centuries. Ocarina opens at the edge of a forest that is slowly dying. Neither begins with a peaceful village getting raided. The village raid is where it *ends* for most people — the reason Rowan is the last one left trying.

Specific changes worth considering:

- **STY-21 (cold open):** Instead of a quiet morning chore, Brackenvale should already be under strain when the game opens — a feed shortage, a missing farmer, a Watch captain who hasn't slept. Rowan is not at ease; Rowan is already trying to help and already failing. The goblins arrive as a confirmation of something everyone feared, not as a shock from nowhere.
- **STY-14 / HER-09:** The sword being "grabbed off the hearth in the chaos" is Fable's origin beat. Consider: the sword has been with Rowan all along, ignored and dull, carried because it was grandfather's and not because it mattered. It wakes not in the moment of crisis but in the moment Rowan decides not to run — a quieter, less theatrical origin.
- **PIL-09 ("From nobody to legend"):** The framing should shift from personal growth to world survival. Rowan doesn't become a legend; Rowan is the one person who was still there when everyone smarter had already left. The arc is less "rise of a hero" and more "last person standing."
- **STY-15 (Aldric, the mentor who falls):** His falling should not be protecting Rowan in a sacrificial way — that's Obi-Wan, yes, but also Maze, and Fable made it famous. Aldric falling while Rowan is elsewhere, holding a ward that nobody knew about, is more interesting and less expected.

---

### 1.2 The village social fabric reads as Oakvale

**Ideas involved:** NPC-04 through NPC-14, NPC-02, NPC-03

Eight named quirky villagers with small personal worries, each with a rumour that seeds a local quest. A gruff farmer. A dairymaid who's known Rowan since childhood. A gossip seller. Guards who grumble about their rounds. This is Oakvale: a cozy, slightly comedic English village where the NPCs are archetypes with mild concerns.

The issue is not that the NPCs exist — Oblivion and Skyrim have named NPCs — but the **tone** of the lines written so far. "Ha! Mind the anvil, it bites." (Tam, NPC-07). "Come here, dearie. Lavender for sleep? Everyone's buying it this month." (Granny Maud, NPC-09). These are warm, whimsical, comedic lines. They would fit Fable perfectly. They don't fit a world where the Dark Lord's armies are spreading and the coast road has gone quiet.

**Remedy:**

The NPCs should feel like people who have been afraid for a long time and are keeping it together by not talking about it. Their small talk should contain dread just below the surface. Compare:

> *Current (Fable tone):* "Come here, dearie. Lavender for sleep? Everyone's buying it this month."

> *Revised (Aldmoor tone):* "Lavender. Yes. Take some — I've more than I need. Everyone in the village is buying it this month and nobody's saying why."

The difference is a single trailing phrase that doesn't explain itself. That's Morrowind's texture — not comedic quaintness, but the specific unease of people who know something is wrong and have decided not to name it. The "wrong note" quality called out in NPC-01 (*"small wrong notes that point ahead"*) needs to be the dominant texture of these lines, not the exception.

Also worth checking: **NPC-03** (NPCs notice what Rowan does) is fine as written — Oblivion and Skyrim both do this. It only becomes Fable if it feeds a good/evil appearance-change system, which is not in the tracker.

---

### 1.3 Use-based skill growth alongside a "nobody to legend" arc

**Ideas involved:** STA-06, STA-07, STA-08, PIL-09

STA-06 (skills improve by use) is in Morrowind and Skyrim, so it's not inherently Fable. But Fable's specific implementation — Strength grows from physical attacks, Will grows from magic, Skill grows from ranged — maps closely to Lycantrope's combat skills (Blade, Blunt, Polearm, Marksman, Guard, Evasion, Rites). And PIL-09's "from nobody to legend" framing puts this skill growth in the same context as Fable: a farmhand who becomes great through practice and bravery.

The fix is partly in the framing (see §1.1) and partly in making the skill names and their descriptions clearly combat-technical rather than life-path-y. The existing names (Blade, Blunt, Guard, Evasion) are good — they read like Dark Souls weapon categories. Keep them that way.

The bigger risk is STA-08 (perks every 10 skill levels). "Choose one of two perks" is Skyrim's perk tree system, but the milestone framing is also how Fable's physical/will/skill upgrades worked. Keep the focus on **combat performance choices** (longer i-frames *or* cheaper rolls) and avoid anything that sounds like a life path (a Strength perk that makes you "look more imposing to villagers" would be pure Fable).

---

### 1.4 The Dawnblade growing with each boss kill

**Ideas involved:** HER-10, ART-17, VAL-05

The sword that grows more powerful and visually changes as the hero completes major story beats is Fable's Sword of Aeons / hero's sword in everything Fable. It's also Ocarina's Master Sword and plenty of JRPG legendaries, so it's not unique to Fable. The safe version is **mechanical growth tied to the world's story** (each Crown Shard restores a part of a broken seal) rather than **personal growth tied to the hero's choices** (the sword reflects your alignment). The current design (HER-10, VAL-05) is on the right side of this — it's about restoring an artifact, not about Rowan becoming more heroic. Keep the emphasis on "the weapon is being healed" rather than "the hero is becoming worthy of it."

---

## 2. RuneScape

### 2.1 "Rune sockets" is the name of a RuneScape mechanic

**Ideas involved:** CMB-25

This is the most direct and easily fixed problem in the whole document. In RuneScape, "Rune" is a gear tier — Rune armour, Rune weapons — and the game's identity is built around runes as currency and magic. "Rune sockets" in a fantasy action RPG will be read as RuneScape immediately.

The mechanic itself (socket found items into weapons for elemental effects) is fine — it's in Morrowind's enchanting and Diablo. The name is the problem.

**Remedy:** Rename to something that fits Aldmoor's texture: **sigil slots**, **ward engravings**, **crest sockets**, or **binding stones**. Pick one and use it everywhere.

---

### 2.2 Use-based skill growth as a grind loop

**Ideas involved:** STA-06, STA-07, STA-08

The same mechanic flagged for Fable reads as RuneScape for a different reason. RS's entire identity is skills that go from 1 to 99 by doing the thing — woodcutting levels by cutting wood, fishing levels by fishing. STA-06 makes combat skills improve by use, which is Morrowind and Skyrim, but the question is what the **player experience** feels like. If a player fights 50 goblins to grind Blade from 40 to 50, that's RuneScape. If a player fights 50 goblins because they're trying to get through the Wolfwood and the skill goes up as a byproduct, that's Morrowind.

The fix is behavioral, not structural: skill gains should be **invisible while they're happening** and **noticeable only at milestones**. No XP bars for skills. No "Blade increased to 41." Just an occasional milestone notification when a perk becomes available. This is how Skyrim handles it and it avoids the grind feeling.

---

### 2.3 The fishing pond minigame

**Ideas involved:** WLD-22

WLD-22 is already marked "a later stretch goal," but its current description — "a relaxing fishing minigame at a lake hut" — is essentially a screenshot caption from RuneScape circa 2004. If it makes it into the game, it needs a reason to exist in Aldmoor beyond "relaxation." A fishing spot that provides an item for a quest, or that unlocks a shortcut, or that is haunted — that's Ocarina. A skill you level up by fishing is RuneScape.

**Remedy:** If WLD-22 is built, make it a one-time narrative interaction (Rowan fishes to get a specific item, like a key or a reagent) rather than a repeatable skill activity. The hut itself can be atmospheric — a ferryman's hut, an old hermit — without needing a mini-game loop.

---

### 2.4 Ore-based weapon upgrades at a smithing station

**Ideas involved:** CMB-24

CMB-24 is currently "weapon upgrades at Waystones using ore found in the world." The note on the entry says "Ore yes, but smithing NPC should be needed." The mechanic is fine — Dark Souls uses upgrade materials at bonfires and smiths. The RuneScape smell comes from the word "ore" and from any framing that makes the upgrade feel like a crafting process. Smelting ore → making a sword tier is RS's smithing skill.

**Remedy:** Frame it as **restoration** rather than crafting. You're not making a better sword; you're recovering the edge it once had. The material is "brightstone" or "void-iron" or some specific named substance, not generic "ore." The smith NPC (Gerda Vane, found through NPC-07) should feel like a craftsperson from the world, not a crafting station. The UI should show a weapon being cleaned and repaired, not assembled.

---

### 2.5 Faith as a named stat

**Ideas involved:** STA-20

"Faith" as a magic stat is shared with both RuneScape's Prayer skill and Dark Souls' Faith attribute. DS is on the inspiration list, so this is defensible. But DS's Faith is about miracles tied to a covenant/religion system; RS's Prayer is a more literal "pray at an altar for stat bonuses." Make sure Faith in Lycantrope reads clearly as the DS version: an attribute tied to Rowan's connection to the Dawnblade's light and the Rites, not to prayer mechanics or altar visits.

---

## 3. What is fine

The following ideas are similar to Fable or RuneScape in some surface way but actually come from the stated inspirations and should not be changed:

- **WLD-09 Waystones** — read as DS bonfires; the respawn-and-rest mechanic is DS.
- **CMB-22 Lifewater flask** — read as DS Estus; not a Fable potion.
- **CMB-18 Damage types** — elemental resistances are in Morrowind, not RS specifically.
- **CMB-19 Status buildup** — DS poison/bleed, not RS poison.
- **STA-11 Heart shards** — Ocarina's Pieces of Heart.
- **CMB-44 Food heals slowly** — Skyrim and Oblivion; RS food heals instantly and in bulk.
- **STA-01/STA-05 XP and soft caps** — DS's leveling curve.
- **NPC-03 NPCs notice Rowan** — Oblivion and Skyrim; fine as long as it doesn't extend to appearance changes.
- **BOS-14 Not every boss is a kill** — Majora's Mask and DS.

---

## 4. The combined risk

The individual items above are mostly fixable with renames and tonal adjustments. The larger risk is gestalt: a player who boots the game and sees a cheerful British village, a farmhand protagonist grabbing their grandfather's sword during a raid, a "skills improve by use" progression system, ore-based weapon upgrades, a fishing spot, and "rune sockets" will not think of Dark Souls and Ocarina of Time. They will think of Fable with a fishing pond in a game called Lycantrope.

The two interventions that would do the most work:

1. **Make Brackenvale feel like a world in late-stage decline, not a cozy starting village.** The villagers should be rationing. The watch should be understaffed. The gossip should be grim. The road to the nearest city should have been quiet for three months. This costs nothing in code — it's a pass over the NPC dialogue lines — but it changes what the game is about from the first screen.

2. **Rename everything that uses "rune."** It's one word. CMB-25 Rune sockets → sigil slots, done.

The Dark Souls inspiration is already strong in the combat design, the equip load, the status buildup, the fall damage, the poise system and the loot. The gap is that the town and the story don't feel like they come from the same game as the combat. If the village was as stark and lived-in as Firelink Shrine, the Fable comparison would stop immediately.
