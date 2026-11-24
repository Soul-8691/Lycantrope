# LYCANTROPE — Ideas

> *Silver for the beast. Fang for the wicked. Both, for whatever wears a crown.*

**Lycantrope** is a free, open-source (MIT) 3D action-adventure fantasy RPG built with **Python + pygame(-ce) + moderngl**. The main focus is combat. You play one fixed hero: a monster hunter who has been bitten and can now become the monster.

**Inspirations (only these nine):** *Ocarina of Time* (OoT), *Majora's Mask* (MM), *Twilight Princess* (TP), *Morrowind* (MW), *Oblivion* (OB), *Skyrim* (SK), *Dark Souls* 1–3 (DS1/DS2/DS3, or DS for the whole series). Ideas tagged **DOC** are programming and pipeline ideas adapted from `DREAM-QUEST.md` and `THE_DREAMLANDS.md`, with nothing Lovecraftian and nothing exclusive to Morrowind. Ideas tagged **NEW** are original.

---

## How this file works with the Idea Tracker

- Each idea is one bullet that starts with an **ID** in brackets: `- [CMB-04] **Title** — description *(sources)*`.
- **IDs never change.** New ideas take the next free number in their category. Deleted ideas keep their old ID, which is never reused.
- ⭐ = recommended for the **First Playable** milestone (see ROADMAP.md).
- Run the tracker with `run_idea_tracker.bat` or `python tools/idea_tracker.py`. It watches this file, so new ideas show up while it is open.
- Decisions are saved to `ideas_status.json`, the source of truth that Claude reads. `IDEAS_STATUS.md` is a readable summary generated from it. When you want to refer to an idea, just use its ID ("deny WLF-06", "what did I approve in Combat?").

---

## 1. Pillars (PIL)

- [PIL-01] **Combat first** — Every system feeds the fight. Exploration exists to find new enemies, new gear and XP. If a feature doesn't make combat deeper or more varied, it waits. ⭐ *(NEW)*
- [PIL-02] **Deliberate, readable, fair** — Enemies show clear wind-ups, the player commits to attack animations, and every death teaches you something. Difficulty comes from timing, not from huge HP pools. ⭐ *(DS, DOC)*
- [PIL-03] **Two bodies, one hero** — The human form is precise (steel, silver, parries). The beast form is overwhelming (claws, leaps, feeding). Switching between them at the right moment is the game's signature skill. ⭐ *(TP, SK)*
- [PIL-04] **See it, go there** — An open world built around landmarks you can see from far away. The Eclipse Spire, mountains and ruins pull you toward them. ⭐ *(OoT, SK)*
- [PIL-05] **Generated, not hand-made** — Models come from Meshy, voices and SFX from ElevenLabs, and terrain, textures, sky, VFX and kits from Python scripts. Hand work only fixes things; it doesn't create them. ⭐ *(DOC)*
- [PIL-06] **Tropes played straight, with a wink** — Familiar fantasy (prophecy, dark lord, cursed hero, elemental dungeons) done sincerely. The title's pun is the only wink. ⭐ *(NEW)*
- [PIL-07] **Ship small, ship often** — Every week ends with a playable build. Content is data, so new enemies and items don't need new code. ⭐ *(DOC)*

## 2. Story & Setting (STY)

- [STY-01] **Premise: the Chained Moon** — Long ago the Silver Wardens bound the soul of Lycaon, the First Wolf, inside the Moon. Each Blood Moon weakens the chain. A cult, the Eclipse Choir, is breaking the four Moon Seals to free him. ⭐ *(NEW)*
- [STY-02] **The realm of Aldmoor** — A fading kingdom of mossy ruins, abandoned watchtowers and wild country, where the monsters outnumber the people. The empty world is part of the story, and it's why there are no NPCs at first. ⭐ *(NEW)*
- [STY-03] **Four Moon Seals, four dungeons** — Wolfwood (Thorn), Blackmire (Tide), Frostfang Peaks (Frost) and Ashen Reach (Ember). Each is guarded by a boss and a cult lieutenant. This is the classic structure of dungeon → item → boss. *(OoT, TP)*
- [STY-04] **The term "Lycantrope"** — In-world, a *lycanthrope* is a slave to the moon. A *Lycantrope* is the rare one who turns *at will*. The Wardens call it heresy. The cult calls it a prophecy. *(NEW)*
- [STY-05] **Prologue: the hunt gone wrong** — A short tutorial. Rowan and the Wardens hunt a werewolf, the hunt fails, Rowan is bitten, and the first transformation happens against Rowan's will. ⭐ *(TP, SK)*
- [STY-06] **The Hunger: a voice in the bite** — The curse talks. It's a sardonic, ancient voice in Rowan's head that gives hints, taunts and comments on kills. It's a companion who can't be killed and works as a built-in hint system. *(TP, OoT)*
- [STY-07] **The Wardens hunt you** — Rowan's old order wants Rowan dead. Silver-armored knights show up as enemies, and Rowan's former mentor is a recurring duel boss. *(NEW)*
- [STY-08] **Two endings** — At the Spire, either chain Lycaon again by taking his place in the Moon, or devour him and become the new Wolf-King. *(DS1, SK)*
- [STY-09] **Story told through items and places** — Item descriptions, ruined camps, corpses and scattered journals tell most of the story. Only a few lines are voiced. ⭐ *(DS, MW)*
- [STY-10] **Readable lore books and notes** — Short in-world texts (Warden field manuals, cult hymns, bandit letters) found in the world. They're generated from templates and edited by hand. *(MW, OB, SK)*
- [STY-11] **Blood Moon nights** — Every few in-game nights there's a Blood Moon: stronger enemy variants, a red sky, more XP, and a risk of uncontrolled transformation (WLF-06). *(MM, NEW)*
- [STY-12] **Cult lieutenants with names and barks** — Each Seal has a named cultist who taunts you across the dungeon with voiced lines, then fights next to the boss. *(OoT, TP)*

