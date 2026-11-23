# Creatures: Lovecraft → Morrowind

This file maps each Lovecraft creature in The Dreamlands to the vanilla Morrowind creature (Morrowind, Tribunal or Bloodmoon) that is the best starting point for it. It also notes where **4thUnknown's Creatures Morrowind Edition** has a better version of that base. Use it to plan the asset work and to estimate effort. It expands the short table in [THE_DREAMLANDS.md §4.1](THE_DREAMLANDS.md).

## How to read this

**Match** is how close the base creature already is to Lovecraft's description:

| Match | Meaning | Typical work |
|---|---|---|
| ★★★★★ | Nearly exact | New record and texture only |
| ★★★★☆ | Right shape, wrong surface | Retexture and rescale |
| ★★★☆☆ | Right body plan, key features missing | Retexture plus small mesh edits (remove or add a part) |
| ★★☆☆☆ | Only the silhouette or the role fits | Kitbash parts from several meshes |
| ★☆☆☆☆ | Placeholder only | Needs a new mesh: generate with **Meshy**, rig onto the nearest vanilla skeleton (THE_DREAMLANDS.md §16.4) |

**4U** means 4thUnknown has a remodel of that base creature. The conversion is by Bahamut, from 4thUnknown's Skyrim creatures. It covers 10 bases:
- Daedroth
- Shalk
- Clannfear
- Ogrim (two texture variants)
- Nix-Hound
- Kagouti
- Durzog
- Guar
- Ascended Sleeper
- Kwama Forager

The mod's notes say not every creature is done yet, and that it keeps the vanilla skeletons and animations with small tweaks. Because the skeletons are vanilla, a 4U mesh can stand in for the vanilla one without new animation work.

## Using 4thUnknown's meshes: read this first

The mod is a **replacer**: it overwrites the vanilla mesh files. A Dreamlands creature can use it in one of two ways:

1. **Optional dependency (safe):** our creature records point at the vanilla mesh paths. Players who install 4thUnknown see the better model automatically. We redistribute nothing of theirs. **The catch:** retexturing a vanilla mesh for a new creature means shipping our own copy of the mesh under `meshes/tdl/`. That copy is always the vanilla version, not 4U.
2. **Edited copies (needs permission):** to ship a modified 4U mesh (for example a pale, noseless 4U Guar as a ghast), you need permission from 4thUnknown and Bahamut. I couldn't read the mod's Nexus Permissions tab (the page blocks automated access), so **check it before building on these meshes**:
   - [Morrowind Nexus #50137](https://www.nexusmods.com/morrowind/mods/50137)
   - [Modding-OpenMW listing](https://modding-openmw.com/mods/4thunknowns-creatures-morrowind-edition/)

   If modification and reuse aren't allowed, ask the authors, or use route 1.

**Recommendation:** build every creature from vanilla meshes, which the Bethesda mod policy covers. List 4thUnknown as an *optional visual upgrade* only for creatures that keep a vanilla mesh unchanged. Use 4U versions directly only after you have permission.

---

## Demo creatures (Part I)

These appear in the Arkham, Dunwich and Kingsport incursions. Build them first.

| Lovecraft creature | Source | Base creature | 4U | Match | Notes |
|---|---|---|---|---|---|
| **Night-gaunt** | *Dream-Quest*, *Fungi from Yuggoth* | **Winged Twilight** | — | ★★★★☆ | Black, rubbery, horned, bat-winged, barbed tail: the Twilight already has the horns, membranous wings and tail. Remove the face (smooth the head), make the skin black and oily, and drop the feminine shaping. **The closest match in the game.** |
| **Ghast** | *Dream-Quest* | **Guar** | ✓ | ★★★☆☆ | Ghasts are horse-sized and hop on long kangaroo-like hind legs, with a noseless, almost human face. The Guar's two-legged stance and size fit very well; the head needs replacing with a flat, pale, noseless face. The 4U Guar has a better leg silhouette. Alt: **Clannfear** (✓4U) for smaller ghasts. |
| **Zoog** | *Dream-Quest* | **Scamp** (scaled ~0.5) | — | ★★★☆☆ | Lovecraft barely describes them ("small, brown", furtive, fluttering speech), so there's design freedom. A small, shrunken, fur-textured Scamp reads as a sly little goblin-thing. Alt: **Rat** for swarm fodder (★★☆☆☆). |
| **Man of Leng** | *Dream-Quest*, *Celephaïs* | **NPC: Khajiit/Argonian legs + Dremora head** | — | ★★★★☆ | Horned, hoofed, wide-mouthed satyr-men. Beast-race digitigrade legs (no shoes) give the goat legs, and Dremora heads give the horns. Recolour the skin, widen the mouth. As NPCs they can use weapons, armour and the turban-like headwear from the text. |
| **Moon-beast** | *Dream-Quest* | **Ascended Sleeper** | ✓ | ★★★☆☆ | Lovecraft: greyish-white, slippery, toad-like, *eyeless*, with a mass of short pink tentacles on the snout. The Sleeper's tentacled face is the right idea. Bulk out the body, make it pale and wet-looking, tint the tentacles pink and remove the robes. The 4U Sleeper has much better tentacles. |
| **Shantak** (boss mount) | *Dream-Quest* | **Cliff Racer** (scaled ×4–5) | — | ★★★☆☆ | "Larger than elephants," scaly not feathered, with a head like a horse's. The Cliff Racer's scaly flier shape and dive-attack AI are ideal; replace the head with a long equine one. Animation plays fine at scale. |
| **Shantak Rider** (boss) | design doc | **Moon-beast** (above) on the Shantak | — | ★★☆☆☆ | Morrowind has no mounted creatures. Fake it: phase 1 is one creature (Shantak with a rider mesh attached at the spine bone); phase 2 swaps in two separate actors. |
| **Cultist** | *Dunwich*, *Call of Cthulhu* | **NPC (Sixth House robes)** | — | ★★★★★ | Dagoth/Sixth House robes and masks fit cultists almost unchanged. |

## Part II creatures

| Lovecraft creature | Source | Base creature | 4U | Match | Notes |
|---|---|---|---|---|---|
| **Ghoul** | *Pickman's Model*, *Dream-Quest* | **Corprus Stalker** body + **Durzog** head | ✓ (Durzog) | ★★★☆☆ | Rubbery, stooping, dog-faced, with hoof-like feet. The Stalker's hunched gait and the Durzog's canine-reptile snout together give the "doglike" face. Alt: **Hunger** (gaunt, rubbery, long limbs, ★★★☆☆), or **Daedroth** (✓4U, a bipedal beast-head, ★★☆☆☆). |
| **Gug** | *Dream-Quest* | **Ogrim / Ogrim Titan** (scaled ×1.5–2) | ✓ | ★★★☆☆ | Huge, furry, with a mouth that opens *vertically*, and forearms that split in two at the elbow. The Ogrim has the bulk and the brute AI; you need a vertical-mouth head, fur and the doubled forearms. The 4U Ogrim is the better base. |
| **Dhole** (Vale of Pnath) | *Dream-Quest* | **Kwama Forager** (scaled ×15+) | ✓ | ★★★☆☆ | Barely seen in the text ("something slithering"). A giant grub breaking up through bone-heaps sells it. Keep it mostly hidden and scripted. |
| **Wamp** | *Dream-Quest* | **Scrib** or **Kwama Forager** | (✓) | ★★☆☆☆ | Only "red-footed" and carrion-dwelling. Paint the feet red. Fodder. |
| **Spider of Leng** | *Dream-Quest* | **Shalk** (scaled up) | ✓ | ★☆☆☆☆ | Morrowind has no organic spider. A big purple Shalk is a placeholder; plan a new mesh. |
| **Cat of Ulthar / of Saturn** | *The Cats of Ulthar*, *Dream-Quest* | **none** (placeholder: Bloodmoon **Wolf**, scaled down) | — | ★☆☆☆☆ | There is no house cat in Morrowind. Cats matter (allies, a faction, the Dream-Shape form), so **a new cat mesh is a priority asset**. Saturn's cats: same mesh, odd colours and size. |
| **Deep One** | *Dagon*, *Shadow over Innsmouth* | **NPC: Argonian body + new fish head** | — | ★★★★☆ | Grey-green, white-bellied, gilled, bulging-eyed, webbed, hopping. The Argonian body is right (webbed hands, swimming animations, weapons). Alt for feral ones: **Dreugh** (★★★☆☆) or **Daedroth** (✓4U, ★★☆☆☆). |
| **Innsmouth hybrid** | *Shadow over Innsmouth* | **NPC, any race**, with a "Look" retexture | — | ★★★★☆ | Narrow head, unblinking eyes, scaly neck folds. Head retextures on normal NPCs. Swap to Deep One at the end of *The Change*. |
| **Dagon / Mother Hydra** | *Dagon*, *Innsmouth* | **Deep One** scaled ×5 | — | ★★★☆☆ | Lovecraft: a huge Deep One-like being. Scaling works; add barnacle textures. |
| **Star-spawn / Cthulhu** | *The Call of Cthulhu* | **Ascended Sleeper** (scaled ×10+) | ✓ | ★★★☆☆ | Octopus head, scaly rubbery body, claws, *narrow wings*. The Sleeper's tentacled face is the best Cthulhoid head in the game, especially the 4U version. Add Winged Twilight-style wings and remove the robes. Cthulhu himself needs a dedicated mesh for the R'lyeh finale. |
| **Shoggoth** | *At the Mountains of Madness* | **none** (placeholder: **Kwama Queen**) | — | ★☆☆☆☆ | A fifteen-foot, shapeless, iridescent mass full of eyes. Nothing like it in the game. New mesh, ideally with a morph/ripple animation. |
| **Elder Thing** | *At the Mountains of Madness* | **none** (placeholder: **Netch**) | — | ★☆☆☆☆ | Barrel body, starfish head, fan wings. The Netch's float AI and tentacles are the only useful part. New mesh. |
| **Mi-Go** | *The Whisperer in Darkness* | **Dreugh** + **Cliff Racer / Twilight wings** | — | ★★☆☆☆ | Pinkish, crab-like, fungoid, with membranous wings and a convoluted "head" of antennae. The Dreugh's crustacean legs and claws help; it needs wings, a fungal head and pink skin. |
| **Great Race of Yith** | *The Shadow out of Time* | **none** (placeholder: **Dwemer Centurion**) | — | ★☆☆☆☆ | Ten-foot ridged cones with four flexible limbs. The Centurion is only a stand-in that moves slowly and fires lightning. New mesh. |
| **Flying Polyp** | *The Shadow out of Time* | **Bull Netch** (invisible) | — | ★★★★☆ | "Only partly material" and mostly invisible: the design already hides it below Insight 4. Give a Bull Netch a chameleon/invisibility effect, whistling sounds and dust particles. The mesh barely matters. |
| **The Colour Out of Space** | *The Colour Out of Space* | **Ancestor Ghost** (mesh hidden) + VFX | — | ★★★★☆ | It has no body. Use a ghost actor for AI and hit detection, render it as a glowing, unnamable-hued light, and blight the area around it. |
| **Things from Beyond** | *From Beyond* | **Netch** (scaled down) | — | ★★★★★ | Tillinghast sees "great inky, jellyfish monstrosities" drifting through the air. A dark, translucent Netch is almost exactly that. |
| **The Dunwich Horror** (Wilbur's twin) | *The Dunwich Horror* | **Invisible actor**; visible form: **Kwama Queen + Ascended Sleeper** parts | ✓ (Sleeper) | ★★★☆☆ | Invisible for nearly the whole story: footprints, crushed fences and sounds. When the powder shows it, it's a vast egg-like mass of ropy tentacles with half a face on top. Kitbash a single reveal model. |
| **Wilbur Whateley** | *The Dunwich Horror* | **NPC** + **Ascended Sleeper** tentacle parts | ✓ | ★★★☆☆ | Human from the waist up, with tentacles and a tail below, under clothes. Only shown in his death scene. |
| **The Hound** | *The Hound* | **Nix-Hound** + **Winged Twilight** wings | ✓ | ★★★☆☆ | A winged, hound-like thing; a skeleton when found in the grave. The 4U Nix-Hound has a gaunt, alien canine shape that fits. Grave form: a skeleton mesh with a jade amulet. |
| **Lurking Fear (degenerate Martenses)** | *The Lurking Fear* | **Goblin** (Tribunal) | — | ★★★★☆ | Dwarfed, ape-like, hairy, pale, in swarms under Tempest Mountain. Tribunal goblins already fit; whiten the skin, add fur. |
| **The rats** | *The Rats in the Walls* | **Rat** | — | ★★★★★ | Exact. Spawn them in waves with scraping sounds behind walls. |
| **Reanimated dead** | *Herbert West* | **Bonewalker / Ash Zombie** | — | ★★★★☆ | Fresh, violent corpses. Ash Zombie animations with fresh-corpse textures. *(Herbert West is excluded from the writing model's training for its racism; using the reanimated as a creature concept is fine.)* |
| **Beings of Ib / Bokrug** | *The Doom that Came to Sarnath* | **Dreugh** or **Argonian NPC** | — | ★★★☆☆ | Green, voiceless, with bulging eyes, flabby lips and odd ears. Bokrug the water-lizard: **Clannfear** (✓4U) scaled ×6 and made idol-like. |
| **Nyarlathotep** (human mask) | *Nyarlathotep*, *Dream-Quest* | **NPC** (Dark Elf/Imperial, Egyptian robes) | — | ★★★★★ | The tall, swarthy Pharaoh form is a normal NPC. His true forms (the Crawling Chaos, the faceless god) need custom meshes and VFX. |
| **The High Priest Not to Be Described** | *Dream-Quest* | **NPC**, yellow silk mask | — | ★★★★★ | A robed figure in a yellow mask; what's under it is never shown. |
| **Pickman** (ghoul form) | *Pickman's Model*, *Dream-Quest* | **Ghoul** (above) with unique textures | — | ★★★☆☆ | Same as ghoul. |
| **Kuranes, Carter, Nodens** | *Celephaïs*, *Dream-Quest* | **NPCs** | — | ★★★★★ | People (Nodens is a grey, archaic figure in a shell chariot pulled by dolphins: an NPC on a scripted static). |

**Left out on purpose** (other authors' creations, per THE_DREAMLANDS.md §14.2): Hounds of Tindalos, Byakhee, Dark Young, Shudde M'ell, Cthugha.

## Filler: bandits and fantasy monsters

These need little or no change, which suits a dark-ages Miskatonic Valley:

| Role | Base | 4U | Match |
|---|---|---|---|
| Bandits, brigands, deserters | NPCs | — | ★★★★★ |
| Wolves, bears, boars | Bloodmoon wildlife | — | ★★★★★ |
| Goblins in the hills | Tribunal Goblins | — | ★★★★★ |
| Barrow dead, skeletons | Skeleton, Bonewalker, Draugr (Bloodmoon) | — | ★★★★★ |
| Swamp beasts | **Kagouti**, **Nix-Hound** (✓4U both) as "Dreamlands-tainted" fauna | ✓ | ★★★★☆ |
| Giant beetles in caves | **Shalk** | ✓ | ★★★★★ |
| Hill troll / ogre | Bloodmoon **Grahl**, **Ogrim** | ✓ (Ogrim) | ★★★★☆ |

---

## Summary

- **Morrowind is strongest on Dreamlands monsters.**
  - Night-gaunts, Men of Leng, cultists, Things from Beyond, the rats and the Lurking Fear are four or five stars.
  - Ghasts, zoogs, Moon-beasts, Shantaks, gugs and ghouls are three stars: one or two mesh edits each.
  - **All of the demo creatures can be built from vanilla parts.**
- **It is weakest on Lovecraft's alien races.** Shoggoths, Elder Things, Yithians and the Spider of Leng need new meshes. So do the **cats**, which should be built first because they are allies, a faction and a Dream-Shape. All of these are Part II.
- **Meshy fills those gaps** (THE_DREAMLANDS.md §16):
  - It generates the missing creatures. Rig each one onto the nearest vanilla skeleton so it reuses vanilla animations:
    - cats on the Nix-Hound
    - the Spider of Leng on the Shalk
    - the Mi-Go on the Dreugh
  - It generates the **replacement parts** that the three-star entries need: the ghast's face, the Gug's vertical mouth, the Shantak's horse head, the Moon-beast's snout. That is faster and safer than editing 4thUnknown's meshes.
  - Shoggoths and Elder Things have no usable skeleton, so they still need new animations. They are the most expensive creatures.
- **4thUnknown gives the most to these creatures:**
  - the Ascended Sleeper: Moon-beasts, Star-spawn, Cthulhu, Wilbur;
  - the Guar: ghasts;
  - the Ogrim: gugs;
  - the Nix-Hound: the Hound.
- **4thUnknown's limit:** it improves 10 vanilla bases, and none of those is a creature Morrowind is missing. Check its permissions before shipping edits of its meshes.

### Rough effort for the demo (Part I)

| Creature | Work | Estimate |
|---|---|---|
| Night-gaunt (if used early) | Face removal + retexture | 1–2 days |
| Ghast | Head replacement + retexture | 2–3 days |
| Zoog | Scale + fur retexture | 1 day |
| Man of Leng | NPC parts + head edit | 1–2 days |
| Moon-beast | Body edit + retexture | 3–4 days |
| Shantak + Rider | Head replacement, scale, attachment, boss script | 4–6 days |
| Cultists | Records only | < 1 day |

That's about **2–3 weeks** of asset work for one person who is new to Blender and NIF export. It goes faster once the [io_scene_mw](https://github.com/Greatness7/io_scene_mw) pipeline is familiar.
