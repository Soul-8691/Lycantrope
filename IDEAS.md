# LYCANTROPE — Ideas

> *Every goblin has a cave. Every cave has a chest. Every chest has a mimic. Somebody has to deal with it.*

**Lycantrope** is a free, open-source (MIT) 3D action-adventure fantasy RPG built with **Python + pygame(-ce) + moderngl**. The main focus is combat. You play one fixed hero, a humble youth chosen by prophecy, on a classic quest to stop a returning Dark Lord. The title is a play on the game's real stars: a bestiary full of **classic fantasy-trope monsters**.

**Inspirations (only these nine):** *Ocarina of Time* (OoT), *Majora's Mask* (MM), *Twilight Princess* (TP), *Morrowind* (MW), *Oblivion* (OB), *Skyrim* (SK), *Dark Souls* 1–3 (DS1/DS2/DS3, or DS for the whole series). Ideas tagged **DOC** are programming and pipeline ideas adapted from `DREAM-QUEST.md` and `THE_DREAMLANDS.md`, with nothing Lovecraftian and nothing exclusive to Morrowind. Ideas tagged **NEW** are original.

---

## How this file works with the Idea Tracker

- Each idea is one bullet that starts with an **ID** in brackets: `- [CMB-04] **Title** — description *(sources)*`.
- **IDs never change.** New ideas take the next free number in their category. Deleted ideas keep their old ID, which is never reused. *(On 2026-11-23 the story changed from a werewolf plot to a generic hero plot. The ideas that only fit the old story were removed, and they appear in the tracker under "Removed from IDEAS.md".)*
- ⭐ = recommended for the **First Playable** milestone (see ROADMAP.md).
- Run the tracker with `run_idea_tracker.bat` or `python tools/idea_tracker.py`. It watches this file, so new ideas show up while it is open.
- Decisions are saved to `ideas_status.json`, the source of truth that Claude reads. `IDEAS_STATUS.md` is a readable summary generated from it. When you want to refer to an idea, just use its ID ("deny VAL-04", "what did I approve in Combat?").

---

## 1. Pillars (PIL)

- [PIL-01] **Combat first** — Every system feeds the fight. Exploration exists to find new enemies, new gear and XP. If a feature doesn't make combat deeper or more varied, it waits. ⭐ *(NEW)*
- [PIL-02] **Deliberate, readable, fair** — Enemies show clear wind-ups, the player commits to attack animations, and every death teaches you something. Difficulty comes from timing, not from huge HP pools. ⭐ *(DS, DOC)*
- [PIL-04] **See it, go there** — An open world built around landmarks you can see from far away. The Dark Lord's citadel, mountains and ruins pull you toward them. ⭐ *(OoT, SK)*
- [PIL-05] **Generated, not hand-made** — Models come from Meshy, voices and SFX from ElevenLabs, and terrain, textures, sky, VFX and kits from Python scripts. Hand work only fixes things; it doesn't create them. ⭐ *(DOC)*
- [PIL-06] **Tropes played straight, with a wink** — Familiar fantasy (prophecy, dark lord, chosen hero, wise mentor, elemental dungeons) done sincerely. The title's pun and the bestiary are the wink. ⭐ *(NEW)*
- [PIL-07] **Ship small, ship often** — Every week ends with a playable build. Content is data, so new enemies and items don't need new code. ⭐ *(DOC)*
- [PIL-08] **Valor: fight bravely, get stronger mid-fight** — Aggressive, skilful play (clean hits, parries, close dodges) fills a Valor meter that powers the hero's sword. Playing it safe is allowed; playing it brave pays. This is the combat hook (see VAL). ⭐ *(NEW)*
- [PIL-09] **From nobody to legend** — Rowan starts as a farmhand with an old sword and ends as the realm's champion. Early areas feel dangerous; going back to them later feels heroic. ⭐ *(OoT, MW, DS)*
- [PIL-10] **A monster for every trope** — Rats in the cellar, goblins in the cave, a troll under the bridge, a dragon on the mountain. Players should recognize every enemy instantly and still learn something new about how it fights. ⭐ *(NEW)*

## 2. Story & Setting (STY)