## 3. The Hero (HER)

- [HER-01] **Rowan Fenhallow, the Moonbitten** — A disgraced Silver Warden. Look: weathered leather brigandine, a grey wolf-pelt mantle, a braid threaded with silver rings, a scar across the nose, and **one amber eye** since the bite. Gear: a hooked silver-edged longsword, a small round buckler and a hand crossbow. ⭐ *(NEW)*
- [HER-02] **Rowan is a woman** — Voice direction: low, weathered, dry humor, early 30s. Pick this **or** HER-03. ⭐ *(NEW)*
- [HER-03] **Rowan is a man** — Voice direction: gravelly, tired, dry humor, mid 30s. Pick this **or** HER-02. ⭐ *(NEW)*
- [HER-04] **The bite scar glows** — The bitten forearm shows the Bloodlust meter on the model itself: faint at 0, amber veins at 50%, burning at 100%. You can read Rowan's state without looking at the HUD. ⭐ *(NEW)*
- [HER-05] **A few memorable lines** — Short voiced reactions: on level up, low HP, a boss kill, entering a new biome, and refusing the Hunger. About 40 lines in total, and few enough that each one gets noticed. ⭐ *(SK, TP)*
- [HER-06] **The beast is still Rowan** — The werewolf form keeps the scar, the braid with its silver rings, and the amber eye. Players recognize it as the same person at a glance. ⭐ *(TP)*
- [HER-07] **Visible armor swaps** — Armor pieces swap meshes on the model (head, chest, arms, legs). This comes later, after the First Playable. *(SK, DS)*
- [HER-08] **Signature idle animations** — Rowan tests the sword edge, flexes the bitten hand, and glances at the moon at night. *(TP, NEW)*

## 4. Combat (CMB)

