# Boss Fights

This file plans the boss fights for both versions of the story:
- **V1:** the portal story in [STORY.md](STORY.md).
- **V2:** the *Dream-Quest* story in [STORY_V2_IDEAS.md](STORY_V2_IDEAS.md).

Many bosses appear in both versions; §4 shows which. Creature bases come from [CREATURES.md](CREATURES.md). The combat systems (Quickstep, Reclaim, Severance) are in [THE_DREAMLANDS.md](THE_DREAMLANDS.md) §12, and Sanity, Insight and Anchors are in §3 and §11.

---

## 1. Rules for every boss

1. **One idea per boss.** Every boss teaches or tests one thing:
   - Light against ghasts.
   - Parrying a dive.
   - Breaking a chant.
   - Choosing *not* to fight.
   
   Write that idea down before building the fight.
2. **Telegraph everything.** Big attacks have a visible wind-up (an animation, a glow, a sound and a Mindspeak hint), and the wind-up is the **Severance window**.
3. **Phases by health.** Phases change at roughly 66% and 33% health. Each change gets a short beat: a roar, a voice line, or a change in the arena. The boss is invulnerable for 1–2 s during it, so phases can't be skipped.
4. **Allies matter.** Morrowind's AI is simple, so bosses get hard from the arena and the mechanics, not from the AI being clever. Named allies (Captain Thorne, Pickman, the cats) can help, but **they never die in a boss fight unless the story says so**.
5. **Horror costs Sanity, not health only.**
   - Every boss has a **Reveal** moment that costs Sanity (the first sight of it, or a phase change).
   - Killing the boss lets you **Resolve-Reclaim** some of that Sanity back (§12).
6. **Not every boss is a kill.** Some fights are won by surviving, sealing, escaping, submitting or sparing. Say so in the Mindspeak hints, so players don't feel cheated.
7. **Fair retries.** A checkpoint just before the arena door, a short walk back, and no long unskippable scenes on retry.
8. **Morrowind limits:**
   - Scaled-up creatures get stuck: big bosses need **open, flat arenas** with simple collision.
   - Flying is limited to cliff-racer-style AI. Dives and swoops are **scripted moves** (MWSE moves the actor), not real flight pathing.
   - Every arena needs a pathgrid.

### Level guide

| Range | V1 | V2 |
|---|---|---|
| Levels 1–4 | Prologue, Incursion 1 | Acts 1–2 |
| Levels 5–10 | Incursion 2, Kingsport (end of the demo) | Act 3 (end of the demo) |
| Levels 10–18 | Enchanted Wood → Underworld | Acts 4–6 |
| Levels 18–25 | Leng → Serannian | Acts 7–8 |
| Final | Kadath, the Drowned Coast | Kadath |

---

## 2. V1 bosses (STORY.md)

| # | Boss | Where | Type | Demo? |
|---|---|---|---|---|
| 1 | The Thing in the Cellar | Pell's shop, Arkham | Tutorial | ✓ |
| 2 | The Unwritten Gate | The old burying-ground, Arkham | Seal under pressure | ✓ |
| 3 | Old Corwin of the Pike *(optional)* | Aylesbury Pike | Bandit chief | ✓ |
| 4 | The Apprentice at the Stones | The stone circle above Dunwich | Break the chant; the boss escapes | ✓ |
| 5 | **The Shantak Rider** | The cliff-top, Kingsport | **Demo final boss** | ✓ |
| 6 | The Hostage-Keeper | Moon-beast camp, the Enchanted Wood | Rescue | |
| 7 | The Factor of Dylath-Leen | Dylath-Leen docks | Chase | |
| 8 | The Night-Gaunts of Ngranek | Ngranek | Don't fight | |
| 9 | The Gug Warlord | The war beside the Vaults of Zin | Giant | |
| 10 | The High Priest Not to Be Described | The monastery of Leng | Duel, then a reveal | |
| 11 | The Wound over Serannian | Fallen Serannian | Endurance seal | |
| 12 | Nyarlathotep | Kadath | Temptation (dialogue boss) | |
| 13 | **The Night of the Rising Star** | The Drowned Coast, thirty years ago | **Final boss**: spare the priest | |

**Post-game / sequel:** R'lyeh Rising (THE_DREAMLANDS.md §14.7), set up by the epilogue.

