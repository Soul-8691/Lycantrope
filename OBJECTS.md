# LYCANTROPE — Objects to Generate with Meshy or Tripo3D

Every prop, building and item in the world that **Meshy** or **Tripo3D** should make. The idea tracker reads this file too, so you can approve or deny each object the same way as ideas, and the approved ones become the batch list for `tools/meshy/batch.py` (ART-01) or the equivalent Tripo3D web-app / CLI queue.

---

## How to read an entry

`- [TRE-01] **Name** — what it is. Prompt: "…" · variants · triangle budget · placement · collider. ⭐ (where)`

- **Prompt** describes the object only. The batch script appends the shared style line (ART-02) to every prompt automatically:
  > *stylized dark-fantasy, hand-painted textures, chunky readable silhouette, muted earthy palette, game-ready low-poly, single object, centered, no ground plane, no background*
- **Variants** is how many separate generations to keep, so repeated objects don't look identical. Rotation, scale and tint add more variety in-engine.
- **Budget** is the remesh target in triangles (ART-06). Things placed by the hundred stay small.
- **Placement:**
  - **scatter** means the world generator places it by biome rules, drawn with GPU instancing (WLD-12).
  - **placed** means it goes at a specific spot in `layout.json`, such as a landmark or Waystone.
  - **kit** means it's a piece that snaps together with others.
  - **held** means it's attached to a hand or the back.
- **Collider** is the simple shape the game uses for collisions, made by `normalize.py` (ART-07). The Meshy mesh itself is never used for collision.
- ⭐ = needed for the First Playable (about 45 objects).

**Tips for Meshy and Tripo3D:**
- **Trees:** ask for *"chunky clumps of foliage"*, not individual leaves. Both tools make solid meshes, and clumps read well and stay cheap.
- **Pose:** one object per prompt, upright, with no base or ground plane unless the object needs one (a statue plinth, for example).
- **Text and symbols:** avoid writing, logos and readable symbols. Use "carved runes" or "abstract sigils" instead.
- **Previews:** generate the cheap preview first, refine only the ones you keep, and re-roll anything that clashes with the rest (ART-16 previewer).