- [CMB-01] **Third-person orbit camera** — A free-orbit camera that collides with terrain, with an over-the-shoulder aim mode for the crossbow. ⭐ *(OoT, TP, DS)*
- [CMB-02] **Lock-on targeting** — Lock onto an enemy with a button. Flick the stick or mouse to switch targets. While locked, Rowan strafes around the target. ⭐ *(OoT, DS)*
- [CMB-03] **Stamina** — Attacks, dodges, blocks and sprinting all cost stamina. It regenerates fast but stops while you're blocking. ⭐ *(DS)*
- [CMB-04] **Light and heavy combo strings** — Each weapon class has a light chain (3–4 hits) and a heavy chain (2 hits), defined entirely in frame-data JSON. ⭐ *(DS, SK)*
- [CMB-05] **Directional power attacks** — Holding heavy plus a direction gives different moves: forward is a lunge, backward is a sweep, sideways is a cleave. *(SK)*
- [CMB-06] **Dodge roll with i-frames** — Rolling makes you briefly invulnerable. Equip load decides the roll type (fast, medium or fat). ⭐ *(DS)*
- [CMB-07] **Block and guard break** — The buckler blocks. Blocked hits drain stamina based on shield stability. If stamina runs out, Rowan is guard-broken and open. ⭐ *(DS, OB)*
- [CMB-08] **Parry → riposte** — A tight parry window during the enemy's active frames, followed by a heavy critical riposte with hitstop and a close-up. ⭐ *(DS)*
- [CMB-09] **Backstabs and sneak attacks** — Crouch to sneak. A critical hit from behind does ×2.5 damage (×4 on an unaware enemy). Light and noise affect detection. *(DS, SK, OB)*
- [CMB-10] **Poise and stagger** — Both sides have poise. Heavy hits break it and stagger the target. Armor adds poise, and bosses have a large poise bar. ⭐ *(DS)*
- [CMB-11] **Charged spin attack** — Hold light to charge a 360° spin that hits every enemy around you. Costs a lot of stamina. *(OoT, TP)*
- [CMB-12] **Hidden techniques** — Moves found on technique scrolls in the world: shield bash, back-slice, helm-splitter, finishing stab on a downed enemy, jump strike. *(TP)*
- [CMB-13] **Jump strike and plunge attack** — A leaping overhead strike while locked on, and a plunge when you drop onto an enemy from a ledge. *(OoT, DS)*
- [CMB-14] **Hit feel** — Hitstop (50–90 ms), camera shake, a small FOV punch, sparks and impact sounds that vary by material. This matters more than anything else in this file. ⭐ *(DOC)*
- [CMB-15] **Input buffering** — Attack, dodge and parry presses are buffered for about 150 ms so combos feel responsive. ⭐ *(DOC)*
- [CMB-16] **Frame data as JSON** — Every attack lists its wind-up, active and recovery frames, the hitbox shape and path, damage, poise damage, stamina cost, cancel windows and the parryable flag. Easy to tune and to test. ⭐ *(DOC)*
- [CMB-17] **Swept-capsule hitboxes** — The weapon's hitbox is swept between frames so fast swings don't pass through enemies. Each actor has capsule hurtboxes. ⭐ *(DOC)*
- [CMB-18] **Damage types and resistances** — Slash, strike, pierce, fire, frost and **silver**. Each enemy has resistance values (skeletons resist slash, trolls fear fire, wraiths fear silver). ⭐ *(DS, MW, SK)*
- [CMB-19] **Status buildup** — Bleed, poison, burn, frost (slow) and stun build up as meters and trigger when full. *(DS)*
- [CMB-20] **Hand crossbow** — Quick shots from the hip or aimed over the shoulder. Bolt types: iron, silver, fire. It's used to knock fliers down and to interrupt casters. ⭐ *(OoT, TP)*
- [CMB-21] **Throwables** — Firebombs, silver dust (reveals and weakens), and smoke (drops aggro). *(DS, OoT)*
- [CMB-22] **Moonwater flask** — A healing flask with a few charges, refilled when you rest at a Moonwell. You can find upgrades for more charges and stronger healing. ⭐ *(DS)*
- [CMB-23] **Weapon classes** — Longsword (Rowan's default), axe, mace, spear and greatsword. Each class has its own moveset and stat scaling. *(DS, SK)*
- [CMB-24] **Weapon upgrades at Moonwells** — +1 to +10 using ore found in the world. No smith NPC is needed. *(DS)*
- [CMB-25] **Rune sockets** — Socket found runes into weapons for elemental damage or effects on hit. *(SK, MW, OB)*
- [CMB-26] **Equip load tiers** — Under 30% is a fast roll, under 70% a medium roll, and more than that a slow roll. Heavy armor is a real trade-off. *(DS)*
- [CMB-27] **Attack tokens** — Groups share a limited pool of "attack tokens", so only one or two enemies attack at the same time and fights stay readable. ⭐ *(NEW)*
- [CMB-28] **Difficulty through reaction time** — Higher-level and elite enemies react faster, parry and dodge more often, and follow up more. Their HP grows only moderately. ⭐ *(DOC)*
- [CMB-29] **Moon Rites (small spell set)** — Three or four spells: *Silver Flash* (parries at range), *Moonward* (a short barrier), *Lunar Mark* (makes a target take more damage). They cost focus. *(SK, OB, DS)*
- [CMB-30] **Essence drop on death** — When you die, you drop all unspent XP where you fell. Get back there without dying again to recover it. *(DS)*
- [CMB-31] **Kicks and environment kills** — Kick to break a guard or knock an enemy off a ledge. Explosive barrels, spike traps and falling rocks hurt enemies too. *(DS, OoT)*
- [CMB-32] **Mounted combat on a dire wolf** — A later stretch goal: ride a dire wolf across the open world and fight from its back. *(TP, OoT)*

## 5. Beast Form (WLF)

- [WLF-01] **Bloodlust meter** — Fills when you deal or take damage and slowly drains out of combat. When it's full, a button transforms Rowan. ⭐ *(SK, TP)*
- [WLF-02] **Beast moveset** — Fast claw strings, a leaping pounce, a grab-and-throw, and a ground slam. The beast can't block or drink flasks and doesn't use the crossbow, but it has a dodge-leap. ⭐ *(SK)*
- [WLF-03] **Feeding** — Devour a staggered or dead enemy to heal and extend the transformation. Feeding takes time and leaves you open. ⭐ *(SK)*
- [WLF-04] **Scent senses** — A toggle that greys out the world and highlights enemies (through walls), blood trails, buried loot and weak points. *(TP)*
- [WLF-05] **Moon phases** — An 8-phase moon cycle tied to in-game days. At the full moon the beast is stronger and lasts longer. At the new moon it can't transform. *(MM, NEW)*
- [WLF-06] **Losing control** — If the meter overflows during a Blood Moon, you lose control for a few seconds. The beast attacks the nearest thing, and you can steer but not stop it. *(NEW)*
- [WLF-07] **Instinct prompts** — In beast form, urges flash on screen ("HUNT", "FEED", "FLEE THE SILVER"). Obey within 2 s for a short buff, or ignore for a small amount of Bloodlust. *(DOC)*
- [WLF-08] **Silver hurts** — In beast form, silver weapons (Warden knights) deal +50% damage to you. It's the counterweight to the beast's power. ⭐ *(NEW)*
- [WLF-09] **Beast perk tree** — Perks unlocked through the Savagery skill: longer transformation, stronger feeding, a howl that terrifies weaker enemies. *(SK)*
- [WLF-10] **Howls** — Short-range cone powers with long cooldowns: *Fear* (weak enemies flee), *Call of the Pack* (summon two spectral wolves), *Shatter* (stagger nearby enemies). *(SK)*
- [WLF-11] **Wolves are kin** — Ordinary wolves don't attack you in beast form, and they may follow you for a while. *(TP, NEW)*
- [WLF-12] **Trophy masks** — Wearing a boss's skull trophy lends a trait to your beast form (the Brood Queen's skull adds web spit). *(MM)*
- [WLF-13] **Its own camera** — The beast camera sits lower with a wider FOV, adds speed lines when sprinting, and has a heavier footfall shake. ⭐ *(DOC)*
- [WLF-14] **Climb and dig** — The beast can scramble up rough cliff faces and dig at marked spots to find hidden passages and loot. *(TP)*

## 6. Stats, Skills & Leveling (STA)