### V1-1. The Thing in the Cellar (tutorial)
- **Story:** the prologue's "chase something out of the cellar." It's a rat swollen to the size of a dog, fat from eating the shop's tallow.
- **Idea:** teaches attacking, Quickstep and Reclaim.
- **Fight:**
  - One phase. Its lunge has a long, obvious wind-up; dodge it, then hit back to Reclaim.
  - At 50% it knocks over a lamp, and you learn to step out of fire.
- **Reward:** Pell's grudging praise; 5 gold "for the tallow."
- **Build:** **Rat** scaled ×2.5 with a greasy texture.

### V1-2. The Unwritten Gate (first incursion)
- **Story:** the sky above the burying-ground opens; zoogs and Leng raiders pour out; Pell falls. You make the Sign three times: you fail, you hold, then you seal it.
- **Idea:** sealing while under attack, with allies.
- **Arena:** the hilltop burying-ground, with tilted headstones as cover. Captain Thorne's Watch line holds the bottom of the hill.
- **Phases:**
  1. **The climb:** fight up the hill through zoog swarms. The Watch keeps raiders off your back as long as you stay near the line.
  2. **First Sign (scripted failure):** the channel bar fills to 40%, then the gate throws you down. The Archsage says: *"Again. It knows your name now; let it."*
  3. **Second Sign:** a **Leng Raid-Captain** steps out and keeps interrupting your channel. Kill him or Severance him to stagger him, then channel.
  4. **Third Sign:** zoogs only, at full speed. Hold the channel while the Watch closes in around you.
- **Sanity:** standing at the gate drains Sanity slowly (the "voices speaking your name").
- **Reward:** the Watch's respect (faction), the Raid-Captain's curved blade, Pell's survival.
- **Build:** the gate is a VFX activator. The zoogs are **Scamps** scaled ×0.5; the Raid-Captain is a **Man of Leng** NPC.

### V1-3. Old Corwin of the Pike (optional bandit boss)
- **Story:** bandits got bold on the Aylesbury Pike while the Watch was busy elsewhere.
- **Idea:** a plain human duel that rewards Severance. A palate cleanser between horrors.
- **Fight:**
  - Corwin fights with a buckler and a falchion, with two crossbowmen on a ridge.
  - He **parries back**: hitting his raised buckler staggers *you*.
  - At 33% he calls for terms. Spare him (he becomes a fence in Arkham) or finish him.
- **Reward:** the bandits' stash, plus a road-safety quest for the Watch.

### V1-4. The Apprentice at the Stones (Dunwich)
- **Story:** ghasts and hooded valley cultists keep a gate open inside a stone circle. Their leader is the Archsage's old apprentice, who speaks *through your ears* to the Archsage, then escapes through the gate, laughing.
- **Idea:** light against darkness, and a boss you can't kill yet.
- **Arena:**
  - A ring of standing stones on a hilltop at night.
  - **Four cult fires** feed the gate.
  - **Six empty braziers** sit around the slope, with Dunwich farmers carrying torches below.
- **Phases:**
  1. **The pack:** ghasts leap in from the dark. Light braziers (activate them with a torch) to make zones they can't enter. Ghasts caught in light **burn and die**.
  2. **The chant:** the Apprentice stands at the gate behind a ward. **Put out the four cult fires**, each guarded by a cultist, to drop his ward.
  3. **The duel:** he fights with the Archsage's old priesthood magic: a drowning curse (stand still and you take damage) and a sickly-green bolt. He hijacks Mindspeak, so his lines replace the Archsage's hints with lies; one hint is deliberately wrong.
  4. **The escape:** at 50% he steps through the gate. Seal it behind him before the next pack arrives.
- **Sanity:** big loss when the hijacked Mindspeak reveal hits. You can't win it back, because he doesn't die here.
- **Reward:** his dropped prayer-book, the clue that the gates are opened from inside, and the farmers' trust.
- **Build:** the ghasts are **Guars** with new pale, noseless heads (Meshy); the cultists are Sixth House robe NPCs.

