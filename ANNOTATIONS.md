# Annotations to STORY.md

Background notes for each caret marker in [STORY.md](STORY.md), from the game's point of view. Each note can cover:

- **Game:** what the player does or sees, and which system it uses (section numbers refer to [THE_DREAMLANDS.md](THE_DREAMLANDS.md)).
- **Lore:** where it comes from in Lovecraft's public-domain fiction.
- **Changed:** where the mod deliberately bends that lore.
- **Decide:** open questions for you.

Run `python tools/story/check_annotations.py` after editing either file. It checks that every marker has a note (and the reverse), and runs the racism filters over both files.

---

## Frame

<a id="a1"></a>
### ^1. The testament frame
**Lore:** Lovecraft's favourite device is the first-person document written after the events, by a narrator who expects not to be believed (*Dagon*, *The Call of Cthulhu*, *At the Mountains of Madness*).
**Changed:** his narrators are usually broken by what they learned. This one ends grateful and hopeful. That is the "heroic" turn.
**Game:** the testament is an in-game book. One chapter unlocks in the journal as each act ends, read aloud by the Archsage (§7.4). The player character is always "my pupil," with no name, sex or race, so the text fits any character the player makes.

<a id="a2"></a>
### ^2. The Archsage's name
**Decide:** still undecided (placeholders in §15.2: Corwin Sallow, Ezra Keel, Thaddeus Wren). The testament never gives it, which can stay that way: he is ashamed of his priest-name and never uses his new one in writing. Optionally, Part II reveals his old priestly name as a story beat.

## Part I: The Waking World

<a id="a3"></a>
### ^3. The Drowned Coast
**Game:** a Part II region and the Archsage's tower; seen in the opening flashback (^6).
**Lore:** *The Call of Cthulhu* places R'lyeh's rising far out at sea and links it to carved idols and sailors' finds.
**Changed:** an **invented** coast and people. It replaces the real Pacific islands Lovecraft used (e.g. Ponape in *Innsmouth*), which he wrote about with racist assumptions.
**Assets:** Bloodmoon coastline and rocks, Daedric ruins re-textured green-black for the reef temple.

<a id="a4"></a>
### ^4. The idol and "when the stars came right"
**Lore:** *The Call of Cthulhu* (1928): the pulpy, tentacled head on a pedestal of glyphs, and the phrase "when the stars are right."
**Game:** the green-crusted stones are collectible misc items whose descriptions build the Cthulhu backstory before Part II's finale.

<a id="a5"></a>
### ^5. The chant
**Lore:** quoted from *The Call of Cthulhu*. Public domain.
**Game:** the same line is the core of the cultists' chant at Dunwich (^24) and in R'lyeh. The Archsage's voice line uses the "wet second voice" treatment (§7.2).

<a id="a6"></a>
### ^6. The warrior
**Game:** the game's **opening scene**: a short flashback played as the young priest, ending when the hooded, faceless warrior spares you. The player has no reason to suspect who the warrior is until ^53–55, where the scene is replayed from the warrior's side.
**Decide:** this replaces the "bloodline" option (C) in §15.2 with a time loop: the warrior *is* the player.

<a id="a7"></a>
### ^7. No sign of the sword
**Game:** consistency note: the warrior leaves the sword standing in the sand (^54), and the tide takes it before dawn. The Archsage never saw what happened to it until he found it in Pell's shop.

<a id="a8"></a>
### ^8. The ward
**Game:** the in-story reason the Archsage never fights beside you (option A in §15.2). He can leave his tower for a few nights a year, which he spends once, in Chapter II. Every time he strains the ward for you (the Sky Road, ^48), Cthulhu's stirring in the epilogue (^57) gets worse. It's a quiet cost the player may notice in Doom (§3.2).

<a id="a9"></a>
### ^9. Medieval Arkham and the Collegium
**Lore:** Arkham and Miskatonic University (*Herbert West*, *The Dunwich Horror*, *The Dreams in the Witch House*, and others).
**Changed:** a walled dark-ages market town; the university becomes the monastery-college **the Miskatonic Collegium**.
**Assets:** Imperial town pieces with new gambrel-roof textures (§4.1).