- [STA-01] **XP from kills** — XP depends on enemy level and the level difference between you (0.25× to 2×). The curve: `xp_to_next(L) = 100 · L^1.5`. ⭐ *(SK, DS)*
- [STA-02] **Level up anywhere** — Once you have enough XP, open the level-up screen any time you're out of combat. No NPC. Choose this **or** STA-03. ⭐ *(SK, NEW)*
- [STA-03] **Level up only at Moonwells** — Spend XP while resting at a Moonwell. It's riskier and more like Dark Souls. Choose this **or** STA-02. *(DS)*
- [STA-04] **Six attributes** — **Might** (heavy weapons, beast damage), **Finesse** (swords, crossbow, crits), **Vigor** (HP), **Endurance** (stamina, equip load), **Spirit** (Bloodlust gain, Moon Rites, transformation time), **Fortune** (crit chance, loot). Each level gives +1 point. ⭐ *(DS, MW, OB)*
- [STA-05] **Derived stats with soft caps** — HP, stamina, equip load, poise and crit chance come from the attributes through curves that slow down past 20 and again past 40. ⭐ *(DS)*
- [STA-06] **Skills improve by use** — Blade, Blunt, Polearm, Marksman, Guard, Evasion, Savagery and Rites, each from 1 to 100. Landing hits, blocking, dodging well and kills in beast form all raise them. ⭐ *(MW, OB, SK)*
- [STA-07] **Hybrid progression** — Your character level (from XP) gives attribute points. Skill levels (from use) give percentage bonuses and perks. Both matter. ⭐ *(SK, DS)*
- [STA-08] **Perks every 10 skill levels** — Choose one of two perks at each milestone. For example, Evasion 30: *longer i-frames* or *roll costs 25% less stamina*. *(SK)*
- [STA-09] **Weapon scaling grades** — Weapons show S/A/B/C/D/E scaling with Might and Finesse, and an upgraded weapon's grades rise. *(DS)*
- [STA-10] **Fixed-level regions** — Each region has a fixed level range (the Vale is 1–5, the Peaks 12–18). The world does **not** scale to the player, so going back to an early area makes you feel powerful. ⭐ *(DS, MW)*
- [STA-11] **Heart shards** — Hidden collectibles. Every 4 shards give +10% max HP permanently, and stamina shards work the same way. They reward exploration outside the leveling system. ⭐ *(OoT, TP)*
- [STA-12] **Respec item** — The rare *Moonless Tear* lets you redistribute all attribute points once. *(DS)*
- [STA-13] **Optional damage numbers** — Floating damage numbers, off by default, with a setting to turn them on. *(NEW)*
- [STA-14] **Stat gates** — A few heavy doors and gaps need Might or Finesse 15+ (or the beast form), which gives builds a role in exploration. *(MW, DS)*

## 7. Enemies (ENM)

*Each enemy is one of about 10 behavior **archetypes** with its own tuning, model and voice, which keeps 20 enemies achievable. Lv = base level, and Blood Moon variants get +3.*

- [ENM-01] **Giant Rat** — Lv 1 · Vale, Crypts · Packs of 3–6, lunging bites, very weak alone. Teaches lock-on. *Voice: squeaks and hisses (SFX).* ⭐ *(OoT, MW, SK)*
- [ENM-02] **Grey Wolf** — Lv 2 · Wolfwood, Vale · Packs circle you and lunge from behind. The alpha howls to send the pack in. *Voice: growls and howls (SFX).* ⭐ *(TP, SK)*
- [ENM-03] **Goblin Cutthroat** — Lv 2 · Vale, Ashen · Fast, cowardly, runs away at low HP to fetch friends. Dagger feints. *Voice: shrill cackles, "Shiny! Mine!"* ⭐ *(SK, OB)*
- [ENM-04] **Bandit Brigand** — Lv 3 · Vale, roads · Sword and shield. Blocks, then counters. *Voice: gruff taunts ("Nice coat. I'll take it.").* ⭐ *(SK, OB, DS)*
- [ENM-05] **Bog Ooze** — Lv 3 · Blackmire · Splits into two smaller oozes when cut. Fire burns it whole. *Voice: wet gurgles (SFX).* ⭐ *(OoT, TP)*
- [ENM-06] **Bandit Crossbowman** — Lv 4 · Vale, ruins · Keeps its distance, backs away, and reloads behind cover. *Voice: "Hold still!", "Reloading!"* ⭐ *(SK, DS)*
- [ENM-07] **Goblin Hexer** — Lv 4 · Vale, Ashen · Buffs nearby goblins and throws firebolts. Kill it first. *Voice: chanting gibberish.* ⭐ *(SK, OB)*
- [ENM-08] **Skeleton Warrior** — Lv 5 · Crypts, ruins · Pulls itself back together after a few seconds unless it's finished with blunt or silver damage, or stomped. *Voice: bone rattles and a hollow moan.* ⭐ *(OoT, DS1, SK)*
- [ENM-09] **Giant Spider** — Lv 5 · Wolfwood · Drops from the canopy to ambush and spits webs that slow you. *Voice: chittering (SFX).* ⭐ *(SK, OoT, DS1)*
- [ENM-10] **Drowned Thrall** — Lv 6 · Blackmire · A zombie that rises out of the water, grabs and bites. Slow, but in groups. *Voice: drowned groans.* ⭐ *(SK, DS)*
- [ENM-11] **Harpy** — Lv 7 · Frostfang cliffs · Dive-bombs and shrieks to stun. Shoot it down with the crossbow. *Voice: shrieking cackles and mocking lines.* ⭐ *(NEW)*
- [ENM-12] **Lizardfolk Spearman** — Lv 7 · Blackmire · Long reach and thrust combos. Dives into water to get around you. *Voice: hissed words.* ⭐ *(OoT, OB)*
- [ENM-13] **Orc Berserker** — Lv 8 · Ashen, roads · Fights with two axes and enrages at low HP (glowing red, faster, but stops defending). *Voice: war cries.* ⭐ *(SK, OB)*
- [ENM-14] **Bog Troll** — Lv 10 · Blackmire · Regenerates unless hit by fire or silver. Wide sweeping attacks. *Voice: grunts and a few dim words.* ⭐ *(SK, MW, OB)*
- [ENM-15] **Wraith** — Lv 11 · Crypts, night · Goes intangible between attacks. Only silver or Rites hit it while it's faded. *Voice: layered whispers.* ⭐ *(TP, SK)*
- [ENM-16] **Frost Yeti** — Lv 12 · Frostfang · Throws boulders, grabs, and beats its chest before charging. *Voice: roars (SFX).* ⭐ *(SK)*
- [ENM-17] **Ogre Brute** — Lv 13 · Frostfang, Ashen · Huge club, ground-pound shockwave, grab-and-throw. *Voice: slow and dim ("SMASH… little… wolf.").* ⭐ *(OB, DS)*
- [ENM-18] **Rogue Werewolf** — Lv 14 · Wolfwood (night) · A mirror of your beast form: leaps, fast strings, and howls to call wolves. *Voice: snarls and broken speech.* ⭐ *(SK, TP)*
- [ENM-19] **Silver Warden Knight** — Lv 15 · Anywhere (hunts you) · Parries, ripostes, carries a shield, and fights with **silver** weapons (bonus damage against the beast). *Voice: formal and zealous ("By silver and oath!").* ⭐ *(DS, NEW)*
- [ENM-20] **Runestone Golem** — Lv 16 · Ashen, ruins · Slow and heavily armored. Break its glowing rune weak points first. Immune to bleed. *Voice: grinding stone (SFX).* ⭐ *(TP, OoT, DS)*
- [ENM-21] **Mimic Chest** — Optional · Anywhere · A chest that bites. Tell it apart by the chain that faces the wrong way. *(DS)*
- [ENM-22] **Necromancer** — Optional · Crypts · Raises skeletons, teleports, and stays out of melee range. *Voice: arrogant monologues.* *(SK, OB)*
- [ENM-23] **Elite variants** — Any enemy can spawn as an **Elite** with a tint, +2 levels, one extra trait (fast, armored, vampiric) and double XP. *(SK, DS)*
- [ENM-24] **Behavior archetypes** — melee-basic, pack-circler, ranged-kiter, caster-support, flyer, ambusher, brute, regenerator, phaser and armored-weakpoint. A new enemy is just an archetype plus a JSON file. ⭐ *(DOC)*
- [ENM-25] **Telegraph language** — Every enemy uses the same cues: a white glint means you can parry, a red flare means you can't parry so dodge, and a deep sound means a grab. ⭐ *(DS, NEW)*