### V1-5. The Shantak Rider (demo final boss)
- **Story:** a black galley comes down over Kingsport; three gates open; the Moon-beast overseer comes down on a Shantak to finish things on the cliff below the Strange High House.
- **Idea:** everything the demo taught, plus fighting something in the air.
- **Arena:**
  - The bare cliff-top: wide, flat, with a sheer drop on two sides.
  - The galley hangs overhead in the mist, and the High House's lit windows are behind you.
  - **Three ballista emplacements** (Watch siege crossbows), and a Watch line holding the harbour stairs.
- **Phases:**
  1. **In the air (100–66%):**
     - The Shantak circles out of reach, then **dives** in a straight line. The dive has a clear wind-up: a horse-scream and a shadow on the ground.
     - Quickstep out of the line, or hit it with a crossbow bolt or Severance during the wind-up to **ground it** for 5 s.
     - A ballista shot stuns it for longer, but you have to reload it between dives.
  2. **On the ground (66–33%):**
     - The wounded Shantak crashes and fights on foot with beak sweeps and wing buffets that push you toward the cliff edge.
     - The **overseer dismounts** and fights alongside it.
     - Moon-beasts **swell and shrink**:
       - **Swollen:** big, slow, armoured sweeps.
       - **Shrunk:** fast, and vulnerable to criticals.
       
       Read the shape and punish the shrunk form.
  3. **The last stand (33–0%):**
     - The Shantak tries to take off with its rider.
     - Ground it one last time, or use the **Black Tongue**: one word grounds the Shantak instantly, at a heavy Sanity cost, with the Archsage's voice going wet and strange.
     - The Shantak falls into the sea; the overseer fights alone and desperate.
- **After:** the sky clears except for the one huge gate out at sea that won't seal. Fallen Serannian is visible through it. *End of the demo.*
- **Sanity:** the Reveal costs Sanity when the overseer first shows its face of pink feelers. Killing the overseer Resolve-Reclaims it.
- **Reward:** the Overseer's Goad (a weapon that stuns Moon-beasts), a Shantak scale (crafting), and the end-of-demo screen.
- **Build:**
  - **Cliff Racer** scaled ×4–5 with a Meshy horse head.
  - **Ascended Sleeper** body for the overseer.
  - A rider mesh attached to the Shantak's spine bone in phase 1, swapped for two separate actors in phase 2.

### V1-6. The Hostage-Keeper (Enchanted Wood)
- **Story:** the Moon-beasts burned part of the wood and took every third zoog as a hostage. You free them instead of taking revenge.
- **Idea:** a rescue where how you play changes the fight.
- **Fight:**
  - A camp of cages. The Keeper is an elite Moon-beast with a fire-pot.
  - **Every cage you open before the fight** adds zoogs who swarm the Keeper during it.
  - **Stealth route:** open them all quietly, and the Keeper fights alone and panicking.
  - **Loud route:** the Keeper sets the cages alight, and you must put them out or lose hostages, which lowers zoog standing.
- **Reward:** the zoog council's passage, and zoog paths that act as fast travel in the wood.

### V1-7. The Factor of Dylath-Leen
- **Story:** the black galleys trade rubies again, and their hooded factor is the Apprentice, who escapes by water.
- **Idea:** a chase. He keeps escaping, and you learn who he is.
- **Fight:** a running chase across the docks.
  - He drops ruby-bribed thugs behind him.
  - He throws a cursed ruby: whoever picks it up turns on you, so don't pick it up, or Dispel the charmed NPC.
  - It ends at the water with him boarding a galley's boat.
  - Optional: a perfect run (no thugs killed, no ruby touched) wins a **parting word** from him: a lore clue about Leng.

### V1-8. The Night-Gaunts of Ngranek (a non-fight)
- **Story:** you climb Ngranek by night and **let the night-gaunts take you** instead of fighting.
- **Idea:** the bravest choice is not to fight.
- **Mechanic:**
  - The gaunts come silently, and ambient sound drops out.
  - **Fighting back:** they're numerous, endless and tickle-stunning, and you eventually fall from the mountain. That's a "death" with a hint.
  - **Lowering your weapon:** they carry you down into the Vale of Pnath, in a scripted flight with a heavy Sanity cost.
  - Mindspeak hint: *"Nodens' creatures serve no one we fight. Let them carry you."*