<a id="a10"></a>
### ^10. Abner Pell and the shop
**Game:** the prologue tutorial (§15.3): stocking shelves, bartering, deliveries, the cellar fight. Pell is an original character and the player's first **Anchor** (§11.2). His shop is the emotional home base: it gets damaged in the first incursion, repaired over Part I, and sells better stock as you help him.

<a id="a11"></a>
### ^11. The dream of the cloud city
**Lore:** the phrasing echoes *Celephaïs*, where Serannian is "the pink marble city of the clouds… where the west wind flows into the sky."
**Game:** destiny option (A) from §15.2. Sleeping in a bed sometimes plays a short dream vignette of Serannian. Over Part I the vignettes darken, foreshadowing the black marble (^29).

<a id="a12"></a>
### ^12. Stars that go out
**Game:** a visible world clock. The night sky loses stars as **Doom** rises (a sky-texture swap or shader) and gets them all back at the end (^56). It's a cheap, haunting way to show the stakes without a UI bar.

<a id="a13"></a>
### ^13. The thing in the jar
**Game:** the **Composure check** tutorial (§11.2). Looking at the jar costs your first Sanity and introduces the HUD bar. It can't fail completely (a scripted pass), but the amount lost depends on Willpower.
**Lore:** "of no colour that has a name" nods to *The Colour Out of Space*.

<a id="a14"></a>
### ^14. The enemy in the sky
**Changed:** the core lore change (§15.1). The horrors come from the Dreamlands' sky cities, not outer space.
**Lore:** Serannian floats above the Cerenerian Sea in *Celephaïs* and *Dream-Quest*. The Moon-beasts' black galleys already sail into the sky in *Dream-Quest*.

<a id="a15"></a>
### ^15. The thread (Mindspeak)
**Game:** the Mindspeak power (§15.8): talk to the Archsage anywhere, with voiced lines (§7.4 item 9). He can see through your eyes, which is how he can narrate everything in the testament.

<a id="a16"></a>
### ^16. The year of lessons
**Game:** the training structure of §15.5. The "year" is never reached. Each incursion cuts the schedule short, which is the story's justification for the player being underpowered (§15.4).
**Characters:** Captain Mercy Thorne is original: a trainer (Lesson of Steel), the head of the Watch faction (§3.4), and a recurring ally in incursions.

<a id="a17"></a>
### ^17. The Sign
**Lore:** Lovecraft mentions an "Elder Sign" in *Dream-Quest* (villagers make it against evil) without ever describing it in detail.
**Changed:** the Sign is the mod's own: a priest's *opening* gesture turned inside out. That makes the Archsage's past the reason the player can fight at all.
**Game:** the sealing channel mechanic (§15.4).

<a id="a18"></a>
### ^18. The first incursion
**Game:** Chapter 3 (§15.3): zoog swarms and Leng raiders in Arkham's streets, ending at the burying-ground gate.
**Lore:** zoogs are the furtive creatures of the Enchanted Wood (*Dream-Quest*); the Men of Leng are horned, hooved almost-humans who serve the Moon-beasts (*Dream-Quest*).
**Assets:** scamps re-scaled as zoogs; raiders built on Morrowind NPC bodies with horns and hoods (§4.1).

<a id="a19"></a>
### ^19. Pell is struck down
**Game:** the stakes of the first fight. Pell survives in every version, but the player's actions decide *how* hurt: reach his street fast and he keeps his arm. A small consequence that teaches the player that choices in incursions matter.
**Decide:** whether this is scripted (as written) or player-dependent.

<a id="a20"></a>
### ^20. Three attempts at the Sign
**Game:** the sealing mechanic teaches itself through failure: the first channel is scripted to be interrupted, the second holds, the third succeeds. This mirrors the "Press On" push mechanic (§11.2).

<a id="a21"></a>
### ^21. Training resumes: Warding
**Game:** the first Interlude (§15.3): the Lesson of Warding from Magister Henry Armitage (a medieval version of the *Dunwich Horror* librarian, §14.4) unlocks the ward spell and calming draught.