## 8. Bosses (BOS)

- [BOS-01] **Grimtooth, Alpha of the Wolfwood** — A giant werewolf. Phase 1 is a duel. In phase 2 he howls in wolves and leaps between trees. He reuses the werewolf rig and animations, so he's cheap to build. **Recommended first boss.** ⭐ *(TP, SK)*
- [BOS-02] **The Brood Queen** — A massive spider in a web cathedral. She climbs walls and ceiling, spawns spiderlings and webs the arena, and her weak point is exposed while she's stuck in a web. *(OoT, DS1)*
- [BOS-03] **Old Mother Mire** — A bog hag riding a troll. Kill the troll's regeneration with fire, then fight the hag on foot as she teleports through swamp pools. *(OoT, SK)*
- [BOS-04] **The Frostfang Wyvern** — Fought on a cliff. Shoot its wings with the crossbow to ground it, then fight it on the ground with tail sweeps and frost breath. *(SK, DS)*
- [BOS-05] **The Cinder Colossus** — A giant golem in a magma forge. Climb its arm while it's stunned to break the rune core. *(OoT, TP)*
- [BOS-06] **Inquisitor Maren Ashby** — Rowan's former mentor. A human duel, very technical: parries, silver blades, Moon Rites. She returns three times and gets stronger each time. *(DS, NEW)*
- [BOS-07] **Lycaon, the First Wolf** — The final boss. Phase 1 is a crowned man. Phase 2 is a colossal wolf on the Moon-chained spire. In Phase 3 you transform and fight him beast to beast. *(OoT, DS3)*
- [BOS-08] **Silver mist gates** — Boss arenas are sealed by a mist wall. Walking through it starts the music and the boss bar. Dying sends you back to the last Moonwell. ⭐ *(DS)*
- [BOS-09] **Use the dungeon item** — Each boss's main weakness is the dungeon's new tool (for example, the grappling chain pulls the wyvern down). *(OoT, TP)*

## 9. World & Biomes (WLD)

- [WLD-01] **One seamless heightmap world** — A map of about 2 × 2 km, generated in Python (layered noise plus a biome mask PNG that can be painted by hand). It's streamed in chunks with LOD. ⭐ *(DOC)*
- [WLD-02] **Brackenvale (start)** — Rolling meadows, a ruined Warden outpost, a burned village, standing stones and gentle slopes. Levels 1–5. ⭐ *(OoT, SK)*
- [WLD-03] **The Wolfwood** — Dense dark pine, fog, fallen giant trees, wolf dens, spider groves. Levels 4–10. ⭐ *(TP, SK)*
- [WLD-04] **The Blackmire** — Swamp: shallow water that slows you, stilt-huts, sunken ruins, drifting mist, lantern-flies. Levels 6–12. ⭐ *(OoT, MW, OB)*
- [WLD-05] **Frostfang Peaks** — Snowy switchbacks, cliffs, ice caves, a harpy roost, and blizzards that shorten sight lines. Levels 10–16. ⭐ *(SK, DS)*
- [WLD-06] **The Ashen Reach** — Volcanic badlands, lava cracks, obsidian spires, an orc warcamp and golem ruins. Levels 13–18. *(OoT, MW, DS)*
- [WLD-07] **The Sunken Crypts** — An underground network beneath the Vale, with skeletons, wraiths and a necromancer. Shortcuts open back to the surface. *(DS1, SK)*
- [WLD-08] **The Eclipse Spire** — A black tower in the center of the map, chained to the Moon. You can see it from anywhere. It's the final area and the compass of the whole world. ⭐ *(OoT, SK, DS)*
- [WLD-09] **Moonwells** — Rest points that heal, refill flasks, respawn enemies, save the game, and let you upgrade weapons and fast travel between wells you've lit. ⭐ *(DS)*
- [WLD-10] **Shortcuts that loop back** — Gates, ladders and elevators that you open from the far side, so the world folds back to your last Moonwell. ⭐ *(DS1)*
- [WLD-11] **Day/night cycle and weather** — Day, night and the moon phase change spawns (wraiths and werewolves at night), lighting and fog. Each biome has its own weather. ⭐ *(MM, OoT, SK)*
- [WLD-12] **Scripted scatter** — Trees, rocks, grass, ruins and camps are placed with Poisson-disk sampling, using rules per biome (slope, height, density, clearings). ⭐ *(DOC)*
- [WLD-13] **One hand-picked landmark per area** — Each region has one set piece placed deliberately (the burned windmill, the troll bridge, the frozen giant), and generated land around it. ⭐ *(DOC)*
- [WLD-14] **Dungeons from a scripted kit** — Python generates modular walls, floors, stairs and arches. Dungeon layouts are short JSON grids assembled from them. *(DOC)*
- [WLD-15] **Dungeon tools that gate the world** — A grappling chain, a silver lantern (shows hidden paths), and iron boots (walk on lakebeds). Each opens new areas in the overworld. *(OoT, TP)*
- [WLD-16] **Hidden walls and secrets** — Hidden walls that one hit reveals, cracked walls you can bomb, and a dig spot in beast form. *(DS, OoT)*
- [WLD-17] **Loot chests and loot tables** — Chests, corpses with loot and enemy drops, all from data-driven loot tables with rarity tiers. ⭐ *(SK, DS)*
- [WLD-18] **Ambient wildlife** — Deer, crows and rabbits that run from you, making the world feel alive at almost no cost. *(SK, OB)*
- [WLD-19] **Simple traversal** — Auto-jump at ledges and climbing on marked ledges. Deep water makes you drown and respawn nearby (swimming comes later). ⭐ *(OoT)*
- [WLD-20] **Pacing director** — A hidden system that watches HP, deaths and how long since the last fight, then adjusts ambushes, quiet stretches and Elite spawns. *(DOC)*
- [WLD-21] **World validators** — Automated checks: every Moonwell can be reached, no spawns inside geometry, no slopes you can't climb on main paths, and a maximum distance between safe points. ⭐ *(DOC)*
- [WLD-22] **Fishing pond** — A later stretch goal: a relaxing fishing minigame at a lake hut. *(OoT, TP)*