**Not made with Meshy or Tripo3D** (code makes these, so they're not in this list): terrain, water surfaces, the procedural sky (ART-09), roads and fog. There's no grass and there are no particles (ART-10 and ART-13 were denied); fire and spell effects are Meshy meshes instead (section 13, VFX). Also not Meshy: the dungeon wall/floor kit (ART-11, scripted geometry that Meshy can retexture), and the glow on the Dawnblade (a shader).

---

## 1. Trees (TRE)

- [TRE-01] **Brackenvale Oak** — Broad, gnarled meadow oak; the classic "tree on a hill". Prompt: "broad gnarled oak tree, thick twisted trunk, wide rounded canopy of chunky foliage clumps" · 3 variants · 3k tris · scatter · collider: trunk capsule. ⭐ *(Brackenvale)*
- [TRE-02] **Silver Birch** — Slim pale trunks in small groves along the roads. Prompt: "slender silver birch tree, white bark with black marks, light airy canopy of chunky leaf clumps" · 3 variants · 2k tris · scatter · collider: trunk capsule. ⭐ *(Brackenvale)*
- [TRE-03] **Apple Tree** — Small orchard trees near the village and farms. Prompt: "broad gnarled apple tree, short thick twisted trunk, wide rounded canopy of large chunky foliage clumps, small red fruit dotted over the foliage" · 2 variants · 3k tris · scatter · collider: trunk capsule. *(Brackenvale)*
- [TRE-04] **Burned Tree** — A tree charred by the raid, for the burned village outskirts. Prompt: "burned dead tree, charred black trunk, broken bare branches, ember-scorched bark" · 2 variants · 1.5k tris · scatter · collider: trunk capsule. ⭐ *(Brackenvale village)*
- [TRE-05] **Giant Wolfwood Pine** — Very tall, dark pine; the Wolfwood is made of these. Prompt: "very tall dark pine tree, thick straight trunk, layered drooping branches of dark needles, ancient forest" · 4 variants · 3.5k tris · scatter · collider: trunk capsule. ⭐ *(Wolfwood)*
- [TRE-06] **Dead Pine** — Grey dead pine with bare branches, for the gloomier glades. Prompt: "dead grey pine tree, bare jagged branches, peeling bark" · 2 variants · 1.5k tris · scatter · collider: trunk capsule. ⭐ *(Wolfwood)*
- [TRE-07] **Web-Wrapped Tree** — Tree shrouded in thick spider silk, for the Spider Grove. Prompt: "dead tree wrapped in thick white spider webs, silk cocoons hanging from branches" · 2 variants · 2.5k tris · placed · collider: trunk capsule. *(Spider Grove)*
- [TRE-08] **Weeping Swamp Willow** — Drooping willow with curtains of hanging moss. Prompt: "weeping willow tree, twisted trunk, long hanging curtains of moss and leaves, swamp" · 3 variants · 3k tris · scatter · collider: trunk capsule. ⭐ *(Blackmire)*
- [TRE-09] **Bald Cypress** — Swamp cypress with flared trunk and knobbly "knees" around it. Prompt: "bald cypress swamp tree, wide flared buttress trunk, knobby roots, sparse hanging moss" · 3 variants · 2.5k tris · scatter · collider: trunk capsule. ⭐ *(Blackmire)*
- [TRE-10] **Drowned Dead Tree** — Rotting grey trunk standing in water. Prompt: "rotting dead swamp tree trunk, broken top, slimy grey wood, fungus shelves" · 2 variants · 1.2k tris · scatter · collider: trunk capsule. *(Blackmire)*
- [TRE-11] **Snowy Fir** — Dense fir with snow on every branch layer. Prompt: "snow-covered fir tree, dense conical shape, thick snow resting on branches" · 3 variants · 2.5k tris · scatter · collider: trunk capsule. ⭐ *(Frostfang)*
- [TRE-12] **Frozen Dead Tree** — Ice-crusted bare tree, bent by the wind. Prompt: "frozen dead tree bent by wind, bare branches coated in ice and frost" · 2 variants · 1.5k tris · scatter · collider: trunk capsule. *(Frostfang)*
- [TRE-13] **Charred Ash Tree** — Black, split, still-smouldering tree. Prompt: "charred black tree trunk split open, glowing orange embers in cracks, volcanic wasteland" · 2 variants · 1.5k tris · scatter · collider: trunk capsule. ⭐ *(Ashen Reach)*
- [TRE-14] **Petrified Tree** — Tree turned to grey stone, crystal veins. Prompt: "petrified stone tree, grey rock bark, dull crystal veins, twisted shape" · 2 variants · 2k tris · scatter · collider: trunk capsule. *(Ashen Reach)*
- [TRE-15] **Thorn-Black Tree** — Leafless black tree with long thorns; the Dark Lord's land. Prompt: "leafless black thorn tree, long sharp thorns, twisted menacing branches, dark fantasy" · 3 variants · 2k tris · scatter · collider: trunk capsule. ⭐ *(Duskhold)*
- [TRE-16] **Great Fallen Oak** — The landmark: a colossal fallen tree you can walk along and under. Prompt: "colossal fallen ancient oak tree lying on its side, huge exposed roots, hollow trunk you can walk through, moss" · 1 variant · 12k tris · placed · collider: boxes along trunk. *(Wolfwood landmark, WLD-13)*
- [TRE-17] **Fallen Log** — Mossy log to climb over or hide behind. Prompt: "mossy fallen log, broken ends, bark peeling, mushrooms growing on it" · 3 variants · 800 tris · scatter · collider: capsule. ⭐ *(Wolfwood, Brackenvale)*
- [TRE-18] **Tree Stump** — Cut and broken stumps, with and without an axe in them. Prompt: "old tree stump with roots, one with a woodcutter's axe stuck in it" · 3 variants · 600 tris · scatter · collider: cylinder. *(all forests)*
- [TRE-19] **Ancient Yew** — A dark, wide, very old yew for the burying ground on the northern hill; the old graveyard tree, and a silhouette you can pick out from the village square (WLD-45). Prompt: "ancient yew tree, massive hollow fluted trunk made of several fused stems, dense dark evergreen needle foliage in heavy layered sprays, low wide spreading crown, gnarled exposed roots" · 2 variants · HD ~20k tris · placed (burying ground) + a few scattered on the hill · collider: trunk capsule. *(Brackenvale)*
- [TRE-20] **Riverside Willow** — A healthy green weeping willow along Brackenvale's river and ponds; the bright cousin of the Blackmire's swamp willow (TRE-08). Prompt: "weeping willow tree on a riverbank, thick leaning trunk, long graceful curtains of fresh green hanging branches reaching almost to the ground, light airy foliage" · 2 variants · HD ~20k tris · scatter along water (shore placement) · collider: trunk capsule. *(Brackenvale)*
- [TRE-21] **Hawthorn** — A small crooked tree bent by the wind, for hedgerows, field edges and lone spots on hillsides; sits between the bushes and the full-size oaks. Prompt: "small old hawthorn tree bent by the wind, crooked twisting thorny trunk, dense rounded crown of small leaf clusters, white blossom and a few red berries" · 2 variants · HD ~12k tris · scatter (field edges, hedgerows, hillsides) · collider: trunk capsule. *(Brackenvale)*
- [TRE-22] **Field Maple** — A rounder, lighter-green broadleaf so the woods aren't only oak and birch. Prompt: "field maple tree, short sturdy trunk, dense round bushy crown of distinct leaf clusters, lobed leaves, bright fresh green turning gold at the edges" · 2 variants · HD ~20k tris · scatter (mixed into the oak groves) · collider: trunk capsule. *(Brackenvale)*

## 2. Plants & Ground Cover (PLT)

- [PLT-01] **Meadow Bush** — Round green bush for Brackenvale. Prompt: "round leafy green bush, chunky foliage" · 3 variants · 1.5k tris · scatter · collider: none. ⭐ *(Brackenvale)*
- [PLT-02] **Bracken Fern Clump** — Tall fern clumps the Vale is named after. Prompt: "clump of tall bracken ferns, curling fronds" · 3 variants · 400 tris · scatter · collider: none. ⭐ *(Brackenvale, Wolfwood)*
- [PLT-03] **Wildflower Patch** — Clusters of small colorful flowers. Prompt: "small patch of wildflowers, poppies, cornflowers and daisies" · 3 variants · 300 tris · scatter · collider: none. *(Brackenvale)*
- [PLT-04] **Bramble Thicket** — Thorny bushes that block paths and hide secrets. Prompt: "low wide mound of arching thorny bramble canes, chunky clumps of dark green leaves, clusters of black blackberries" · 2 variants · 2k tris · scatter · collider: box. *(Brackenvale, Wolfwood)*
- [PLT-05] **Forest Mushrooms** — Clusters of mushrooms on the forest floor. Prompt: "cluster of forest mushrooms, brown and red caps, different sizes" · 3 variants · 300 tris · scatter · collider: none. ⭐ *(Wolfwood)*
- [PLT-06] **Giant Toadstool** — Huge toadstools in the deep woods. Prompt: "giant toadstool mushroom taller than a person, spotted cap, thick stem" · 2 variants · 1k tris · scatter · collider: cylinder. *(Wolfwood)*
- [PLT-07] **Reeds & Cattails** — Tall reeds along every shore. Prompt: "clump of tall reeds and cattails, marsh plants" · 3 variants · 400 tris · scatter · collider: none. ⭐ *(Blackmire, shores)*
- [PLT-08] **Lily Pads** — Floating pads and flowers on still water. Prompt: "cluster of floating lily pads with two white water lily flowers, flat" · 2 variants · 200 tris · scatter (on water) · collider: none. *(Blackmire)*
- [PLT-09] **Hanging Moss Curtain** — Moss strands that hang from branches and ruins. Prompt: "long strands of hanging grey-green moss, drooping curtain" · 2 variants · 300 tris · placed/scatter · collider: none. *(Blackmire)*
- [PLT-10] **Glowcap Fungus** — Bioluminescent fungus for night and caves (emissive). Prompt: "cluster of glowing blue bioluminescent fungus on a rock" · 2 variants · 400 tris · scatter · collider: none. *(Blackmire, Crypts)*
- [PLT-11] **Snow Shrub** — Low, snow-covered juniper. Prompt: "low snow-covered juniper shrub, frosted branches" · 2 variants · 400 tris · scatter · collider: none. ⭐ *(Frostfang)*
- [PLT-12] **Ice Crystals** — Jagged blue ice crystals jutting from the snow. Prompt: "cluster of jagged blue ice crystals" · 3 variants · 400 tris · scatter · collider: hull. *(Frostfang)*
- [PLT-13] **Ash Scrub** — Dry, burnt, spiky shrubs. Prompt: "dry burnt spiky shrub, black and grey twigs, volcanic" · 2 variants · 300 tris · scatter · collider: none. ⭐ *(Ashen Reach)*
- [PLT-14] **Black Thornbush** — Barbed black bushes around Duskhold. Prompt: "black thornbush with long barbed thorns, dark fantasy" · 2 variants · 500 tris · scatter · collider: box. *(Duskhold)*
- [PLT-15] **Cottage Garden Bed** — A low bed of mixed cottage flowers against a cottage wall. Prompt: "low cottage garden flower bed, hollyhocks, foxgloves and marigolds, small stone edging" · 2 variants · 800 tris · placed by cottages · collider: none. *(Brackenvale)*
- [PLT-16] **Lavender Bush** — Round bushes of purple lavender by the market and the farms; Granny Maud sells it (NPC-09). Prompt: "round lavender bush with tall purple flower spikes" · 2 variants · 500 tris · scatter · collider: none. *(Brackenvale)*
- [PLT-17] **Climbing Rose** — Red and pink roses climbing a wooden trellis, for cottage walls and gates. Prompt: "climbing rose bush on a simple wooden trellis, red and pink roses" · 2 variants · 900 tris · placed against walls · collider: none. *(Brackenvale)*
- [PLT-18] **Sunflower Row** — A short row of tall sunflowers at the edge of a vegetable plot. Prompt: "short row of tall sunflowers, big yellow heads, green leaves" · 2 variants · 700 tris · placed at farm plots · collider: none. *(Brackenvale)*
- [PLT-19] **Window Flower Box** — A wooden box of red geraniums under a cottage window. Prompt: "wooden window flower box with red geraniums and trailing ivy" · 1 variant · 300 tris · placed under windows · collider: none. *(Brackenvale)*

## 3. Rocks & Stone (RCK)

- [RCK-01] **Mossy Boulder** — Rounded boulders with moss on top. Prompt: "large rounded mossy boulder, granite, moss on top" · 4 variants · 800 tris · scatter · collider: hull. ⭐ *(Brackenvale, Wolfwood)*
- [RCK-02] **Rock Cluster** — Small group of rocks; general dressing. Prompt: "cluster of small and medium grey rocks" · 3 variants · 600 tris · scatter · collider: hull. ⭐ *(all)*
- [RCK-03] **Cliff Chunk** — Big angular rock faces to break up steep slopes. Prompt: "large angular cliff rock chunk, layered stone face, weathered" · 4 variants · 2k tris · scatter (steep slopes) · collider: hull. ⭐ *(all mountains)*
- [RCK-04] **Standing Stone** — Tall carved menhir; circles of them dot the Vale. Prompt: "tall ancient standing stone menhir, weathered, faint carved spirals, lichen" · 3 variants · 600 tris · placed · collider: box. ⭐ *(Brackenvale)*
- [RCK-05] **Swamp Stone** — Slimy, half-sunk rocks. Prompt: "slimy dark half-sunken swamp rock, algae and moss" · 3 variants · 600 tris · scatter · collider: hull. *(Blackmire)*
- [RCK-06] **Stepping Stones** — Flat stones crossing shallow water. Prompt: "row of flat round stepping stones" · 2 variants · 400 tris · placed · collider: boxes. *(Blackmire, streams)*
- [RCK-07] **Snowy Boulder** — Boulder with a snow cap. Prompt: "granite boulder with a thick snow cap, icicles" · 3 variants · 800 tris · scatter · collider: hull. ⭐ *(Frostfang)*
- [RCK-08] **Obsidian Shard** — Glassy black spikes jutting from the ash. Prompt: "jagged black obsidian rock shards, glassy, pointing upward" · 3 variants · 800 tris · scatter · collider: hull. ⭐ *(Ashen Reach)*
- [RCK-09] **Lava Rock** — Porous dark rocks with glowing seams (emissive). Prompt: "porous black volcanic rock with glowing orange lava cracks" · 3 variants · 700 tris · scatter · collider: hull. *(Ashen Reach)*
- [RCK-10] **Basalt Columns** — Hexagonal columns forming steps and cliffs. Prompt: "group of hexagonal basalt columns of different heights" · 2 variants · 1.5k tris · placed · collider: boxes. *(Ashen Reach)*
- [RCK-11] **Dark Spire Rock** — Tall black rock spires around the crag. Prompt: "tall jagged black rock spire, sharp, dark fantasy" · 3 variants · 1.2k tris · scatter · collider: hull. *(Duskhold)*
- [RCK-12] **Natural Rock Arch** — A landmark arch to walk under. Prompt: "natural stone rock arch, weathered sandstone, large" · 1 variant · 3k tris · placed · collider: hull pieces. *(any biome)*

## 4. Brackenvale Village (VIL)

- [VIL-01] **Thatched Cottage** — Rowan's village home style, intact. Prompt: "small medieval thatched-roof cottage, timber frame and white plaster, stone chimney, wooden door" · 2 variants · 4k tris · placed · collider: box. ⭐ *(Brackenvale Village)*
- [VIL-02] **Burned Cottage** — The same cottage after the raid: roof gone, walls blackened. Prompt: "burned-out medieval cottage ruin, collapsed thatched roof, charred timber frame, blackened walls" · 3 variants · 4k tris · placed · collider: boxes. ⭐ *(Brackenvale Village, STY-14)*
- [VIL-03] **Fenhallow Farmhouse** — Rowan's family home: slightly bigger, with a porch. Prompt: "medieval farmhouse with a covered porch, thatched roof, stone base, partly burned on one side" · 1 variant · 6k tris · placed · collider: boxes. *(Brackenvale Village)*
- [VIL-04] **Barn** — Large timber barn. Prompt: "large wooden medieval barn, big double doors, hay loft" · 1 variant · 4k tris · placed · collider: box. *(Brackenvale)*
- [VIL-05] **Burned Windmill** — The landmark: a stone windmill with broken, scorched sails. Prompt: "stone windmill with broken scorched wooden sails, smoke-blackened walls" · 1 variant · 6k tris · placed · collider: cylinder. ⭐ *(Brackenvale landmark, WLD-13)*
- [VIL-06] **Village Well** — Stone well with roof and bucket. Prompt: "medieval stone village well with small wooden roof, rope and bucket" · 1 variant · 1.5k tris · placed · collider: cylinder. ⭐ *(Brackenvale Village)*
- [VIL-07] **Smithy** — Open-sided forge with anvil and bellows. Prompt: "small open-sided village smithy, stone forge, anvil, bellows, tools on the wall" · 1 variant · 5k tris · placed · collider: boxes. *(Brackenvale Village)*
- [VIL-08] **Village Chapel** — Small stone chapel with a bell tower. Prompt: "small stone village chapel with a bell tower, arched door, slate roof" · 1 variant · 6k tris · placed · collider: boxes. *(Brackenvale Village)*
- [VIL-09] **Market Stall** — Wooden stall with a cloth awning. Prompt: "medieval market stall with striped cloth awning, wooden counter, baskets of goods" · 2 variants · 1.5k tris · placed · collider: box. *(Brackenvale Village)*
- [VIL-10] **Haycart** — Farm cart, one broken. Prompt: "wooden farm cart loaded with hay, large spoked wheels" · 2 variants · 1.5k tris · placed · collider: box. *(Brackenvale)*
- [VIL-11] **Hay Bales** — Round and square bales. Prompt: "stack of square hay bales and one round hay bale" · 2 variants · 500 tris · scatter · collider: box. *(Brackenvale)*
- [VIL-12] **Scarecrow** — A ragged scarecrow in the fields (a fine place for crows). Prompt: "ragged scarecrow on a wooden pole, straw stuffing, burlap head, old hat" · 2 variants · 800 tris · placed · collider: capsule. *(Brackenvale)*
- [VIL-13] **Cow** — A farm cow for the Fenhallow fields and pastures; grazes and wanders, harmless. Prompt: "sturdy brown and white farm cow with short horns, standing still on all four legs, legs straight, head level and looking straight ahead, symmetrical neutral stance, not walking" · 1 variant · 6k tris · animated (quadruped rig) · collider: capsule. *(Brackenvale farms)*

## 5. Buildings & Ruins Elsewhere (BLD)

- [BLD-01] **Ruined Watchtower** — Landmark: a broken round tower you can climb. Prompt: "ruined round stone watchtower, collapsed top, broken spiral stairs visible, ivy" · 1 variant · 6k tris · placed · collider: boxes. ⭐ *(Brackenvale landmark)*
- [BLD-02] **Ruined Wall Section** — Broken stone walls for ruins everywhere. Prompt: "ruined medieval stone wall section, broken top, fallen stones, moss" · 4 variants · 1k tris · scatter/placed · collider: box. ⭐ *(all)*
- [BLD-03] **Ruined Archway** — Freestanding broken arch. Prompt: "ruined stone archway, cracked, partially collapsed, vines" · 2 variants · 1.5k tris · placed · collider: boxes. *(all)*
- [BLD-04] **Broken Pillar** — Toppled and standing column stumps. Prompt: "broken ancient stone column, toppled fragments, weathered" · 3 variants · 600 tris · scatter · collider: cylinder. *(all ruins)*
- [BLD-05] **Hunter's Lodge** — Log cabin in the Wolfwood; a Waystone stands beside it. Prompt: "rustic log cabin hunting lodge, antlers above the door, stone chimney, firewood stack" · 1 variant · 5k tris · placed · collider: box. *(Wolfwood)*
- [BLD-06] **Stilt Hut** — Swamp hut raised on poles. Prompt: "rickety swamp hut on wooden stilts, reed roof, rope ladder, hanging nets" · 2 variants · 3k tris · placed · collider: boxes. ⭐ *(Blackmire)*
- [BLD-07] **Witch's Hut** — Old Mother Mire's crooked home (BOS-03). Prompt: "crooked witch's hut on stilts in a swamp, skulls and charms hanging, bubbling cauldron outside, twisted roof" · 1 variant · 6k tris · placed · collider: boxes. *(Blackmire landmark)*
- [BLD-08] **Sunken Shrine** — Half-flooded stone shrine. Prompt: "half-sunken ancient stone shrine, pillars and a small dome, flooded, algae" · 1 variant · 4k tris · placed · collider: boxes. *(Blackmire)*
- [BLD-09] **Summit Shelter** — Stone mountain hut with a sloped roof. Prompt: "small stone mountain shelter hut, heavy snow on slate roof, wooden door" · 1 variant · 3k tris · placed · collider: box. *(Frostfang)*
- [BLD-10] **Ice Cave Mouth** — Entrance arch of blue ice, for ice caves. Prompt: "entrance to an ice cave, arch of blue glacier ice, icicles" · 1 variant · 3k tris · placed · collider: hull pieces. *(Frostfang)*
- [BLD-11] **Cinder Forge** — Giant ruined forge where the Colossus lies (BOS-05). Prompt: "huge ruined ancient forge, giant anvil, cracked stone furnace with lava glow, chains" · 1 variant · 10k tris · placed · collider: boxes. *(Ashen landmark)*
- [BLD-12] **Rune Pillar** — Carved pillars with glowing runes, golem ruins. Prompt: "tall carved stone pillar with glowing blue abstract runes, ancient" · 2 variants · 1k tris · placed · collider: box. *(Ashen Reach, ruins)*
- [BLD-13] **Sunken Crypts Entrance** — Stone stairway down into the Crypts (WLD-07). Prompt: "stone crypt entrance in a hillside, stairs going down, carved stone door frame, iron gate" · 1 variant · 4k tris · placed · collider: boxes. *(Brackenvale landmark)*

## 6. Walls, Fences, Bridges & Water (STR)

- [STR-01] **Wooden Fence** — Split-rail fence segments and gates. Prompt: "wooden split-rail fence segment, rustic" · Gate prompt: "rustic wooden farm gate between two thick fence posts, split-rail style, closed, iron hinges and latch" · 2 variants (straight, gate) · 300 tris · kit · collider: box. ⭐ *(Brackenvale)*
- [STR-02] **Dry Stone Wall** — Low field walls along roads. Prompt: "low dry stone field wall segment, stacked flat stones" · 2 variants · 600 tris · kit · collider: box. ⭐ *(Brackenvale)*
- [STR-03] **Stone Bridge** — Arched bridge over streams. Prompt: "arched medieval stone bridge, single span, low walls" · 1 variant · 3k tris · placed · collider: boxes. *(roads)*
- [STR-04] **Troll Bridge** — Landmark: a big old bridge with a dark arch underneath (there's a troll). Prompt: "large old stone bridge over a swamp, dark arch underneath, bones and junk under the arch, moss" · 1 variant · 6k tris · placed · collider: boxes. ⭐ *(Blackmire landmark)*
- [STR-05] **Rope Bridge** — Plank bridge over gorges. Prompt: "wooden plank rope bridge, sagging, frayed ropes" · 1 variant · 2k tris · placed · collider: boxes. *(Frostfang, Wolfwood)*
- [STR-06] **Boardwalk** — Swamp walkway sections on posts. Prompt: "section of wooden swamp boardwalk on posts, uneven planks" · 2 variants (straight, corner) · 500 tris · kit · collider: box. ⭐ *(Blackmire)*
- [STR-07] **Wooden Dock** — Short pier with mooring posts. Prompt: "small wooden fishing dock on posts, mooring posts, rope" · 1 variant · 1.5k tris · placed · collider: boxes. *(lakes, Blackmire)*
- [STR-08] **Rowboat** — Intact and sunk/rotting versions. Prompt: "small wooden rowboat with oars" · 2 variants (intact, rotting) · 800 tris · placed · collider: box. *(lakes, Blackmire)*
- [STR-09] **Fishing Hut** — Hut by a lake for the fishing pond (WLD-22). Prompt: "small lakeside fishing hut, nets drying, fishing rods, wooden" · 1 variant · 3k tris · placed · collider: box. *(later)*
- [STR-10] **Waterfall Rocks** — Rock lip and pool stones where a waterfall shader goes. Prompt: "rocky cliff ledge for a waterfall, smooth worn stones, pool rocks at the base" · 1 variant · 3k tris · placed · collider: hull. *(Frostfang, Wolfwood)*
- [STR-11] **Palisade Wall** — Sharpened log walls for camps. Prompt: "wooden palisade wall segment, sharpened logs, rope lashings" · 2 variants · 600 tris · kit · collider: box. ⭐ *(Ashen warcamp, bandit camps)*
- [STR-12] **Wooden Gate** — Palisade gate with a lift bar; doubles as a shortcut gate (WLD-10). Prompt: "heavy wooden double gate in a log palisade, iron bands, crossbar" · 1 variant · 1.2k tris · placed · collider: box. *(camps)*

## 7. Landmarks (LMK)

- [LMK-01] **The Frozen Giant** — A giant frozen mid-stride in a glacier; the Frostfang landmark. Prompt: "colossal giant frozen inside a glacier, only head, shoulder and one arm visible through the ice" · 1 variant · 15k tris · placed · collider: hull pieces. *(Frostfang landmark)*
- [LMK-02] **Wyvern Roost** — Nest of bones and branches on a cliff (BOS-04). Prompt: "huge wyvern nest on a cliff top, woven from broken trees and bones, large eggs" · 1 variant · 8k tris · placed · collider: hull. *(Frostfang)*
- [LMK-03] **Orc Warcamp Centerpiece** — Big war totem with skulls and banners. Prompt: "tall orc war totem pole, carved faces, horned skulls, torn red banners" · 1 variant · 3k tris · placed · collider: cylinder. *(Ashen Reach)*
- [LMK-04] **Grimtooth's Clearing Altar** — Bone-strewn stone in the boss clearing (BOS-01). Prompt: "flat sacrificial stone surrounded by bones and claw marks, wolf skulls" · 1 variant · 2k tris · placed · collider: box. ⭐ *(Wolfwood boss arena)*
- [LMK-05] **Ancient Hero Statue** — Huge weathered statue of the old hero holding a sword (the Dawnblade's first owner). Prompt: "huge weathered stone statue of an ancient hero raising a sword, cloak, cracked and mossy, on a plinth" · 1 variant · 8k tris · placed · collider: boxes. *(Brackenvale or Wolfwood)*
- [LMK-06] **Giant Skeleton** — The bones of a dragon-sized beast half-buried in the badlands. Prompt: "half-buried skeleton of a giant dragon, huge ribcage arching out of the ground, skull" · 1 variant · 10k tris · placed · collider: capsules. *(Ashen Reach)*

## 8. Duskhold Citadel (DSK)

- [DSK-01] **Citadel Gatehouse** — The great gate at the top of the King's Road. Prompt: "massive dark fortress gatehouse, two tall black stone towers, huge iron portcullis, spikes" · 1 variant · 12k tris · placed · collider: boxes. *(Duskhold)*
- [DSK-02] **Citadel Wall Segment** — Black crenellated wall pieces (combined with the scripted kit). Prompt: "black stone fortress wall segment with crenellations and spikes" · 2 variants (straight, corner) · 2k tris · kit · collider: box. *(Duskhold)*
- [DSK-03] **Citadel Tower** — Tall spiked tower. Prompt: "tall dark fantasy fortress tower, black stone, spiked roof, narrow glowing windows" · 2 variants · 6k tris · placed · collider: cylinder. *(Duskhold)*
- [DSK-04] **Dark Lord Statue** — Menacing statue of Malgrath. Prompt: "tall menacing statue of a crowned dark sorcerer-king in robes, black stone, glowing eyes" · 1 variant · 6k tris · placed · collider: box. *(Duskhold)*
- [DSK-05] **Chained Brazier** — Iron braziers with purple-black fire (the flame is VFX-08). Prompt: "iron brazier on a tripod with chains and spikes, dark fantasy" · 1 variant · 800 tris · placed · collider: cylinder. *(Duskhold)*
- [DSK-06] **Duskhold Banner** — Tattered war banner on a pole. Prompt: "tattered black and purple war banner on a spiked pole, abstract crown sigil" · 2 variants · 600 tris · placed · collider: capsule. ⭐ *(Duskhold, warcamps)*
- [DSK-07] **Spiked Barricade** — Wooden stake barricades along the approach. Prompt: "wooden spiked barricade, crossed sharpened stakes" · 2 variants · 600 tris · scatter · collider: box. *(Duskhold approach)*

## 9. Gameplay Objects (INT)

- [INT-01] **Waystone** — The rest point (WLD-09): a carved stone with a hollow where the light glows when lit (glow is a shader). Prompt: "waist-high carved standing stone shrine with a hollow niche at the top, worn runes, small stone base" · 1 variant · 1.5k tris · placed · collider: cylinder. ⭐ *(everywhere)*
- [INT-02] **Wooden Chest** — The common chest. Prompt: "wooden treasure chest with iron bands and a lock, closed lid" · 1 variant · 800 tris · placed · collider: box. ⭐ *(WLD-17)*
- [INT-03] **Iron Chest** — The better chest. Prompt: "heavy iron-bound treasure chest with ornate metal corners and studs" · 1 variant · 1k tris · placed · collider: box. *(dungeons)*
- [INT-04] **Ornate Chest** — Boss and secret chest. Prompt: "ornate gilded treasure chest with carvings and a gem on the lid" · 1 variant · 1.2k tris · placed · collider: box. *(bosses, secrets)*
- [INT-05] **Mimic Chest Body** — The mimic (ENM-21), opened with teeth and tongue (needs rigging). Prompt: "monster mimic treasure chest, lid open with sharp teeth and long tongue" · 1 variant · 3k tris · enemy · collider: box. *(later)*
- [INT-06] **Shortcut Lever** — Wall lever that opens gates (WLD-10). Prompt: "large iron wall lever on a stone base" · 1 variant · 400 tris · placed · collider: box. *(dungeons)*
- [INT-07] **Ladder** — Wooden ladder for shortcuts and climbs. Prompt: "tall wooden ladder" · 1 variant · 300 tris · placed · collider: box. *(everywhere)*
- [INT-08] **Iron Portcullis** — Gate that rises and falls. Prompt: "iron portcullis gate, grid of bars with spikes at the bottom" · 1 variant · 500 tris · placed · collider: box. *(dungeons, Duskhold)*
- [INT-09] **Mist Gate Arch** — Stone frame the boss mist wall fills (BOS-08; the mist is a shader). Prompt: "tall weathered stone archway frame, carved pillars, empty opening" · 1 variant · 1.5k tris · placed · collider: boxes. ⭐ *(boss arenas)*
- [INT-10] **Training Dummy** — Straw dummy for testing combat. Prompt: "straw training dummy on a wooden post, burlap sack head, crossbar arms" · 1 variant · 600 tris · placed · collider: capsule. ⭐ *(Brackenvale)*
- [INT-11] **Signpost** — Wooden road signs at junctions (shapes, no text). Prompt: "wooden signpost with three pointed arrow boards, blank" · 1 variant · 300 tris · placed · collider: capsule. *(roads)*
- [INT-12] **Breakable Pot** — Clay pots that shatter (and maybe hold something). Prompt: "set of clay pots of different sizes, earthenware" · 3 variants · 300 tris · scatter · collider: cylinder. *(everywhere, OoT-style)*
- [INT-13] **Explosive Barrel** — Red-banded barrel of black powder (CMB-31). Prompt: "wooden barrel with red bands and a fuse, black powder" · 1 variant · 500 tris · placed · collider: cylinder. *(camps)*
- [INT-14] **Cracked Wall** — Bombable wall patch hiding a secret (WLD-16). Prompt: "cracked stone wall section with a visible crumbling weak spot" · 1 variant · 800 tris · placed · collider: box. *(dungeons)*
- [INT-15] **Spike Trap** — Floor plate with spikes (CMB-31). Prompt: "metal floor spike trap plate with sharp spikes raised" · 1 variant · 500 tris · placed · collider: box. *(dungeons)*

## 10. Camps & Clutter (CLT)

- [CLT-01] **Barrel** — Plain wooden barrels. Prompt: "wooden barrel" · 2 variants · 300 tris · scatter · collider: cylinder. ⭐ *(everywhere)*
- [CLT-02] **Crate** — Wooden crates and stacks. Prompt: "stack of wooden supply crates" · 2 variants · 300 tris · scatter · collider: box. ⭐ *(everywhere)*
- [CLT-03] **Grain Sacks** — Burlap sacks. Prompt: "pile of burlap grain sacks" · 1 variant · 400 tris · scatter · collider: box. *(village, camps)*
- [CLT-04] **Campfire** — Stone ring with logs (the fire is VFX-06). Prompt: "campfire stone ring with stacked logs and ash, unlit" · 1 variant · 500 tris · placed · collider: cylinder. ⭐ *(camps)*
- [CLT-05] **Bandit Tent** — Patched canvas tent. Prompt: "patched canvas bandit tent, wooden poles, ropes" · 2 variants · 1.5k tris · placed · collider: box. ⭐ *(bandit camps)*
- [CLT-06] **Orc War Tent** — Hide tent with bone decorations. Prompt: "large orc war tent made of animal hides, bone and tusk decorations" · 2 variants · 2k tris · placed · collider: box. *(Ashen warcamp)*
- [CLT-07] **Weapon Rack** — Rack with spears and swords. Prompt: "wooden weapon rack holding spears, swords and an axe" · 1 variant · 1k tris · placed · collider: box. *(camps)*
- [CLT-08] **Goblin Junk Pile** — Heap of stolen junk and shiny things. Prompt: "messy pile of stolen junk, broken pots, rusty pans, coins and trinkets" · 2 variants · 800 tris · placed · collider: hull. *(goblin camps)*
- [CLT-09] **Cooking Spit** — Spit over a fire with a roasting animal. Prompt: "campfire cooking spit with a roasting boar, wooden supports" · 1 variant · 800 tris · placed · collider: box. *(camps)*
- [CLT-10] **Lantern Post** — Hanging lantern on a post (light is code). Prompt: "wooden post with a hanging iron lantern" · 1 variant · 400 tris · placed · collider: capsule. *(roads, village)*
- [CLT-11] **Wall Torch** — Iron sconce with a torch (the flame is VFX-07). Prompt: "iron wall torch sconce holding a wooden torch" · 1 variant · 200 tris · placed · collider: none. *(dungeons)*
- [CLT-12] **War Drum** — Big orc drum. Prompt: "large orc war drum, stretched hide, bone drumsticks" · 1 variant · 800 tris · placed · collider: cylinder. *(Ashen warcamp)*
- [CLT-13] **Cage** — Hanging and floor cages. Prompt: "rusty iron cage, hanging from a chain" · 2 variants · 600 tris · placed · collider: box. *(camps, Duskhold)*
- [CLT-14] **Bones & Skulls** — Scattered remains for monster lairs. Prompt: "scattered pile of old bones and skulls" · 3 variants · 400 tris · scatter · collider: none. ⭐ *(lairs, Crypts)*
- [CLT-15] **Spider Egg Sacs** — Clusters of eggs in webs (Spider Grove). Prompt: "cluster of pale spider egg sacs in sticky web" · 2 variants · 500 tris · placed · collider: hull. *(Wolfwood)*

## 11. Crypt Dressing (DNG)

- [DNG-01] **Tombstones** — Old gravestones, leaning and broken. Prompt: "set of old leaning tombstones, cracked, moss" · 3 variants · 300 tris · scatter · collider: box. *(Crypts, graveyards)*
- [DNG-02] **Sarcophagus** — Stone coffin with a carved lid. Prompt: "stone sarcophagus with a carved knight on the lid" · 2 variants (closed, open) · 1.5k tris · placed · collider: box. *(Crypts)*
- [DNG-03] **Bone Pile Alcove** — Wall niche stacked with skulls. Prompt: "stone wall alcove filled with stacked skulls and bones, catacomb" · 1 variant · 1.5k tris · kit · collider: box. *(Crypts)*
- [DNG-04] **Candle Cluster** — Melted candles (the flames are VFX-09). Prompt: "cluster of melted wax candles of different heights" · 2 variants · 300 tris · placed · collider: none. *(Crypts, shrines)*
- [DNG-05] **Necromancer's Altar** — Altar with a ritual circle (ENM-22). Prompt: "dark stone ritual altar with skulls, black candles and a carved circle" · 1 variant · 2k tris · placed · collider: box. *(Crypts)*
- [DNG-06] **Cobweb Corner** — Webs for ceilings and corners. Prompt: "thick dusty cobweb, flat, spanning a corner" · 2 variants · 200 tris · placed · collider: none. *(Crypts)*

## 12. Items, Weapons & Pickups (ITM)

- [ITM-01] **Dawnblade, Rusty** — Stage 1: grandfather's old, dull sword (ART-17). Prompt: "old rusty longsword, plain crossguard, leather-wrapped grip, chipped blade" · 1 variant · 2k tris · held · collider: none. ⭐ *(HER-10)*
- [ITM-02] **Dawnblade, Restored** — Stage 2: clean steel with a gold inlay. Prompt: "elegant longsword with polished steel blade, gold inlay along the fuller, ornate crossguard" · 1 variant · 2.5k tris · held · collider: none. *(HER-10)*
- [ITM-03] **Dawnblade, Awakened** — Stages 3–4: sun motif on the guard, a gem in the pommel (glow is a shader). Prompt: "legendary holy longsword, sun-shaped crossguard, glowing gem in the pommel, engraved blade" · 1 variant · 3k tris · held · collider: none. *(HER-10)*
- [ITM-04] **Rowan's Buckler** — Small round wooden shield with an iron rim. Prompt: "small round wooden buckler shield with iron rim and boss, worn" · 1 variant · 800 tris · held · collider: none. ⭐ *(HER-09)*
- [ITM-05] **Hand Crossbow** — Rowan's crossbow (CMB-20). Prompt: "compact one-handed crossbow, wood and iron, small" · 1 variant · 1.5k tris · held · collider: none. ⭐ *(CMB-20)*
- [ITM-06] **Crossbow Bolts** — Iron, blessed and fire bolts. Prompt: "three crossbow bolts: plain iron, silver-tipped, and one with an oil-soaked rag" · 1 variant · 200 tris · held/projectile · collider: none. *(CMB-20)*
- [ITM-07] **Lifewater Flask** — The healing flask (CMB-22). Prompt: "glass flask with a cork, filled with glowing pale green liquid, leather strap" · 1 variant · 400 tris · held · collider: none. ⭐ *(CMB-22)*
- [ITM-08] **Heart Shard** — Collectible max-HP shard (STA-11). Prompt: "small crystal shard shaped like a quarter of a heart, red, glowing" · 1 variant · 200 tris · pickup · collider: sphere. ⭐ *(STA-11)*
- [ITM-09] **Crown Shard** — One of the four pieces of the Crown of Dawn (STY-03). Prompt: "broken golden crown fragment with a large gem, ancient, glowing" · 4 variants (one per shard) · 800 tris · pickup · collider: sphere. *(STY-03)*
- [ITM-10] **Upgrade Ore** — Ore chunks for weapon upgrades (CMB-24). Prompt: "chunk of raw ore with shiny blue metal veins" · 3 variants (tiers) · 300 tris · pickup · collider: sphere. *(CMB-24)*
- [ITM-11] **Firebomb & Holy Water** — Throwables (CMB-21). Prompt: "clay firebomb with a cloth fuse, and a small glass vial of holy water" · 1 variant each · 300 tris · held · collider: none. *(CMB-21)*
- [ITM-12] **Key** — Dungeon and boss keys. Prompt: "large ornate iron dungeon key, and a big skull-shaped boss key" · 2 variants · 300 tris · pickup · collider: sphere. *(dungeons)*
- [ITM-13] **Boss Masks** — Trophy masks (VAL-07). Prompt: "tribal-style trophy mask made from a monster's skull" · 1 per boss · 800 tris · pickup/worn · collider: none. *(VAL-07)*
- [ITM-14] **Weapon Set** — Axe, mace, spear and greatsword (CMB-23). Prompt: "medieval weapon: [battle axe | flanged mace | long spear | greatsword], worn steel" · 1 per weapon · 1.5k tris · held · collider: none. *(CMB-23)*
- [ITM-15] **Essence Remnant** — The spot where your dropped XP waits after death (CMB-30). Prompt: "small glowing wisp-shaped crystal on the ground" · 1 variant · 200 tris · pickup · collider: sphere. *(CMB-30)*

## 13. Effects (VFX)

*Rite and fire effects made as Meshy meshes (ART-19), since there are no particles. Each mesh is drawn with a glowing, see-through shader and animated in code: scale up, spin, pulse, fade out. Prompts ask for a **simple solid shape**; the glow, color and transparency come from the shader, not the texture. Budgets are small because several can be on screen at once.*

- [VFX-01] **Flash Burst** — The *Flash* Rite (CMB-29): a starburst of radiant light that expands from Rowan's hand and fades in 0.3 s. Prompt: "stylized starburst shape with long sharp rays, flat, simple solid form, light effect" · 2 variants · 300 tris · effect · collider: none. ⭐ *(CMB-29)*
- [VFX-02] **Ward Dome** — The *Ward* Rite: a hexagon-patterned half-dome around Rowan that ripples when hit and shatters when it breaks (a second, cracked variant for the break). Prompt: "half dome shield made of hexagonal panels, simple geometric, energy barrier" · 2 variants (whole, shattered) · 800 tris · effect · collider: sphere (the ward itself). ⭐ *(CMB-29)*
- [VFX-03] **Mark Sigil** — The *Mark* Rite: a rotating rune circle floating over the marked enemy. Prompt: "flat circular magic sigil ring with abstract carved runes, thin, simple" · 1 variant · 400 tris · effect · collider: none. ⭐ *(CMB-29)*
- [VFX-04] **Cast Circle** — A small rune circle that appears at Rowan's off hand while any Rite is cast; tinted per Rite. Prompt: "small flat magic circle with concentric rings and abstract runes" · 1 variant · 300 tris · effect · collider: none. ⭐ *(CMB-29, CMB-34)*
- [VFX-05] **Radiant Slash Arc** — A crescent of light that trails Faith-scaled radiant hits (STA-20), so you can see when holy damage lands. Prompt: "thin crescent moon arc shape, smooth, tapered ends, light trail" · 2 variants · 200 tris · effect · collider: none. *(STA-20)*
- [VFX-06] **Campfire Flame** — Stylized flame tongues for campfires (CLT-04); the shader scrolls a gradient up through it so it flickers. Prompt: "stylized cartoon campfire flames, several tall flame tongues, simple solid shape" · 2 variants · 400 tris · effect · collider: none. ⭐ *(CLT-04)*
- [VFX-07] **Torch Flame** — A single small flame for wall torches and lantern posts (CLT-10, CLT-11). Prompt: "single stylized torch flame, teardrop shape with a curling tip, simple solid" · 2 variants · 150 tris · effect · collider: none. *(CLT-10, CLT-11)*
- [VFX-08] **Dark Flame** — Twisting purple-black flame for Duskhold braziers (DSK-05). Prompt: "twisting stylized flame with sharp jagged tongues, simple solid shape" · 1 variant · 400 tris · effect · collider: none. *(DSK-05)*
- [VFX-09] **Candle Flames** — Tiny flame set for candle clusters (DNG-04). Prompt: "set of tiny teardrop candle flames, simple" · 1 variant · 60 tris · effect · collider: none. *(DNG-04)*
- [VFX-10] **Firebomb Blast** — The burst when a firebomb (CMB-21) lands: a fiery ring and a puff that expand and fade. Prompt: "stylized explosion burst, rounded billowing fire puffs, cartoon, simple solid shape" · 2 variants · 600 tris · effect · collider: sphere (blast radius). *(CMB-21)*
- [VFX-11] **Holy Water Splash** — A crown-shaped splash for holy water (CMB-21). Prompt: "stylized water splash crown shape, droplets rising, simple solid" · 1 variant · 400 tris · effect · collider: sphere. *(CMB-21)*
- [VFX-12] **Smoke Puff** — A cluster of rounded smoke clouds for smoke bombs (CMB-21) and the enemy-death dissolve. Prompt: "cluster of rounded cartoon smoke clouds, simple puffy solid shape" · 2 variants · 500 tris · effect · collider: none. *(CMB-21)*
- [VFX-13] **Relic Power Shapes** — One mesh per relic power (VAL-03): a spiral gust for *Gale*, ice spikes for *Frostward*, a cracked ground ring for *Earthshaker*, a flame ring for *Flame Ring*. Prompt: "[spiral wind gust | ring of ice spikes | cracked rock shockwave ring | ring of flames], stylized, simple solid shape" · 1 each · 600 tris · effect · collider: per power. *(VAL-03)*
- [VFX-14] **Waystone Glow Wisp** — A soft floating orb with two orbiting motes over a lit Waystone (INT-01). Prompt: "small smooth glowing orb with two tiny orbiting spheres, simple" · 1 variant · 200 tris · effect · collider: none. *(WLD-09, INT-01)*
- [VFX-15] **Level-Up Pillar** — A brief column of light around Rowan when leveling up (STA-02). Prompt: "tall hollow cylinder of light with flared top and soft vertical stripes, simple" · 1 variant · 300 tris · effect · collider: none. *(STA-01, STA-02)*