### V1-9. The Gug Warlord (the war in the dark)
- **Story:** nine nights of war beside the Vaults of Zin. The ghouls' price for the Sky Road tablet is help against the gugs and the ghasts.
- **Idea:** a giant you beat by using the terrain.
- **Arena:**
  - A field of cyclopean round towers.
  - **Narrow ghoul tunnels** around the edge where the gug can't follow.
  - **Hanging boulders** that ghouls can cut loose.
- **Phases:**
  1. **The hunt:** the Warlord stalks the field. Its vertical mouth opens with a long wind-up for a bite that kills outright. Its split forearms strike four times; dodge the fourth.
  2. **Tunnel war:** hide in the tunnels, where it reaches in with one arm. Hit the arm (a weak point) to stagger it.
  3. **The drop:** lead it under the boulders and signal Pickman's ghouls to cut them; then finish it.
- **Side wave:** ghasts pour in from the Vaults when the gug falls. Light the ghoul lamps.
- **Reward:** the Sky Road tablet; Pickman's promise ("we will come with you").
- **Build:** **Ogrim** scaled ×1.8 with a Meshy vertical-mouth head and doubled forearms.

### V1-10. The High Priest Not to Be Described (Leng)
- **Story:** at the end of the painted passage the priest sits on a golden throne. It wears the Apprentice's robes and makes the old priesthood sign with the Apprentice's hand. **When the mask is struck away, there is nothing behind it but darkness.**
- **Idea:** a duel against a recurring villain who has already been consumed, with a reveal.
- **Arena:**
  - The throne room. The walls show Leng's history in murals.
  - **The murals move during the fight**, and their scenes warn which attack is coming next.
- **Phases:**
  1. **The priest:** uses the Apprentice's old spells (from V1-4), now stronger. The Mindspeak hijack returns. Learn to ignore it.
  2. **The mask:** a Severance aimed at the head can **knock the mask loose**. You get one chance per phase.
  3. **What's behind it:** once the mask is off, the robes keep fighting with nothing inside.
     - Its attacks come from wherever you're *not* looking.
     - High Insight lets you see a faint outline.
     - Strike the empty robes until they collapse.
- **Sanity:** a severe Reveal at the unmasking.
- **Reward:** the yellow silk mask (an artifact: wearing it lets Men of Leng mistake you for one of their own, at a Sanity cost over time); the Archsage's grief scene.

### V1-11. The Wound over Serannian (endurance seal)
- **Story:** you walk the Sky Road into fallen Serannian and seal the great gate. It takes a night and a day. Voices pull you back: Pell, Thorne, the Collegium bells.
- **Idea:** the climax of the sealing mechanic, tied to **Anchors**.
- **Fight:**
  - A long channel (about 4 minutes of real time) on the harbour terrace.
  - **Waves** of Moon-beasts and Men of Leng attack while you channel.
  - Allies arrive in scripted beats: cats on the Moon (the sky darkens with them), then ghouls riding night-gaunts.
  - **Your mind sinks:** at set points the screen darkens and Sanity drops sharply.
    - Glowing **Anchor points** appear on the terrace, each with a voice: Pell grumbling about the shutters, Thorne ordering the line, the Collegium bells.
    - Touch an Anchor to recover, but it means breaking the channel briefly.
    - Anchors you sacrificed earlier in the game **don't appear**, which makes this fight harder.
- **Win:** the gate closes and the black drains out of Serannian's marble from the highest tower down.
- **Reward:** Kuranes' gratitude; Serannian becomes a hub.

### V1-12. Nyarlathotep (temptation)
- **Story:** in Kadath's onyx hall the Pharaoh-faced god offers you the dream-city forever. You refuse by choice: *"I only dreamed it. I live in Arkham."* He laughs and pushes you through a door in the air.
- **Idea:** a boss fought with conviction, not steel.
- **Mechanic: a dialogue duel.**
  - He makes **three offers**, each tailored to your journal: the faction you served best, the Anchor you lost, the companion who died.
  - Each offer **pulls Sanity down** over time while you think.
  - Answer with **Anchors and memories** gathered in the game (dialogue topics unlocked by earlier deeds) to push him back.
  - If you run out, a final **Composure check** decides.
  - If you **accept**, you get the dark ending.
- **Optional (high Insight only):** you can draw your sword on him. He doesn't fight back. He takes on one of the forms from §14.7 and the hall *unmakes* around you. Survive 60 s. It's a Sanity endurance fight that leads to the same door, plus a secret journal entry.