## 10. HUD & UI (UIX)

- [UIX-01] **Minimal HUD** — HP, stamina and Bloodlust bars top-left. Quick slots (flask, crossbow bolts, throwable) bottom-left. Essence count bottom-right. ⭐ *(DS)*
- [UIX-02] **Compass bar** — A compass across the top with markers for Moonwells, discovered landmarks and the Spire. *(SK)*
- [UIX-03] **Map and compass items** — Each dungeon's map and compass are items you find. They reveal its layout and its chests. *(OoT, TP)*
- [UIX-04] **Lock-on reticle and enemy plates** — The locked target gets a reticle. Damaged enemies show a small HP bar with their level. ⭐ *(OoT, DS)*
- [UIX-05] **Boss bar** — A name and a large HP bar at the bottom of the screen, which appears when you pass the mist gate. ⭐ *(DS)*
- [UIX-06] **Level-up screen** — Shows each attribute with live previews of how derived stats change (green or red) before you confirm. ⭐ *(DS)*
- [UIX-07] **Pause menu** — Inventory grid, equipment, stats and skills, map, bestiary, settings. ⭐ *(SK, OoT)*
- [UIX-08] **Bestiary** — Unlocks as you kill enemies: the model on a turntable, lore, weaknesses and a button that plays its voice line. *(TP, SK)*
- [UIX-09] **Death screen** — *"THE MOON TURNS AWAY"* fades in, then you wake at your Moonwell. ⭐ *(DS, NEW)*
- [UIX-10] **Subtitles for every voice line** — On by default, with a speaker name and a size setting. ⭐ *(DOC)*
- [UIX-11] **Controller and rebinding** — Xbox and PlayStation layouts through `pygame.joystick`, and fully rebindable keyboard and mouse. ⭐ *(DOC)*
- [UIX-12] **Comfort and accessibility** — FOV slider, camera shake and head-bob scaling, high-contrast telegraphs, a hold-or-toggle option for every hold input, and an optional assist mode. *(DOC)*
- [UIX-13] **UI drawn with pygame, shown through GL** — HUD and menus are drawn on a pygame Surface and uploaded as a texture each frame, so there's no extra UI library. ⭐ *(DOC)*
- [UIX-14] **The Hunger's subtitles look different** — The Hunger's lines appear in italic amber with a subtle shake, so you always know when it's the curse talking. *(NEW)*

## 11. Audio & Voice (AUD)

- [AUD-01] **Voice pipeline** — `data/lines.csv` → `tools/voice/generate.py` (ElevenLabs API) → ffmpeg mastering → `assets/audio/vo/`. Re-runs are cached by a hash of the text and settings. ⭐ *(DOC)*
- [AUD-02] **Designed voices only** — Every voice is made with ElevenLabs Voice Design from a text description. No clones of real people. Voice IDs and settings are kept in `data/voices.json`. ⭐ *(DOC)*
- [AUD-03] **Enemy barks** — For each voiced enemy: spotting you (3), attack effort (4), pain (3), death (2), idle (2), with 2 or 3 takes each. The game picks a random take and never plays the same one twice in a row. ⭐ *(DOC, SK)*
- [AUD-04] **Expressive audio tags** — Tags like `[growls]`, `[laughs]`, `[whispers]` and `[shouting]` give barks and the Hunger more character. ⭐ *(DOC)*
- [AUD-05] **Creature sounds from the SFX API** — Squeaks, howls, chittering, roars, gurgles and grinding stone, generated with ElevenLabs Sound Effects. ⭐ *(DOC)*
- [AUD-06] **Combat SFX set** — Swings (light and heavy), impacts per material (flesh, metal, bone, stone, ooze), parry clang, rolls, footsteps per biome and a transformation roar, all generated. ⭐ *(DOC)*
- [AUD-07] **Music for each biome** — Generated tracks (ElevenLabs Music) with an exploration layer and a combat layer that crossfade, plus a theme for each boss. *(OoT, SK)*
- [AUD-08] **Positional audio** — Pan and volume from distance and angle in pygame.mixer, plus a low-pass effect when the source is behind geometry (baked into variants). ⭐ *(DOC)*
- [AUD-09] **Signature jingles** — Short original stings for leveling up, parrying, lighting a Moonwell and opening a chest. Players should come to listen for them. *(OoT, TP)*
- [AUD-10] **Loudness mastering** — Normalize loudness, trim silence and export to OGG Vorbis. Keep all takes outside the game folder. ⭐ *(DOC)*
- [AUD-11] **Pronunciation dictionary** — A single place to fix names (Lycaon, Aldmoor, Fenhallow) for every voice. *(DOC)*
- [AUD-12] **Beast-form audio filter** — In beast form, the world sounds muffled and bassy, your heartbeat is louder, and enemy heartbeats are audible. *(TP, NEW)*