<a id="a22"></a>
### ^22. The open valley
**Game:** the open-world section: bandit bounties on the Aylesbury Pike, ordinary wolves, and the public-domain sidequests in §15.6 (*The Terrible Old Man*, *The Statement of Randolph Carter*, *The Music of Erich Zann*, *The Festival*, *The Tomb*, *The Unnamable*). "Came out … of a few of them sadder" covers the quests without happy endings.

<a id="a23"></a>
### ^23. Dunwich's stone circles
**Lore:** *The Dunwich Horror* describes the round hills crowned with stone circles that the locals avoid.
**Game:** the second incursion (§15.4): a night fight where light matters, because ghasts die in it.
**Lore:** "die in the light" and the kangaroo-like leap are both from *Dream-Quest*.

<a id="a24"></a>
### ^24. The Apprentice
**Game:** the human villain of the demo and Part II (§15.2). First seen at Dunwich; trades with the black galleys in Dylath-Leen (Chapter VIII); ends inside the yellow mask (^44). His line "You chose the wrong side of the gate" is the demo's thematic hook.
**Decide:** his name. The testament never gives it, and the game probably should.

<a id="a25"></a>
### ^25. The Black Tongue
**Game:** the Lesson of the Black Tongue (§15.5): one enemy spell that commands sky-city creatures. Very strong, and costs Sanity on every use. The testament's line about refusing it a hundred times is a promise: track how rarely the player used it, and have the Archsage's final narration and an epilogue variant reflect it.

<a id="a26"></a>
### ^26. Kingsport and the high house
**Lore:** *The Strange High House in the Mist* (published 1931; widely treated as public domain): the house on the cliff no road reaches, whose tenant receives visitors from beyond, including Nodens.
**Game:** the finale's setting and the doorway to Part II (^31).

<a id="a27"></a>
### ^27. The galley and the Moon-beasts
**Lore:** the Moon-beast description paraphrases *Dream-Quest*: greyish-white, able to expand and contract, toad-like and eyeless, with short pink tentacles on the snout. The galleys rowed by unseen rowers are also *Dream-Quest*.
**Game:** the third incursion: three gates at once across Kingsport (§15.4).

<a id="a28"></a>
### ^28. The Shantak Rider
**Game:** the demo boss (option A, §15.3). Phase 1 in the air (bring the Shantak down), Phase 2 on the cliff-top against the overseer. The minstrels' details (the Watch on the harbour-stairs, the fire-boats) are optional side objectives during the fight.
**Lore:** "larger than elephants and had heads like a horse's" is *Dream-Quest*'s description of the Shantak.

<a id="a29"></a>
### ^29. The gate that won't close
**Game:** the demo's last image (§15.3 Ending). The Sign fails on it, so the player is shown, not told, that Part II is about going to the far side.

<a id="a30"></a>
### ^30. End of the demo
**Game:** the `tdl_demo` flag (§15.8) blocks the Dreamlands from here, shows an "End of Part I" screen, and unlocks reading the testament up to this point.

## Part II: The Dreamlands

<a id="a31"></a>
### ^31. Why the player must go into dream
**Game:** the rule that drives Part II: a gate can only be sealed from the side it opened from. It also explains why the player enters the Dreamlands by **sleeping**, not by stepping through the gate. The waking body stays in the high house.

<a id="a32"></a>
### ^32. The seventy steps and the cavern of flame
**Lore:** *Dream-Quest*: the seventy steps of light slumber, the priests Nasht and Kaman-Thah, the seven hundred steps to the Gate of Deeper Slumber.
**Game:** Part II, Act 1 (§3.5); the tutorial for Dreamlands rules (Sanity behaves differently, reverb on voices, §7.4 item 6).

<a id="a33"></a>
### ^33. The sword enters dream
**Game:** the player keeps the warrior's sword, a unique weapon whose strength grows through Part II. Its description changes as the player gets closer to the truth (^53–55).

<a id="a34"></a>
### ^34. The zoogs were hostages
**Changed:** in Lovecraft, zoogs are mischievous and independent. Here they were forced into the invasion. This lets the game turn a demo enemy into a Part II ally, rewarding mercy.
**Game:** the Zoog hostage-rescue quest; joining options for the Zoog council.