### V1-13. The Night of the Rising Star (final boss)
- **Story:**
  - The door opens thirty years into the past, on the outermost reef of the Drowned Coast.
  - A young priest of Cthulhu, **the Archsage**, stands in a ring of stones with a knife. The sea is swelling with something rising.
  - If you do nothing, the Sleeper wakes. If you kill him, the whole story unravels.
  - **You spare him:** *"Not yet. You will be needed."*
- **Idea:** the final fight is won by **not** killing, the opposite of every instinct the game has trained.
- **Arena:** the reef at night. A ring of stones, a rising tide, and a sky with one star rising.
- **Phases:**
  1. **The chant (reused from R'lyeh Rising):**
     - Cultists chant at **four stones**, and the tide rises with every verse.
     - Break each chanter before the verse ends, or the reef floods (less room, and drowned stones).
  2. **The priest:**
     - The young Archsage fights with the full **Black Tongue**, the same word he once taught you.
     - **Use it back on him** (a heavy Sanity cost): it staggers him, because it's *his* word.
     - At 10% health he drops to his knees. **The finishing prompt is "Spare"**, not "Kill." Attacking him again kills him and leads to the **paradox ending**: the screen unravels into the title screen, with a single journal line.
  3. **What was rising:**
     - Ropy limbs of the thing in the sea (Star-spawn) break the surface and lash the reef.
     - Make **the Sign**, the very first spell, at the centre of the circle while dodging the limbs, to push it back down. This is the sealing mechanic's last use, against the thing the Archsage once served.
- **Ending:** the circle breaks; you plant Pell's sword in the sand; *"Not yet. You will be needed."* Then the epilogue.
- **Build:** the young Archsage is an NPC; the limbs are **Ascended Sleeper** tentacle meshes scaled up, as scripted hazard actors.

---

## 3. V2 bosses (STORY_V2_IDEAS.md)

| Act | Boss | Where | Type | Demo? |
|---|---|---|---|---|
| 1 | The Sleepwalker's Shape | The Collegium cellars, Arkham | Tutorial (light and waking) | ✓ |
| 2 | The Gatekeepers' Trial *(optional)* | The Cavern of Flame | Test, not a kill | ✓ |
| 2 | Grandmother Zoog | The Moon-tree, the Enchanted Wood | Fight or talk | ✓ |
| 3 | The Ruby Factor | Dylath-Leen | Mini-boss (charm) | ✓ |
| 3 | **The Shantak Rider** | The Moon's docks | **Demo final boss**, with the cats' rescue | ✓ |
| 4 | The Drum-Master's Galley | Baharna harbour, Oriab | Ship siege | |
| 4 | The Night-Gaunts of Ngranek | Ngranek | Don't fight | |
| 5 | The Gug Sentinel of Koth | The Tower of Koth | Chase, then a giant | |
| 6 | The Shantak Roost | The mountains north of Inganok | Scare them off, then a matriarch | |
| 7 | The High Priest Not to Be Described | The monastery of Leng | Duel, then a reveal | |
| 8 | **The Moon-Beast Admiral** | The flagship over fallen Serannian | War battle | |
| 9 | **Nyarlathotep / the Flight to Azathoth** | Kadath and the void | Final: temptation, then escape | |

**Optional:** The Martense Den (Lurking Fear, Arkham hills), Hatheg-Kla (the Other Gods), the Quarry of Inganok, Kuranes' Dream.

### V2-1. The Sleepwalker's Shape (Act 1 tutorial)
- **Story:** the nightmare sickness spreads in Arkham. In the Collegium cellars, a sleepwalking scholar's nightmare has **taken flesh**.
- **Idea:** teaches the **waking** mechanic and light, before the player ever enters the Dreamlands.
- **Fight:**
  - The Shape is shadowy and half-real. Your weapons barely hurt it.
  - The Archsage, met hours earlier, tells you over Mindspeak to **wake the sleeper**: ring the cellar bell, splash water, or shout.
  - Each time the scholar stirs, the Shape thins and becomes hittable for a few seconds.
  - Lamps keep it at bay.
- **Reward:** the Archsage formally takes you as a student; the Collegium training montage begins.
- **Build:** **Ancestor Ghost** retextured as smoke.

### V2-2. The Gatekeepers' Trial (Act 2, optional)
- **Story:** **Nasht and Kaman-Thah**, the priests of the Cavern of Flame, never let an unworthy dreamer pass.
- **Idea:** they test you with a **conjured echo of your own fighting style** (a copy of your last-used weapon and spells).
- **Fight:** a mirror duel. It copies your most-used attack, so vary your approach.
- **Reward:** their blessing (+1 Insight) and a shortcut down the seven hundred steps.
- **Note:** you can skip it by answering their riddle in dialogue instead.

### V2-3. Grandmother Zoog (Act 2)
- **Story:** the zoogs' council meets beneath the great tree that, according to the book, reaches the Moon. Their eldest decides whether you pass.
- **Idea:** a boss you can **talk down**. Every choice changes the zoogs' attitude toward you for the rest of the game.
- **Talk route:** win three exchanges using what you learned in the wood: who's at war with the cats, which zoogs the Moon-beasts took. The zoogs then become allies.
- **Fight route:**
  - She stays high in the tree and sends **waves of zoogs** while dropping beehive-like nests.
  - **Climb the tree** in three levels to reach her.
  - Winning makes the zoogs hostile for the rest of the game. **Cats approve.**
- **Reward:** either zoog paths (fast travel) or zoog-bone charms.

### V2-4. The Ruby Factor (Act 3 mini-boss)
- **Story:** in occupied Dylath-Leen, a turbaned Man of Leng buys slaves with rubies for the black galleys. This is the book's merchant with the ruby.
- **Idea:** **charm and corruption** instead of raw damage.
- **Fight:**
  - The factor's ruby **charms nearby townsfolk** to fight for him.
  - **Break the ruby**: Severance his raised hand when he lifts it to charm. Otherwise you must deal with a growing mob you don't want to kill.
  - Killing charmed townsfolk costs reputation and lowers the city's War-state.
- **Twist:** win, and he **drugs you at the victory feast** (a scripted capture), so you wake on the galley.
- **Reward:** the factor's ledger (evidence against the collaborators); later, the resistance faction.

### V2-5. The Shantak Rider (Act 3, demo final boss)
- **Story:**
  - You wake stripped of gear aboard a black galley sailing up to the Moon.
  - You break free in an **escape sequence** using improvised weapons: grab your gear from the galley's hold, as in Morrowind's prison-ship opening.
  - You fight across the Moon-beasts' docks.
  - The overseer comes down on its Shantak.
- **Fight:**
  - Same three phases as **V1-5** (air, ground, last stand), with the arena moved to the **Moon's docks**: grey fungus-stone, black galleys at moor, and Earth overhead.
  - **The cats' rescue** replaces the ballistae. In phase 1, the **cats of Ulthar leap onto the Moon** in waves.
  - In the air phase, cats **cling to the Shantak** and drag it down, the way the ballista shots did in V1.
  - The more you helped cats earlier (the Ulthar quests), the more cats come.
- **Reward:** the Overseer's Goad; the cats carry you home. *End of the demo.*

### V2-6. The Drum-Master's Galley (Act 4)
- **Story:** Baharna on Oriab is under siege from the sea; a black galley leads the attack.
- **Idea:** a **ship boss**, fought by boarding.
- **Phases:**
  1. **On the walls:**
     - Repel boarding ladders and Men of Leng.
     - Fishermen offer **fire-ships**. Guide one (escort it along the harbour) into the galley to open a breach.
  2. **Boarding:**
     - Cross onto the galley. The **Drum-Master**, a Moon-beast beating the rowing drum, **buffs** every enemy aboard while the drum sounds.
     - Fight up the deck to reach it.
     - Cut the drum's straps (an activator) to end the buff.
  3. **The Drum-Master:** it uses the swell/shrink pattern from V1-5, plus an overboard grab you must dodge, or swim back.
- **Reward:** Baharna is Free again (War-state); Oriab's harbour opens; the route to Ngranek.

### V2-7. The Night-Gaunts of Ngranek (Act 4)
Same as **V1-8**: the bravest choice is to let them carry you.

### V2-8. The Gug Sentinel of Koth (Act 5)
- **Story:** in the book, the way up from the Underworld runs through the gugs' city and up the giant steps of the **Tower of Koth**, past a sleeping gug sentinel.
- **Idea:** a **stealth chase** that turns into a giant fight.
- **Phases:**
  1. **Sneak:** cross the gug city with ghoul guides. Noise wakes gugs.
  2. **The chase:**
     - The Sentinel wakes on the Tower's giant steps.
     - Climb (each step is a ledge), while it pursues. Ghasts attack it *and* you.
     - The book's ghasts-vs-gugs fight becomes a **three-way brawl** you can exploit.
  3. **The Sentinel at the top:**
     - The same pattern as V1-9: the vertical-mouth bite and the four-strike combo.
     - Its arm reaching through the trapdoor at the top is the weak point.
     - Slam the stone trapdoor on it to finish it.
- **Reward:** the ghouls' friendship (faction); you reach the Enchanted Wood again from below.

### V2-9. The Shantak Roost (Act 6)
- **Story:** the mountains north of Inganok are full of Shantaks. In the book, **Shantaks fear night-gaunts**.
- **Idea:** use what you learned earlier, not raw damage.
- **Fight:**
  - A flock of Shantaks on a high ledge.
  - **Sound the ghouls' night-gaunt call** (learned in Act 5) to make the flock flee in panic, which leaves only the **Roost-Matriarch**, too old and big to fly far.
  - Without the call, the flock dives at you endlessly.
  - **The Matriarch:**
    - She fights on the ledge with wing buffets toward the drop.
    - Her eggs hatch into small Shantaks if left alone; smash the eggs.
- **After:** you're exhausted and are **captured in Inganok** by the Ruby Merchant's agents (a cutscene) and carried to Leng.
- **Reward:** a Shantak egg (a quest item: hatch it for a mount in the epilogue, as an optional thread).

### V2-10. The High Priest Not to Be Described (Act 7)
- Same as **V1-10** (moving murals, knocking the mask loose, empty robes).
- In V2, what's under the robes depends on the premise chosen in STORY_V2_IDEAS §3:
  - **The Apprentice:** Armitage's pupil, turned by Nyarlathotep.
  - **Nothing:** the reveal is the emptiness.
  - **Premise C:** a clue to Carter's fate.

### V2-11. The Moon-Beast Admiral (Act 8)
- **Story:** the war in the sky. You lead your allies against **fallen Serannian**, where the Admiral commands from a flagship moored above the city.
- **Idea:** the **payoff for every faction** you befriended. A battle where your choices show up.
- **Phases:**
  1. **The assault:**
     - Fight across Serannian's black terraces toward the flagship.
     - **Call an ally once per phase** with a Power:
       - cats (swarm),
       - ghouls riding night-gaunts (carry you to a higher terrace),
       - Celephaïs knights (shield wall),
       - zoogs (sabotage: a galley's mooring cut loose),
       - Inganok quarrymen (break a barricade).
     - Missing factions mean fewer options.
  2. **The flagship deck:** the Admiral fights with the swell/shrink pattern plus a **command shout** that brings Men of Leng in. Kill the signal-drummers to stop the reinforcements.
  3. **The rigging:**
     - The flagship starts to sink through the clouds.
     - The Admiral retreats to the Shantak hangar at the stern.
     - Finish it before the deck tilts past saving, or ride the ghouls' night-gaunts off at the last second.
- **Win:** the black drains from Serannian's marble; War-states across the Dreamlands flip toward Free.
- **Reward:** Kuranes' crown-blessing; Serannian becomes a hub.

### V2-12. Nyarlathotep and the Flight to Azathoth (Act 9, final)
- **Story (the book's ending):**
  - Nyarlathotep receives you in Kadath. He tells you the truth: the sunset city is **your own memory of Arkham**.
  - He sends you off on a Shantak supposedly bound for it, but really bound for **Azathoth**.
  - You realise in time and leap.
- **Phase 1: the temptation (as in V1-12):**
  - Three offers, Sanity pressure, and answers from your **Memories** (gathered from good deeds in Arkham; STORY_V2_IDEAS §9).
  - Accepting leads to the dark ending.
- **Phase 2: the flight:**
  - A scripted Shantak ride through the void.
  - You steer weakly (left, right, up, down) toward **sunset lights**, each a Memory you earned: the shop, the river barges, a child's drawing.
  - Each light you reach restores Sanity.
  - **The piping of Azathoth** grows louder and drains Sanity faster.
- **Phase 3: the leap:**
  - When the last Memory is reached, Mindspeak (or Pell's voice, if the Archsage is gone) says *"Now."*
  - Jump off the Shantak into the sunset.
  - If Sanity hits 0 before that, you reach Azathoth (the bad ending).
- **Optional:** with high Insight you can turn the Shantak back toward Kadath for a **true-form fight** (from §14.7's Nyarlathotep forms), the hardest fight in the game, leading to the full "gods come home" ending.
- **Ending:** you wake in Arkham at sunset, and it is the city you dreamed.

### V2 optional bosses
- **The Martense Den** (Arkham hills, any time):
  - A warren of the degenerate clan from *The Lurking Fear*: goblins swarm in the dark.
  - The Martense **Patriarch** only attacks during a thunderstorm, as in the story. Lightning flashes reveal where he is.
- **Hatheg-Kla** (after Ulthar):
  - Climb where **Barzai the Wise** vanished. You can't fight the Other Gods.
  - The mountaintop warps as you go higher. **Get down alive** before Sanity runs out.
  - Gives the Archsage reveal if the Barzai option is chosen.
- **The Quarry of Inganok:**
  - Something is quarrying from the other side of the onyx.
  - A **Dhole**-like worm bursts through walls in a pattern. Watch the dust and trigger the quarry's explosive charges when it surfaces.
- **Kuranes' Dream:**
  - A dream inside a dream: Kuranes' memory of his childhood Cornwall is being eaten by a nightmare.
  - Fight a **Twisted Knight** (a hollow suit of armour wearing Kuranes' boyhood face) inside a shifting English landscape.
  - Reward: Kuranes' sword.

---

## 4. Shared bosses

| Boss | V1 | V2 | Changes |
|---|---|---|---|
| Shantak Rider | Kingsport cliff, ballistae | The Moon's docks, the cats' rescue | Arena and helpers; same three phases |
| Night-gaunts of Ngranek | ✓ | ✓ | Identical |
| Gug (Warlord / Sentinel) | War-field and tunnels | Tower of Koth chase | Same creature and attacks, different arena |
| High Priest Not to Be Described | The Apprentice | Depends on the premise | Identical fight, different reveal |
| Nyarlathotep | Temptation → time door | Temptation → Shantak flight | Phase 1 shared |
| Moon-beast swell/shrink pattern | Overseer, Hostage-Keeper | Overseer, Drum-Master, Admiral | One system, reused |

**Build these first:** the **Shantak Rider** (the demo boss in both versions) and the **Moon-beast swell/shrink system**. Both are reused the most.

---

## 5. Implementation notes (MWSE-Lua)

- **A boss framework** in `scripts/tdl/boss.lua`:
  - a phase table (health thresholds, invulnerability windows, phase-change events);
  - an arena lock (doors and barriers);
  - boss music;
  - a health bar;
  - checkpoint/retry;
  - per-phase Mindspeak hints.
  
  Each boss is a data file plus a few callbacks.
- **Scripted moves:** dives, leaps, grabs and knock-backs move the actor directly with MWSE and play a matching animation. Don't rely on AI pathing for them.
- **Wind-up windows:** the boss framework tells the Severance system when a parry window is open, so every boss gets parries for free.
- **Allies:** use companion AI packages, and make named allies essential during fights.
- **Swell/shrink:** swap between two scaled versions of the actor (or change its scale over 0.5 s), with matching damage and armour stats per form.
- **Non-kill wins** (sparing, submitting, surviving, sealing) set a journal stage and trigger an outro scene. Make sure the fight can't end with an accidental kill: make the target essential until the "Spare" prompt is offered.
- **Difficulty:** an MCM slider for boss health and damage, plus an "assist" option that widens parry windows and shows wind-up markers.
- **Voice:** each boss gets roughly 5–15 barks (taunts, phase changes, death), plus Mindspeak hints from the Archsage. Bosses that don't speak (Shantak, gugs, night-gaunts) get sound design instead (THE_DREAMLANDS.md §7).
- **Testing:** a debug console command that teleports to any boss arena with a preset level and gear.