## 12. Art Pipeline (ART)

- [ART-01] **Meshy batch script** — `assets/manifest.json` (prompts, polycount targets, rig and animation requests) → `tools/meshy/batch.py` → preview → refine → remesh → download GLB. It's cached and can be resumed, and every model is logged to CREDITS.md. ⭐ *(DOC)*
- [ART-02] **Shared style suffix** — Every prompt ends with the same style line, e.g. *"stylized dark-fantasy, hand-painted textures, chunky readable silhouette, muted earthy palette, game-ready low-poly."* This keeps everything consistent. ⭐ *(DOC)*
- [ART-03] **Meshy auto-rig and animations for humanoids** — Rowan, bandits, goblins, orcs, skeletons, knights, the ogre and the werewolf go through Meshy's rigging and animation library: idle, walk, run, attacks, hit and death. ⭐ *(DOC)*
- [ART-04] **Procedural animation for non-humanoids** — Spiders, wolves, rats, oozes and harpies are animated in code (IK legs, sine gaits, squash and stretch). Meshy's auto-rig targets humanoids. ⭐ *(DOC)*
- [ART-05] **Image → 3D for hero assets** — Make concept images first (Meshy's image generation or your own sketches), then use image-to-3D for Rowan and the bosses to get better consistency. *(DOC)*
- [ART-06] **Polygon and texture budgets** — Props 300–2k triangles, enemies 5–15k, Rowan and bosses up to 25k. Textures 512–2048 px. Meshy's remesh enforces the targets. ⭐ *(DOC)*
- [ART-07] **Python normalizer (no Blender needed)** — A `trimesh`/`pygltflib` script that fixes scale (1 unit = 1 m), forward axis, pivot at the feet, makes LODs by decimation and builds collision capsules and boxes. ⭐ *(DOC)*
- [ART-08] **Procedural terrain textures** — Grass, dirt, rock, snow, mud and ash made with numpy noise (albedo and normal), blended by slope, height and the biome mask with triplanar projection. ⭐ *(NEW)*
- [ART-09] **Procedural sky** — A shader gradient, sun and **a huge moon** with phases, stars, and a red tint on Blood Moon nights. No texture assets needed. ⭐ *(NEW)*
- [ART-10] **Instanced grass with wind** — Grass blades generated by GPU instancing and moved by wind in the shader, with density from the biome mask. ⭐ *(NEW)*
- [ART-11] **Scripted modular dungeon kit** — Python builds wall, floor, arch, stair and pillar meshes from parameters, then Meshy's AI texturing gives them surfaces. *(DOC)*
- [ART-12] **Post-processing stack** — Height fog, bloom, ACES tone mapping, vignette, and color grading for each biome from LUTs generated by script. ⭐ *(DOC)*
- [ART-13] **GPU particles** — Sparks, blood (with a toggle), embers, snow, fireflies and spores as instanced quads. Particle textures are drawn with numpy. ⭐ *(NEW)*
- [ART-14] **Auto-rendered item icons** — Item GLBs are rendered offscreen with moderngl to make inventory icons automatically. *(DOC)*
- [ART-15] **Unifying shading** — Soft toon ramp, rim light and shared fog so that AI models in slightly different styles still look like they belong together. ⭐ *(DOC)*
- [ART-16] **Asset previewer** — A small tool that shows each Meshy result on a turntable next to Rowan for scale, with Accept, Reject and Re-roll buttons (same approach as the idea tracker). *(DOC)*

## 13. Engine & Tech (TEC)

- [TEC-01] **pygame-ce instead of pygame** — A drop-in fork (`import pygame` still works) that's actively maintained and has relative mouse mode, better performance and newer SDL. ⭐ *(DOC)*
- [TEC-02] **moderngl on OpenGL 3.3 core** — A single GL context from pygame and shaders in `.glsl` files that hot-reload in dev builds. ⭐ *(DOC)*
- [TEC-03] **PyGLM for math** — Fast vec, mat and quat types for gameplay, with numpy for bulk work (terrain, skinning palettes, particles). ⭐ *(NEW)*
- [TEC-04] **Fixed 60 Hz simulation and interpolated rendering** — Stable frame data and parry windows at any frame rate. ⭐ *(DOC)*
- [TEC-05] **Simulation doesn't touch rendering** — Gameplay state never calls the renderer. The renderer, audio and UI read state and react to events. ⭐ *(DOC)*
- [TEC-06] **Event bus** — Events like `Hit`, `Parried`, `Died`, `LevelUp` and `Transformed` drive SFX, VFX, barks, subtitles and the HUD. ⭐ *(DOC)*
- [TEC-07] **Content as data, with hot reload** — Enemies, attacks, items, loot, biomes and the XP curve live in JSON. Pressing F5 in dev reloads them without restarting. ⭐ *(DOC)*
- [TEC-08] **GLB loader with GPU skinning** — `pygltflib` reads meshes, skins and animations. Joint matrices go to the vertex shader through a uniform buffer, with crossfades between clips. ⭐ *(DOC)*
- [TEC-09] **Light collision** — Character capsules collide with the heightmap and with simple static colliders (spheres, capsules, oriented boxes) through a spatial hash. No physics engine. ⭐ *(DOC)*
- [TEC-10] **Terrain chunks with LOD and culling** — 64 m chunks with 3 LOD levels and frustum culling, and skirts to hide cracks between chunks. ⭐ *(NEW)*
- [TEC-11] **Instanced rendering** — One draw call per prop type per chunk, so thousands of trees and rocks stay cheap. ⭐ *(DOC)*
- [TEC-12] **Shadow map** — One shadow cascade that follows the player, with PCF filtering. Distant shadows fade into fog. ⭐ *(NEW)*
- [TEC-13] **Enemy AI** — A finite state machine for each archetype (idle, patrol, alert, approach, strafe, attack, recover, stagger, flee, dead) with utility scores for picking attacks. Steering on terrain, and grid A* in dungeons. ⭐ *(DOC)*
- [TEC-14] **Activation radius** — Only enemies within about 80 m run their full AI. Farther ones sleep, which keeps Python within its budget. ⭐ *(NEW)*
- [TEC-15] **Seeded RNG and input replays** — One seeded RNG, plus recording of inputs per tick, so bugs can be replayed exactly. *(DOC)*
- [TEC-16] **Save system** — JSON saves (stats, inventory, Moonwells lit, bosses killed, shortcuts opened, position) with versioned migrations. ⭐ *(DOC)*
- [TEC-17] **Debug overlay** — Hitboxes and hurtboxes, AI state labels, FPS and frame-time graph, free camera, and a spawn console (`spawn ogre 3`). ⭐ *(DOC)*
- [TEC-18] **pytest from day one** — Tests for stat formulas, damage resolution, XP curve, frame-data validation, JSON schema checks and save round-trips. ⭐ *(DOC)*
- [TEC-19] **Profile, then optimize** — Profile with cProfile and py-spy, use numpy for bulk work, and Cython only for proven hot spots. *(DOC)*
- [TEC-20] **Lua modding through Lupa** — A later option: sandboxed Lua for enemy behaviors and mods. *(DOC)*
- [TEC-21] **PyInstaller onedir build and butler** — A Windows build first, pushed to itch.io with `butler` for delta patches. ⭐ *(DOC)*
- [TEC-22] **GitHub Actions CI** — Tests on every push, and a Windows build artifact when a version is tagged. *(DOC)*
- [TEC-23] **Settings file** — Resolution, window mode, VSync, FOV, sensitivity, invert Y, volumes and keybinds. ⭐ *(NEW)*
- [TEC-24] **Background asset loading** — Load GLBs and audio in a thread behind a loading screen, then upload to the GPU on the main thread. *(NEW)*

## 14. Tools (TOL)

- [TOL-01] **Idea tracker** — This Tkinter app. It tracks Awaiting, Approved and Denied, writes `ideas_status.json` for Claude to read, and has a CLI too. ⭐ *(NEW)*
- [TOL-02] **Frame-data editor** — A Tkinter timeline that shows wind-up, active and recovery as colored bars, with sliders and a live preview of the hitbox path. *(DOC)*
- [TOL-03] **Voice take picker** — Lists every line and its takes, plays them with pygame.mixer, and marks the best take with one key. *(DOC)*
- [TOL-04] **Balance simulator** — Headless duels give time-to-kill, hits-to-kill and damage taken for every enemy level against every player level, written to a CSV and a chart. *(DOC)*
- [TOL-05] **Biome mask painter** — Paint the biome PNG in any image editor and re-run the world generator. The tool is just a script plus a preview. ⭐ *(DOC)*
- [TOL-06] **Asset credits builder** — Builds CREDITS.md from the Meshy and ElevenLabs logs (prompt, voice, date, plan) on every build. ⭐ *(DOC)*
- [TOL-07] **AI playtest bot** — A later stretch goal: a scripted or RL bot that walks the world and duels enemies to find balance outliers. *(DOC)*

## 15. Release & Licensing (REL)

- [REL-01] **MIT license for the code** — `LICENSE` at the root. Generated assets get their own note in `ASSETS-LICENSE.md` (for example CC BY 4.0). ⭐ *(NEW)*
- [REL-02] **CREDITS.md from day one** — Every model (prompt, Meshy plan, date), every voice (description, plan, date) and every font. ⭐ *(DOC)*
- [REL-03] **AI disclosure on itch.io** — State plainly that the models, voices, SFX and music are AI-generated, and that the voices are designed rather than cloned. ⭐ *(DOC)*
- [REL-04] **Check the terms for public assets** — Before putting raw Meshy and ElevenLabs outputs in a public repo, re-read both services' current terms on redistribution. If anything is unclear, keep binaries in the release zip or GitHub Releases rather than the repo. ⭐ *(DOC)*
- [REL-05] **Git LFS for binaries** — `.glb`, `.png`, `.ogg` and `.wav` files go through LFS, which keeps the repo light. ⭐ *(NEW)*
- [REL-06] **Keys stay secret** — `MESHY_API_KEY` and `ELEVENLABS_API_KEY` stay in environment variables, and `.env` is in `.gitignore`. ⭐ *(DOC)*
- [REL-07] **Weekly devlog and build** — A GIF, a changelog and an itch.io upload every week. ⭐ *(DOC)*
- [REL-08] **SmartScreen note** — Explain "More info → Run anyway" on the itch.io page for the unsigned build. ⭐ *(DOC)*
- [REL-09] **Name check** — Search itch.io, Steam and GitHub for "Lycantrope" before making store art. ⭐ *(DOC)*