<a id="a35"></a>
### ^35. The cats of Ulthar
**Lore:** *The Cats of Ulthar* (no man may kill a cat in Ulthar) and *Dream-Quest* (Carter speaks the language of cats; the cats are the Moon-beasts' enemies; the old cat on the temple steps).
**Game:** the Cats faction (§3.4). Their help at ^47 depends on whether you joined or helped them.

<a id="a36"></a>
### ^36. Kuranes and fallen Serannian
**Lore:** *Celephaïs*: Kuranes, a London dreamer, becomes King of Ooth-Nargai and holds court "alternately in Celephaïs and in the cloud-fashioned Serannian."
**Changed:** Serannian has fallen to the Moon-beasts (§15.1).
**Game:** the Court of Kuranes faction (§3.4).

<a id="a37"></a>
### ^37. Randolph Carter, out of time
**Lore:** Carter is Lovecraft's recurring dreamer (*The Statement of Randolph Carter*, *The Silver Key*, *Dream-Quest*).
**Changed:** the game is set in a dark age, so Carter is a visitor from a far later century. Time in the Dreamlands doesn't follow waking time, which also sets up ^53.
**Game:** a companion for parts of Part II; voice direction in §7.2.

<a id="a38"></a>
### ^38. The silver key
**Lore:** *The Silver Key* (1926; published 1929): the key takes Carter back to his own childhood.
**Game:** a quest item that does nothing until ^54, where it brings the player home from the past. Players who examine it get a hint: "It turns toward whatever you have lost."
**Note:** *Through the Gates of the Silver Key* is a collaboration (with E. Hoffmann Price) and is **not** used.

<a id="a39"></a>
### ^39. The Sky Road tablet
**Game:** the spell from §15.5 that reaches the sky cities. Getting it is the spine of Part II: Kuranes (where) → Ngranek (the way down) → the Underworld (the tablet) → Inganok (reading it).
**Changed:** the Sky Road is original. In Lovecraft, people reach Serannian by galley.

<a id="a40"></a>
### ^40. Ngranek and the night-gaunts
**Lore:** *Dream-Quest*: the carved face on Ngranek; night-gaunts are faceless, horned, rubbery and winged, serve Nodens, carry their victims off in silence, tickle them, and drop them in the Vale of Pnath.
**Game:** a climb that the player can only "lose." Fighting the night-gaunts is pointless, and letting them take you is the way forward. A good place to teach players that not every enemy is an enemy.

<a id="a41"></a>
### ^41. "Because my pupil has asked me to be"
**Game:** the Underworld is the bleakest act (gugs, ghasts, the war). The Archsage keeping it short in the testament is a hint that it cost the pupil something. Players who choose dark options there get one extra line in the epilogue.

<a id="a42"></a>
### ^42. Pickman
**Lore:** *Pickman's Model* (the Boston painter of ghouls) and *Dream-Quest* (Pickman, now a ghoul, helps Carter).
**Game:** the Ghouls faction leader (§3.4); his voice direction in §7.2.

<a id="a43"></a>
### ^43. The high-priest not to be described
**Lore:** *Celephaïs* and *Dream-Quest*: the high-priest who "wears a yellow silken mask over its face" in a prehistoric stone monastery on Leng. In *Dream-Quest*, Carter flees through its painted passages.
**Game:** the Leng dungeon and the Apprentice's final boss fight.

<a id="a44"></a>
### ^44. The Apprentice's end
**Changed:** the Apprentice took the mask and was consumed. The laugh behind it is Nyarlathotep's, which matches the hints in *Dream-Quest* that the high-priest is connected to him.
**Game:** no victory speech. The mask falls, there's nothing there, and the Archsage is silent over Mindspeak for the rest of the area.

<a id="a45"></a>
### ^45. Inganok
**Lore:** *Dream-Quest*: the onyx city whose people quarry stone for the gods and know the way to Kadath.
**Note:** this edition of the text spells it **Inganok**; older editions print "Inquanok." The mod uses Inganok.

<a id="a46"></a>
### ^46. Walking the Sky Road
**Game:** the Sky Road spell in use: a scripted transition (a stair of light, Insight-style shader) rather than real flight. "Sideways from both" is a nod to Lovecraft's non-Euclidean directions.

<a id="a47"></a>
### ^47. The cats leap to the moon
**Lore:** *Dream-Quest*: the cats of dream leap to the moon and rescue Carter from the Moon-beasts.
**Game:** the battle of the sky cities is the payoff of every alliance: cats (^35), ghouls (^42), night-gaunts (^40), zoogs (^34). Each ally you earned appears; each you didn't is missing.

<a id="a48"></a>
### ^48. The voices that bring the pupil back
**Game:** the **Anchors** mechanic (§11.2) as the climax: during the final seal, each Anchor the player still has (Pell, Thorne, Arkham) can save one failed channel. Players who sacrificed or corrupted their Anchors have a harder final seal.
**Theme:** the heroic answer to Lovecraft's cosmic despair: ordinary attachments are what make a person strong enough to face the gulf.

<a id="a49"></a>
### ^49. Kadath
**Lore:** *Dream-Quest*: unknown Kadath in the cold waste, with the onyx castle of the gods of earth.
**Game:** Part II, Act 7. Alone, with no allies, so it's a contrast to ^47.

<a id="a50"></a>
### ^50. Nyarlathotep's form
**Lore:** this description is **quoted** from *Dream-Quest*. Public domain. It is deliberately left verbatim as an homage, and the copy check in `score.py` will (correctly) flag it.
**Game:** the Black Pharaoh form (§7.2). Other forms are available depending on how you played (§4 idea 4).

<a id="a51"></a>
### ^51. The offer
**Lore:** in *Dream-Quest*, Nyarlathotep tells Carter where his sunset city really is, and then sends him on a Shantak toward Azathoth.
**Game:** a dialogue choice. Accepting gives a **bad ending**: the player stays in a perfect dream Serannian forever, and the credits roll over an empty Arkham shop.

<a id="a52"></a>
### ^52. Memory, then choice
**Lore:** Carter escapes by remembering Boston ("…your gold and marble city of wonder is only the sum of what you have seen and loved in youth").
**Changed:** the pupil escapes by *choosing* the waking world, not only remembering it. This makes it the player's decision, which is the heroic version.

<a id="a53"></a>
### ^53. The Night of the Rising Star, again
**Game:** the opening scene (^6) replayed from the warrior's side, in the same location, with the same chant.

<a id="a54"></a>
### ^54. The loop closes
**Game:** the key choice of the game:
- **Spare the priest:** the canon ending. The loop closes, the silver key brings you home.
- **Kill the priest:** a paradox ending. The world unravels; no Archsage, no warning, the sky cities win. A short, horrible epilogue, then a reload prompt.
- **Do nothing:** the rite completes and Cthulhu wakes. The worst ending.

The line "Not yet. You will be needed" is identical to ^6, so players recognise it.

<a id="a55"></a>
### ^55. How the sword reached the shop
**Game:** the reveal of what the sword above the counter always was. Pell's line in Chapter II ("Came up in a fisherman's net, years back") was the setup.

## Epilogue

<a id="a56"></a>
### ^56. The stars return
**Game:** the sky gets all its stars back (^12). The shop has new windows. Free roam continues after the ending.

<a id="a57"></a>
### ^57. Cthulhu stirs
**Game:** the hook for the **endgame or sequel** (§14.7 *R'lyeh Rising*). The Archsage's ward is failing, partly because of what he spent helping you (^8, ^48).
**Decide:** whether R'lyeh is post-game content in this release or a later expansion.

<a id="a58"></a>
### ^58. "The door is shut."
**Lore:** Lovecraft loves a last line in italics that changes everything (*The Outsider*, *Arthur Jermyn*, *The Rats in the Walls*).
**Changed:** here the final italic line is a **victory**: the pupil's own hand, after the Archsage has gone, reporting that R'lyeh's last door was sealed. It's the most direct statement of the game's heroic answer to Lovecraft.
**Game:** shown only after the R'lyeh content is completed. Before that, the testament ends at "My pupil goes to fetch it in the morning."