- [STY-02] **The realm of Aldmoor** — A fading kingdom of mossy ruins, abandoned watchtowers and wild country, where the monsters outnumber the people. The empty world is part of the story, and it's why there are no NPCs at first. ⭐ *(NEW)*
- [STY-03] **Four Crown Shards, four dungeons** — Wolfwood, Blackmire, Frostfang Peaks and Ashen Reach. Each holds a shard of the Crown of Dawn, guarded by a boss and one of the Dark Lord's generals. This is the classic structure of dungeon → item → boss. *(OoT, TP)*
- [STY-09] **Story told through items and places** — Item descriptions, ruined camps, corpses and scattered journals tell most of the story. Only a few lines are voiced. ⭐ *(DS, MW)*
- [STY-10] **Readable lore books and notes** — Short in-world texts (old hero legends, the Dark Lord's decrees, bandit letters) found in the world. They're generated from templates and edited by hand. *(MW, OB, SK)*
- [STY-11] **Shadow Moon nights** — Every few in-game nights the Dark Lord's power peaks: a red sky, stronger enemy variants and more XP. *(MM, NEW)*
- [STY-12] **Four generals with names and barks** — Each Crown Shard is held by one of the Dark Lord's generals, who taunts you across the dungeon with voiced lines and then fights next to the boss. *(OoT, TP)*
- [STY-13] **Premise: the Dark Lord returns** — A thousand years ago a hero shattered the Crown of Dawn to seal **Malgrath the Undying** inside his citadel. The seal is failing, his armies are spreading over Aldmoor, and a prophecy speaks of a hero "born of no house, carrying a forgotten blade." ⭐ *(OoT, SK)*
- [STY-14] **Prologue: the village burns** — Rowan's home village in Brackenvale is raided by goblins and the Dark Lord's soldiers. Grabbing grandfather's old sword from above the hearth to fight back, Rowan finds it awakens in their hand. This is the tutorial. ⭐ *(OoT, TP, SK)*
- [STY-15] **The wise mentor** — Aldric Greymantle, an old wandering wizard who recognises the sword, explains the prophecy and teaches the basics. Trope played straight: he falls mid-game protecting Rowan. *(OoT, SK)*
- [STY-16] **Ember, the spirit in the sword** — The sword holds a talkative spirit, the soul of the ancient hero, who gives hints, reacts to fights and remembers the last war. A companion who can't be killed, and a built-in hint system. *(OoT, TP)*
- [STY-17] **Ending: the final battle, with one secret** — Defeat Malgrath and restore the Crown. The normal ending is triumphant. A secret ending lets Rowan put the Crown on instead, becoming the next Dark Lord. *(DS1, SK)*
- [STY-18] **"The Lycantrope": an in-world bestiary** — The bestiary is a book called *The Lycantrope: A Field Guide to Monsters Most Common*, by a snarky travelling scholar. Its entries poke fun at each monster's trope while giving real tactics. This ties the title into the game. *(NEW)*
- [STY-19] **A rival champion** — Sir Calder the Black, the Dark Lord's champion and a fallen hero of the old order, duels Rowan several times across the journey (see BOS-10). *(DS, OoT)*

## 3. The Hero (HER)

- [HER-02] **Rowan is a woman** — Voice direction: warm, determined, a little wry, early 20s. Pick this **or** HER-03. ⭐ *(NEW)*
- [HER-03] **Rowan is a man** — Voice direction: earnest, steady, a little wry, early 20s. Pick this **or** HER-02. ⭐ *(NEW)*
- [HER-05] **A few memorable lines** — Short voiced reactions: on level up, low HP, a boss kill, entering a new biome, and arguing with Ember. About 40 lines in total, and few enough that each one gets noticed. ⭐ *(SK, TP)*
- [HER-07] **Visible armor swaps** — Armor pieces swap meshes on the model (head, chest, arms, legs). This comes later, after the First Playable. *(SK, DS)*
- [HER-08] **Signature idle animations** — Rowan tests the sword edge, adjusts the scarf, and swats at a passing fly. *(TP, NEW)*
- [HER-09] **Rowan Fenhallow, the farmhand of prophecy** — A young farmhand from Brackenvale. Look: a patched brown travelling coat, a **long red scarf** that trails in the wind (the silhouette people remember), a mismatched pauldron picked up along the way, and a small round buckler. Weapon: the **Dawnblade**, grandfather's old sword. ⭐ *(NEW)*
- [HER-10] **The Dawnblade grows with you** — The sword starts rusty and dull. Each Crown Shard restores part of it: new glow, a new edge, a new move (see VAL-05). Players see their progress on the weapon itself. ⭐ *(OoT, TP)*

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
- [CMB-14] **Hit feel** — Hitstop (50–90 ms), camera shake, a small FOV punch and impact sounds that vary by material. No sparks (decided 2026-11-24). This matters more than anything else in this file. ⭐ *(DOC)*
- [CMB-15] **Input buffering** — Attack, dodge and parry presses are buffered for about 150 ms so combos feel responsive. ⭐ *(DOC)*
- [CMB-16] **Frame data as JSON** — Every attack lists its wind-up, active and recovery frames, the hitbox shape and path, damage, poise damage, stamina cost, cancel windows and the parryable flag. Easy to tune and to test. ⭐ *(DOC)*
- [CMB-17] **Swept-capsule hitboxes** — The weapon's hitbox is swept between frames so fast swings don't pass through enemies. Each actor has capsule hurtboxes. ⭐ *(DOC)*
- [CMB-18] **Damage types and resistances** — Slash, strike, pierce, fire, frost and **radiant** (holy light). Each enemy has resistance values (skeletons resist slash, trolls fear fire, wraiths fear radiant). ⭐ *(DS, MW, SK)*
- [CMB-19] **Status buildup** — Bleed, poison, burn, frost (slow) and stun build up as meters and trigger when full. *(DS)*
- [CMB-20] **Hand crossbow** — Quick shots from the hip or aimed over the shoulder. Bolt types: iron, blessed, fire. It's used to knock fliers down and to interrupt casters. ⭐ *(OoT, TP)*
- [CMB-21] **Throwables** — Firebombs, holy water (hurts undead), and smoke (drops aggro). *(DS, OoT)*
- [CMB-22] **Lifewater flask** — A healing flask with a few charges, refilled when you rest at a Waystone. You can find upgrades for more charges and stronger healing. ⭐ *(DS)*
- [CMB-23] **Weapon classes** — Longsword (the Dawnblade), axe, mace, spear and greatsword. Each class has its own moveset and stat scaling. *(DS, SK)*
- [CMB-24] **Weapon upgrades at Waystones** — +1 to +10 using ore found in the world. No smith NPC is needed. *(DS)*
- [CMB-25] **Rune sockets** — Socket found runes into weapons for elemental damage or effects on hit. *(SK, MW, OB)*
- [CMB-26] **Equip load tiers** — Under 30% is a fast roll, under 70% a medium roll, and more than that a slow roll. Heavy armor is a real trade-off. *(DS)*
- [CMB-27] **Attack tokens** — Groups share a limited pool of "attack tokens", so only one or two enemies attack at the same time and fights stay readable. ⭐ *(NEW)*
- [CMB-28] **Difficulty through reaction time** — Higher-level and elite enemies react faster, parry and dodge more often, and follow up more. Their HP grows only moderately. ⭐ *(DOC)*
- [CMB-29] **Rites (small spell set)** — Three or four spells: *Flash* (parries at range), *Ward* (a short barrier), *Mark* (makes a target take more damage). They cost focus. *(SK, OB, DS)*
- [CMB-30] **Essence drop on death** — When you die, you drop all unspent XP where you fell. Get back there without dying again to recover it. *(DS)*
- [CMB-31] **Kicks and environment kills** — Kick to break a guard or knock an enemy off a ledge. Explosive barrels, spike traps and falling rocks hurt enemies too. *(DS, OoT)*
- [CMB-32] **Mounted combat on horseback** — A later stretch goal: ride a horse across the open world and fight from the saddle. *(TP, OoT)*

*A casting system for Rites to replace Focus (per the note on CMB-29). Pick **one** of CMB-33 to CMB-36.*

- [CMB-33] **Rite charges** — Each Rite has a few casts (for example, 3) that refill only when you rest at a Waystone. The Spirit replacement adds extra charges. Simple and readable, and it makes resting matter. **Recommended.** *(DS1)*
- [CMB-34] **Rite cooldowns** — Each Rite recharges over time (8–30 s), like the relic powers (VAL-03), and Faith shortens cooldowns. No resource to manage, so casting is part of the rhythm of every fight. *(SK, NEW)*
- [CMB-35] **Stamina casting** — Rites cost stamina, the same pool as attacks and dodges. One resource for everything; casting competes with defending, which keeps it tense. *(DS, NEW)*
- [CMB-36] **Lifeblood casting** — Rites cost a slice of HP, which slowly returns out of combat. Strong spells at a real price; pairs well with high Vigor builds. *(MW, NEW)*

## 5. Valor & the Dawnblade (VAL)

- [VAL-01] **Valor meter** — Fills from clean hits, parries, ripostes and close dodges. Drains slowly when you back off, and drops when you're hit. It rewards brave, skilful play. ⭐ *(NEW)*
- [VAL-02] **Awakening** — Spend a full Valor meter to awaken the Dawnblade for about 15 s: it ignites, gains reach, heavy attacks send out a wave of light, stamina refills faster, and light hits can't be interrupted. The music swells and the screen warms. ⭐ *(TP, NEW)*
- [VAL-03] **Relic powers** — Each Crown Shard grants a power on a cooldown: *Gale* (a knockback cone), *Frostward* (freeze attackers), *Earthshaker* (a ground slam), *Flame Ring* (a fire burst). *(OoT, SK)*
- [VAL-04] **Last Stand** — Once per rest, a killing blow leaves Rowan at 1 HP instead, with a moment of slow motion and a full Valor meter. A classic "the hero won't fall here" moment. ⭐ *(NEW)*
- [VAL-05] **A new move with each shard** — Each restored part of the Dawnblade unlocks a sword technique: a dash-thrust, a rising slash, a charged plunge, a crescent sweep. *(TP, OoT)*
- [VAL-06] **Seer's Lens** — A relic that, when held, reveals hidden walls, invisible enemies and secret chests for a few seconds. *(OoT, MM)*
- [VAL-07] **Trophy masks** — Wearing a mask taken from a defeated boss lends Rowan one of its traits (the Brood Queen's mask makes poison weaker). *(MM)*
- [VAL-08] **Light against darkness** — The Dawnblade glows in dark dungeons and crypts, making a moving light source. Undead and shadow creatures flinch from Awakening. *(TP, OoT)*
- [VAL-09] **Ember's commentary** — Ember (STY-16) reacts to how you fight: praise for a parry chain, a groan when you roll into a wall, a warning about a new enemy's weakness. *(OoT, TP)*

## 6. Stats, Skills & Leveling (STA)

- [STA-01] **XP from kills** — XP depends on enemy level and the level difference between you (0.25× to 2×). The curve: `xp_to_next(L) = 100 · L^1.5`. ⭐ *(SK, DS)*
- [STA-02] **Level up anywhere** — Once you have enough XP, open the level-up screen any time you're out of combat. No NPC. Choose this **or** STA-03. ⭐ *(SK, NEW)*
- [STA-03] **Level up only at Waystones** — Spend XP while resting at a Waystone. It's riskier and more like Dark Souls. Choose this **or** STA-02. *(DS)*
- [STA-04] **Six attributes** — **Might** (heavy weapons, poise damage), **Dexterity** (light and precise weapons, crossbow, attack recovery; STA-16), **Vigor** (HP), **Endurance** (stamina, equip load), **Faith** (radiant damage, Rites and their cooldowns, Lifewater healing; STA-20), **Fortune** (crit chance, loot). *(Finesse and Spirit were replaced on 2026-11-24.)* Each level gives +1 point. ⭐ *(DS, MW, OB)*
- [STA-05] **Derived stats with soft caps** — HP, stamina, equip load, poise and crit chance come from the attributes through curves that slow down past 20 and again past 40. ⭐ *(DS)*
- [STA-06] **Skills improve by use** — Blade, Blunt, Polearm, Marksman, Guard, Evasion, Athletics and Rites, each from 1 to 100. Landing hits, blocking, dodging well, sprinting and casting all raise them. ⭐ *(MW, OB, SK)*
- [STA-07] **Hybrid progression** — Your character level (from XP) gives attribute points. Skill levels (from use) give percentage bonuses and perks. Both matter. ⭐ *(SK, DS)*
- [STA-08] **Perks every 10 skill levels** — Choose one of two perks at each milestone. For example, Evasion 30: *longer i-frames* or *roll costs 25% less stamina*. *(SK)*
- [STA-09] **Weapon scaling grades** — Weapons show S/A/B/C/D/E scaling with Might, Dexterity and Faith, and an upgraded weapon's grades rise. *(DS)*
- [STA-10] **Fixed-level regions** — Each region has a fixed level range (the Vale is 1–5, the Peaks 12–18). The world does **not** scale to the player, so going back to an early area makes you feel powerful. ⭐ *(DS, MW)*
- [STA-11] **Heart shards** — Hidden collectibles. Every 4 shards give +10% max HP permanently, and stamina shards work the same way. They reward exploration outside the leveling system. ⭐ *(OoT, TP)*
- [STA-12] **Respec item** — The rare *Tear of Renewal* lets you redistribute all attribute points once. *(DS)*
- [STA-13] **Optional damage numbers** — Floating damage numbers, off by default, with a setting to turn them on. *(NEW)*
- [STA-14] **Stat gates** — A few heavy doors and gaps need Might or Finesse 15+ (or a relic power), which gives builds a role in exploration. *(MW, DS)*

*Replacing Finesse and Spirit (2026-11-24). Pick **one** of STA-15/16/17 for Finesse and **one** of STA-18 to STA-22 for Spirit. Recommended: **Agility + Resolve**.*

- [STA-15] **Agility (replaces Finesse)** — The movement stat, which suits a dodge-first game now that parries and backstabs are denied. It scales swords, spears and the crossbow, and also improves roll speed and recovery, i-frames (up to +3 frames), sprint speed and crossbow reload. Crit chance moves entirely to Fortune, so the two no longer overlap. **Recommended.** *(DS, OB, SK)*
- [STA-16] **Dexterity (replaces Finesse)** — The classic weapon-handling stat: scaling for light and precise weapons (sword, spear, crossbow) plus faster attack recovery, so combos flow. It doesn't affect movement. *(DS, MW)*
- [STA-17] **Precision (replaces Finesse)** — A damage-focused stat: bonus damage to weak points (armored-weakpoint enemies, a scorpion's tail, golem cores), to staggered enemies, and with crossbow bolts. Fortune keeps crit chance; Precision raises crit damage. *(DS, NEW)*
- [STA-18] **Resolve (replaces Spirit)** — Inner grit, which fits a farmhand hero. It powers Rites and shortens relic power cooldowns (VAL-03), and resists status buildup (poison, bleed, frost, stone), fear screams and grabs. It gives a magic build and a tank build a reason to share a stat. **Recommended.** *(SK, MW, NEW)*
- [STA-19] **Arcana (replaces Spirit)** — A pure magic stat: Rite damage and effect, the number of Rites you can equip, relic power strength, and magic resistance. The clearest choice if you want a dedicated caster build. *(OB, SK, DS)*
- [STA-20] **Faith (replaces Spirit)** — Holy power, tying into the Dawnblade and the ancient hero: radiant damage (the Dawnblade's light, holy water, blessed bolts), Rites as prayers, and stronger Lifewater healing. *(DS, OoT)*
- [STA-21] **Willpower (replaces Spirit)** — Mental toughness: keeps your guard and casts from being interrupted, adds Rite charges or shortens cooldowns (whichever casting system wins), and resists status buildup. Less magical than Arcana, broader than Faith. *(MW, OB)*
- [STA-22] **Five attributes (drop Spirit, no replacement)** — Remove the stat entirely: Rites scale with Vigor and relic powers with Fortune. A simpler level-up screen, but magic stops being a build of its own. *(NEW)*
- [STA-23] **Attunement slots** — However Spirit is replaced, its successor also sets how many Rites and relic powers you can equip at once (1 slot at start, +1 at 15, 25 and 40), so investing changes your toolkit, not just your numbers. *(DS1)*

## 7. Enemies (ENM)

*Each enemy is one of about 10 behavior **archetypes** with its own tuning, model and voice, which keeps 20 enemies achievable. Lv = base level, and Shadow Moon variants get +3.*

- [ENM-01] **Giant Rat** — Lv 1 · Vale, Crypts · Packs of 3–6, lunging bites, very weak alone. Teaches lock-on. *Voice: squeaks and hisses (SFX).* ⭐ *(OoT, MW, SK)*
- [ENM-02] **Grey Wolf** — Lv 2 · Wolfwood, Vale · Packs circle you and lunge from behind. The alpha howls to send the pack in. *Voice: growls and howls (SFX).* ⭐ *(TP, SK)*
- [ENM-03] **Goblin Cutthroat** — Lv 2 · Vale, Ashen · Fast, cowardly, runs away at low HP to fetch friends. Dagger feints. *Voice: shrill cackles, "Shiny! Mine!"* ⭐ *(SK, OB)*
- [ENM-04] **Bandit Brigand** — Lv 3 · Vale, roads · Sword and shield. Blocks, then counters. *Voice: gruff taunts ("Nice scarf. I'll take it.").* ⭐ *(SK, OB, DS)*
- [ENM-05] **Bog Ooze** — Lv 3 · Blackmire · Splits into two smaller oozes when cut. Fire burns it whole. *Voice: wet gurgles (SFX).* ⭐ *(OoT, TP)*
- [ENM-06] **Bandit Crossbowman** — Lv 4 · Vale, ruins · Keeps its distance, backs away, and reloads behind cover. *Voice: "Hold still!", "Reloading!"* ⭐ *(SK, DS)*
- [ENM-07] **Goblin Hexer** — Lv 4 · Vale, Ashen · Buffs nearby goblins and throws firebolts. Kill it first. *Voice: chanting gibberish.* ⭐ *(SK, OB)*
- [ENM-08] **Skeleton Warrior** — Lv 5 · Crypts, ruins · Pulls itself back together after a few seconds unless it's finished with blunt or radiant damage, or stomped. *Voice: bone rattles and a hollow moan.* ⭐ *(OoT, DS1, SK)*
- [ENM-09] **Giant Spider** — Lv 5 · Wolfwood · Drops from the canopy to ambush and spits webs that slow you. *Voice: chittering (SFX).* ⭐ *(SK, OoT, DS1)*
- [ENM-10] **Drowned Thrall** — Lv 6 · Blackmire · A zombie that rises out of the water, grabs and bites. Slow, but in groups. *Voice: drowned groans.* ⭐ *(SK, DS)*
- [ENM-11] **Harpy** — Lv 7 · Frostfang cliffs · Dive-bombs and shrieks to stun. Shoot it down with the crossbow. *Voice: shrieking cackles and mocking lines.* ⭐ *(NEW)*
- [ENM-12] **Lizardfolk Spearman** — Lv 7 · Blackmire · Long reach and thrust combos. Dives into water to get around you. *Voice: hissed words.* ⭐ *(OoT, OB)*
- [ENM-13] **Orc Berserker** — Lv 8 · Ashen, roads · Fights with two axes and enrages at low HP (glowing red, faster, but stops defending). *Voice: war cries.* ⭐ *(SK, OB)*
- [ENM-14] **Bog Troll** — Lv 10 · Blackmire · Regenerates unless hit by fire or radiant damage. Wide sweeping attacks. *Voice: grunts and a few dim words.* ⭐ *(SK, MW, OB)*
- [ENM-15] **Wraith** — Lv 11 · Crypts, night · Goes intangible between attacks. Only radiant damage, Rites or Awakening hit it while it's faded. *Voice: layered whispers.* ⭐ *(TP, SK)*
- [ENM-16] **Frost Yeti** — Lv 12 · Frostfang · Throws boulders, grabs, and beats its chest before charging. *Voice: roars (SFX).* ⭐ *(SK)*
- [ENM-17] **Ogre Brute** — Lv 13 · Frostfang, Ashen · Huge club, ground-pound shockwave, grab-and-throw. *Voice: slow and dim ("SMASH… little… hero.").* ⭐ *(OB, DS)*
- [ENM-18] **Werewolf** — Lv 14 · Wolfwood (night) · The classic cursed beast: leaps, fast claw strings, and howls to call wolves. Takes extra radiant damage. *Voice: snarls and broken speech.* ⭐ *(SK, TP)*
- [ENM-19] **Dread Knight** — Lv 15 · Roads, citadel approaches · The Dark Lord's elite soldier. Parries, ripostes, carries a tower shield, and fights in pairs. *Voice: cold and formal ("Kneel, peasant.").* ⭐ *(DS, NEW)*
- [ENM-20] **Runestone Golem** — Lv 16 · Ashen, ruins · Slow and heavily armored. Break its glowing rune weak points first. Immune to bleed. *Voice: grinding stone (SFX).* ⭐ *(TP, OoT, DS)*
- [ENM-21] **Mimic Chest** — Optional · Anywhere · A chest that bites. Tell it apart by the chain that faces the wrong way. *(DS)*
- [ENM-22] **Necromancer** — Optional · Crypts · Raises skeletons, teleports, and stays out of melee range. *Voice: arrogant monologues.* *(SK, OB)*
- [ENM-23] **Elite variants** — Any enemy can spawn as an **Elite** with a tint, +2 levels, one extra trait (fast, armored, vampiric) and double XP. *(SK, DS)*
- [ENM-24] **Behavior archetypes** — melee-basic, pack-circler, ranged-kiter, caster-support, flyer, ambusher, brute, regenerator, phaser and armored-weakpoint. A new enemy is just an archetype plus a JSON file. ⭐ *(DOC)*
- [ENM-25] **Telegraph language** — Every enemy uses the same cues: a white glint means you can parry, a red flare means you can't parry so dodge, and a deep sound means a grab. ⭐ *(DS, NEW)*

## 8. Bosses (BOS)

- [BOS-01] **Grimtooth, Alpha of the Wolfwood** — A giant werewolf. Phase 1 is a duel. In phase 2 he howls in wolves and leaps between trees. He shares the rig and animations of the Werewolf enemy (ENM-18), so he's cheap to build. **Recommended first boss.** ⭐ *(TP, SK)*
- [BOS-02] **The Brood Queen** — A massive spider in a web cathedral. She climbs walls and ceiling, spawns spiderlings and webs the arena, and her weak point is exposed while she's stuck in a web. *(OoT, DS1)*
- [BOS-03] **Old Mother Mire** — A bog hag riding a troll. Kill the troll's regeneration with fire, then fight the hag on foot as she teleports through swamp pools. *(OoT, SK)*
- [BOS-04] **The Frostfang Wyvern** — Fought on a cliff. Shoot its wings with the crossbow to ground it, then fight it on the ground with tail sweeps and frost breath. *(SK, DS)*
- [BOS-05] **The Cinder Colossus** — A giant golem in a magma forge. Climb its arm while it's stunned to break the rune core. *(OoT, TP)*
- [BOS-08] **Mist gates** — Boss arenas are sealed by a mist wall. Walking through it starts the music and the boss bar. Dying sends you back to the last Waystone. ⭐ *(DS)*
- [BOS-09] **Use the dungeon item** — Each boss's main weakness is the dungeon's new tool (for example, the grappling chain pulls the wyvern down). *(OoT, TP)*
- [BOS-10] **Sir Calder the Black** — The Dark Lord's champion (STY-19). A human duel, very technical: parries, feints, a cursed greatsword. He returns three times and gets stronger each time; the last duel can end in him being redeemed. *(DS, OoT)*
- [BOS-11] **Malgrath the Undying** — The final boss in the citadel's throne hall. Phase 1 is a sorcerer-king who duels and casts. Phase 2 is a towering monstrous form. In Phase 3 the Crown is restored and you fight him in a permanent Awakening. *(OoT, DS3)*

## 9. World & Biomes (WLD)

- [WLD-01] **One seamless heightmap world** — A map of about 4 × 4 km (16 km²), generated in Python (layered noise plus a biome mask PNG that can be painted by hand). It's streamed in chunks with LOD. ⭐ *(DOC)*
- [WLD-02] **Brackenvale (start)** — Rolling meadows, Rowan's burned home village, a ruined watchtower, standing stones and gentle slopes. Levels 1–5. ⭐ *(OoT, SK)*
- [WLD-03] **The Wolfwood** — Dense dark pine, fog, fallen giant trees, wolf dens, spider groves. Levels 4–10. ⭐ *(TP, SK)*
- [WLD-04] **The Blackmire** — Swamp: shallow water that slows you, stilt-huts, sunken ruins, drifting mist, lantern-flies. Levels 6–12. ⭐ *(OoT, MW, OB)*
- [WLD-05] **Frostfang Peaks** — Snowy switchbacks, cliffs, ice caves, a harpy roost, and blizzards that shorten sight lines. Levels 10–16. ⭐ *(SK, DS)*
- [WLD-06] **The Ashen Reach** — Volcanic badlands, lava cracks, obsidian spires, an orc warcamp and golem ruins. Levels 13–18. *(OoT, MW, DS)*
- [WLD-07] **The Sunken Crypts** — An underground network beneath the Vale, with skeletons, wraiths and a necromancer. Shortcuts open back to the surface. *(DS1, SK)*
- [WLD-08] **Duskhold, the Dark Lord's citadel** — A black fortress on a crag in the center of the map, under a permanent storm cloud. You can see it from anywhere. It's the final area and the compass of the whole world. ⭐ *(OoT, SK, DS)*
- [WLD-09] **Waystones** — Rest points that heal, refill flasks, respawn enemies, save the game, and let you upgrade weapons and fast travel between waystones you've lit. ⭐ *(DS)*
- [WLD-10] **Shortcuts that loop back** — Gates, ladders and elevators that you open from the far side, so the world folds back to your last Waystone. ⭐ *(DS1)*
- [WLD-11] **Day/night cycle and weather** — Day and night change spawns (wraiths and werewolves at night), lighting and fog. Each biome has its own weather. ⭐ *(MM, OoT, SK)*
- [WLD-12] **Scripted scatter** — Trees, rocks, grass, ruins and camps are placed with Poisson-disk sampling, using rules per biome (slope, height, density, clearings). ⭐ *(DOC)*
- [WLD-13] **One hand-picked landmark per area** — Each region has one set piece placed deliberately (the burned windmill, the troll bridge, the frozen giant), and generated land around it. ⭐ *(DOC)*
- [WLD-14] **Dungeons from a scripted kit** — Python generates modular walls, floors, stairs and arches. Dungeon layouts are short JSON grids assembled from them. *(DOC)*
- [WLD-15] **Dungeon tools that gate the world** — A grappling chain, a lantern of revealing (shows hidden paths), and iron boots (walk on lakebeds). Each opens new areas in the overworld. *(OoT, TP)*
- [WLD-16] **Hidden walls and secrets** — Hidden walls that one hit reveals, cracked walls you can bomb, and secret chests visible only through the Seer's Lens. *(DS, OoT)*
- [WLD-17] **Loot chests and loot tables** — Chests, corpses with loot and enemy drops, all from data-driven loot tables with rarity tiers. ⭐ *(SK, DS)*
- [WLD-18] **Ambient wildlife** — Deer, crows and rabbits that run from you, making the world feel alive at almost no cost. *(SK, OB)*
- [WLD-19] **Simple traversal** — Auto-jump at ledges and climbing on marked ledges. Deep water makes you drown and respawn nearby (swimming comes later). ⭐ *(OoT)*
- [WLD-20] **Pacing director** — A hidden system that watches HP, deaths and how long since the last fight, then adjusts ambushes, quiet stretches and Elite spawns. *(DOC)*
- [WLD-21] **World validators** — Automated checks: every Waystone can be reached, no spawns inside geometry, no slopes you can't climb on main paths, and a maximum distance between safe points. ⭐ *(DOC)*
- [WLD-22] **Fishing pond** — A later stretch goal: a relaxing fishing minigame at a lake hut. *(OoT, TP)*

## 10. HUD & UI (UIX)

- [UIX-01] **Minimal HUD** — HP, stamina and Valor bars top-left. Quick slots (flask, crossbow bolts, throwable) bottom-left. Essence count bottom-right. ⭐ *(DS)*
- [UIX-02] **Compass bar** — A compass across the top with markers for Waystones, discovered landmarks and Duskhold. *(SK)*
- [UIX-03] **Map and compass items** — Each dungeon's map and compass are items you find. They reveal its layout and its chests. *(OoT, TP)*
- [UIX-04] **Lock-on reticle and enemy plates** — The locked target gets a reticle. Damaged enemies show a small HP bar with their level. ⭐ *(OoT, DS)*
- [UIX-05] **Boss bar** — A name and a large HP bar at the bottom of the screen, which appears when you pass the mist gate. ⭐ *(DS)*
- [UIX-06] **Level-up screen** — Shows each attribute with live previews of how derived stats change (green or red) before you confirm. ⭐ *(DS)*
- [UIX-07] **Pause menu** — Inventory grid, equipment, stats and skills, map, bestiary, settings. ⭐ *(SK, OoT)*
- [UIX-08] **Bestiary** — Unlocks as you kill enemies: the model on a turntable, lore, weaknesses and a button that plays its voice line. Written as *The Lycantrope* field guide (STY-18). *(TP, SK)*
- [UIX-09] **Death screen** — *"AND SO THE LEGEND ENDED…"* fades in, then *"…or did it?"*, and you wake at your Waystone. ⭐ *(DS, NEW)*
- [UIX-10] **Subtitles for every voice line** — On by default, with a speaker name and a size setting. ⭐ *(DOC)*
- [UIX-11] **Controller and rebinding** — Xbox and PlayStation layouts through `pygame.joystick`, and fully rebindable keyboard and mouse. ⭐ *(DOC)*
- [UIX-12] **Comfort and accessibility** — FOV slider, camera shake and head-bob scaling, high-contrast telegraphs, a hold-or-toggle option for every hold input, and an optional assist mode. *(DOC)*
- [UIX-13] **UI drawn with pygame, shown through GL** — HUD and menus are drawn on a pygame Surface and uploaded as a texture each frame, so there's no extra UI library. ⭐ *(DOC)*
- [UIX-14] **Ember's subtitles look different** — Ember's lines appear in warm gold with a soft glow, so you always know when it's the sword talking. *(NEW)*

## 11. Audio & Voice (AUD)

- [AUD-01] **Voice pipeline** — `data/lines.csv` → `tools/voice/generate.py` (ElevenLabs API) → ffmpeg mastering → `assets/audio/vo/`. Re-runs are cached by a hash of the text and settings. ⭐ *(DOC)*
- [AUD-02] **Designed voices only** — Every voice is made with ElevenLabs Voice Design from a text description. No clones of real people. Voice IDs and settings are kept in `data/voices.json`. ⭐ *(DOC)*
- [AUD-03] **Enemy barks** — For each voiced enemy: spotting you (3), attack effort (4), pain (3), death (2), idle (2), with 2 or 3 takes each. The game picks a random take and never plays the same one twice in a row. ⭐ *(DOC, SK)*
- [AUD-04] **Expressive audio tags** — Tags like `[growls]`, `[laughs]`, `[whispers]` and `[shouting]` give barks and Ember more character. ⭐ *(DOC)*
- [AUD-05] **Creature sounds from the SFX API** — Squeaks, howls, chittering, roars, gurgles and grinding stone, generated with ElevenLabs Sound Effects. ⭐ *(DOC)*
- [AUD-06] **Combat SFX set** — Swings (light and heavy), impacts per material (flesh, metal, bone, stone, ooze), parry clang, rolls, footsteps per biome and the Awakening flare, all generated. ⭐ *(DOC)*
- [AUD-07] **Music for each biome** — Generated tracks (ElevenLabs Music) with an exploration layer and a combat layer that crossfade, plus a theme for each boss and a heroic main theme. *(OoT, SK)*
- [AUD-08] **Positional audio** — Pan and volume from distance and angle in pygame.mixer, plus a low-pass effect when the source is behind geometry (baked into variants). ⭐ *(DOC)*
- [AUD-09] **Signature jingles** — Short original stings for leveling up, parrying, lighting a Waystone and opening a chest. Players should come to listen for them. *(OoT, TP)*
- [AUD-10] **Loudness mastering** — Normalize loudness, trim silence and export to OGG Vorbis. Keep all takes outside the game folder. ⭐ *(DOC)*
- [AUD-11] **Pronunciation dictionary** — A single place to fix names (Malgrath, Aldmoor, Fenhallow, Greymantle) for every voice. *(DOC)*
- [AUD-13] **Awakening music swell** — When Awakening triggers, the combat track adds a heroic brass and choir layer for its duration. *(OoT, NEW)*

## 12. Art Pipeline (ART)

- [ART-01] **Meshy batch script** — `assets/manifest.json` (prompts, polycount targets, rig and animation requests) → `tools/meshy/batch.py` → preview → refine → remesh → download GLB. It's cached and can be resumed, and every model is logged to CREDITS.md. ⭐ *(DOC)*
- [ART-02] **Shared style suffix** — Every prompt ends with the same style line, e.g. *"stylized dark-fantasy, hand-painted textures, chunky readable silhouette, muted earthy palette, game-ready low-poly."* This keeps everything consistent. ⭐ *(DOC)*
- [ART-03] **Meshy auto-rig and animations for humanoids** — Rowan, bandits, goblins, orcs, skeletons, knights, the ogre and the werewolf go through Meshy's rigging and animation library: idle, walk, run, attacks, hit and death. ⭐ *(DOC)*
- [ART-04] **Procedural animation for non-humanoids** — Spiders, wolves, rats, oozes and harpies are animated in code (IK legs, sine gaits, squash and stretch). Meshy's auto-rig targets humanoids. ⭐ *(DOC)*
- [ART-05] **Image → 3D for hero assets** — Make concept images first (Meshy's image generation or your own sketches), then use image-to-3D for Rowan and the bosses to get better consistency. *(DOC)*
- [ART-06] **Polygon and texture budgets** — Props 300–2k triangles, enemies 5–15k, Rowan and bosses up to 25k. Textures 512–2048 px. Meshy's remesh enforces the targets. ⭐ *(DOC)*
- [ART-07] **Python normalizer (no Blender needed)** — A `trimesh`/`pygltflib` script that fixes scale (1 unit = 1 m), forward axis, pivot at the feet, makes LODs by decimation and builds collision capsules and boxes. ⭐ *(DOC)*
- [ART-08] **Procedural terrain textures** — Grass, dirt, rock, snow, mud and ash made with numpy noise (albedo and normal), blended by slope, height and the biome mask with triplanar projection. ⭐ *(NEW)*
- [ART-09] **Procedural sky** — A shader gradient and sun (built), with a moon, stars and Duskhold's storm cloud to come. Colors and sun position live in `data/world/sky.json`. No texture assets needed. ⭐ *(NEW)*
- [ART-10] **Instanced grass with wind** — Grass blades generated by GPU instancing and moved by wind in the shader, with density from the biome mask. ⭐ *(NEW)*
- [ART-11] **Scripted modular dungeon kit** — Python builds wall, floor, arch, stair and pillar meshes from parameters, then Meshy's AI texturing gives them surfaces. *(DOC)*
- [ART-12] **Post-processing stack** — Height fog, bloom, ACES tone mapping, vignette, and color grading for each biome from LUTs generated by script. ⭐ *(DOC)*
- [ART-13] **GPU particles** — Sparks, blood (with a toggle), embers, snow, fireflies and spores as instanced quads. Particle textures are drawn with numpy. ⭐ *(NEW)*
- [ART-14] **Auto-rendered item icons** — Item GLBs are rendered offscreen with moderngl to make inventory icons automatically. *(DOC)*
- [ART-15] **Unifying shading** — Soft toon ramp, rim light and shared fog so that AI models in slightly different styles still look like they belong together. ⭐ *(DOC)*
- [ART-16] **Asset previewer** — A small tool that shows each Meshy result on a turntable next to Rowan for scale, with Accept, Reject and Re-roll buttons (same approach as the idea tracker). *(DOC)*
- [ART-17] **Dawnblade stages** — Four versions of the sword model (rusty → restored → glowing → Awakened), plus an emissive glow driven by a shader uniform. ⭐ *(NEW)*
- [ART-18] **Painted skybox** — A hand-painted-looking sky panorama, painted by `tools/worldgen/skybox.py` from `data/world/sky.json`: soft color bands, brushy two-tone clouds, and the sun exactly where the game's light comes from. Distant fog and water reflections take their colors from the painting. *(Tried and removed on 2026-11-24; the procedural sky, ART-09, looked better.)* ⭐ *(NEW)*
- [ART-19] **Rite effects as Meshy meshes** — Instead of particles (ART-13 was denied), each visual effect is a small Meshy mesh, such as a burst, a dome or a floating sigil. The game animates it in code (scale, spin, fade) and draws it with a glowing, see-through shader. The same approach covers fire on torches, campfires and braziers. The meshes are listed in OBJECTS.md under Effects (VFX). ⭐ *(NEW)*

## 13. Engine & Tech (TEC)

- [TEC-01] **pygame-ce instead of pygame** — A drop-in fork (`import pygame` still works) that's actively maintained and has relative mouse mode, better performance and newer SDL. ⭐ *(DOC)*
- [TEC-02] **moderngl on OpenGL 3.3 core** — A single GL context from pygame and shaders in `.glsl` files that hot-reload in dev builds. ⭐ *(DOC)*
- [TEC-03] **PyGLM for math** — Fast vec, mat and quat types for gameplay, with numpy for bulk work (terrain, skinning palettes, particles). ⭐ *(NEW)*
- [TEC-04] **Fixed 60 Hz simulation and interpolated rendering** — Stable frame data and parry windows at any frame rate. ⭐ *(DOC)*
- [TEC-05] **Simulation doesn't touch rendering** — Gameplay state never calls the renderer. The renderer, audio and UI read state and react to events. ⭐ *(DOC)*
- [TEC-06] **Event bus** — Events like `Hit`, `Parried`, `Died`, `LevelUp` and `Awakened` drive SFX, VFX, barks, subtitles and the HUD. ⭐ *(DOC)*
- [TEC-07] **Content as data, with hot reload** — Enemies, attacks, items, loot, biomes and the XP curve live in JSON. Pressing F5 in dev reloads them without restarting. ⭐ *(DOC)*
- [TEC-08] **GLB loader with GPU skinning** — `pygltflib` reads meshes, skins and animations. Joint matrices go to the vertex shader through a uniform buffer, with crossfades between clips. ⭐ *(DOC)*
- [TEC-09] **Light collision** — Character capsules collide with the heightmap and with simple static colliders (spheres, capsules, oriented boxes) through a spatial hash. No physics engine. ⭐ *(DOC)*
- [TEC-10] **Terrain chunks with LOD and culling** — 64 m chunks with 3 LOD levels and frustum culling, and skirts to hide cracks between chunks. ⭐ *(NEW)*
- [TEC-11] **Instanced rendering** — One draw call per prop type per chunk, so thousands of trees and rocks stay cheap. ⭐ *(DOC)*
- [TEC-12] **Shadow map** — One shadow cascade that follows the player, with PCF filtering. Distant shadows fade into fog. ⭐ *(NEW)*
- [TEC-13] **Enemy AI** — A finite state machine for each archetype (idle, patrol, alert, approach, strafe, attack, recover, stagger, flee, dead) with utility scores for picking attacks. Steering on terrain, and grid A* in dungeons. ⭐ *(DOC)*
- [TEC-14] **Activation radius** — Only enemies within about 80 m run their full AI. Farther ones sleep, which keeps Python within its budget. ⭐ *(NEW)*
- [TEC-15] **Seeded RNG and input replays** — One seeded RNG, plus recording of inputs per tick, so bugs can be replayed exactly. *(DOC)*
- [TEC-16] **Save system** — JSON saves (stats, inventory, Waystones lit, bosses killed, shortcuts opened, position) with versioned migrations. ⭐ *(DOC)*
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
