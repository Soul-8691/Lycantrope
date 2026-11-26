# NPC variety: unique townsfolk without a Meshy model each

**Goal:** every townsperson looks and sounds like their own person (outfit, face, hair, voice), without
generating a new rigged Meshy model for each one, and without the problems we've already hit.

## What went wrong before, and the rule that follows

| Problem we hit | Cause | Rule |
|---|---|---|
| Waistcoats showing through coats, gaps at wrists, see-through backs | Outfits generated on a grey mannequin and **layered over an already-dressed body** whose proportions didn't match | **Never layer clothes.** Clothing changes are *textures* on one shared mesh, not extra meshes. |
| Bald patches and scalps poking through hats | A hat shell **layered over modelled hair** | **Base heads are close-cropped.** Hair, beards and hats are small attachments made for that one known head, with clearance built in. |
| Grey mannequin skin left on outfits | Stripping skin by colour is guesswork | Nothing is stripped: every texture already belongs to the mesh it's on. |
| Spiky, shattered small models (apple tree, wildflowers) | Meshy is poor at thin, small detail | Hair, beards and hats are **made in code**, like the plants. |
| A young woman with an old woman's voice (twice) | Voices picked at random from a pool | **Voices are tagged by sex and age**, and so are faces; an NPC only gets a voice that matches its face. |
| No jaw on some rigs | Misplaced head markers on individual Meshy rigs | Only a handful of base rigs, each checked once (jaw, hands, head clearance). |
| Credits and Git LFS filling up | A full model per look | A new look is a texture (10 credits, a few MB) or free code. |

## The system: an NPC is a recipe, not a model

Each townsperson is assembled at load time from layers that can't collide:

```
body mesh  ×  outfit texture  ×  face texture  ×  hair  ×  beard  ×  headwear  ×  tint / height / build  ×  voice
(4, Meshy)    (per region,       (per age/sex,    (code)   (code)    (code, opt.)  (code, seeded)              (age/sex pool)
              Meshy retexture)    Meshy retexture)
```

### 1. A few base bodies (Meshy, rigged once)

Four rigged base bodies, all close-cropped, in plain everyday clothes, A-pose, empty hands:

- **Man, average build** and **man, heavy build**
- **Woman, average build (skirt)** and **woman, trousers/working build**

Each one is generated, textured and rigged once (about 35 credits each), then checked once: the jaw
joint (the lesson from the stocky bandit's rig), hand placement for held items, and how much room the
head has for hair and hats. Every NPC is one of these four meshes, so animations, jaws, collision
and held items all work exactly the same for everyone.

### 2. Outfits and faces as textures (Meshy retexture)

Meshy can re-paint an existing model from a text prompt without changing its shape (its
retexture / text-to-texture feature). Each base body gets a set of retextures:

- **Outfits:** shepherd, smith's hand, merchant, dairymaid, weaver, market seller, farmhand, miller,
  innkeeper… (the looks we already like, painted onto the base clothes).
- **Faces:** a handful per base body, tagged by **age** (young / adult / old) and colouring
  (skin tone, eye colour, freckles, wrinkles, stubble).

Because all retextures of one base body share the same mesh and UV layout, they can be **mixed by
body region**. A region mask (made once per base body from its skinning: head, top, bottom, feet)
says which texture each part of the body reads from, so one NPC can have:

```
head   <- face texture "adult, ruddy, freckles"
top    <- outfit "smith's hand"
bottom <- outfit "farmhand"
feet   <- outfit "merchant"
```

No meshes overlap, so nothing can poke through. The only joins are texture seams at the neck, waist
and boot tops, which are natural edges for clothes anyway.

**How the game draws it:** all retextures of a base body go into one texture array; the shader picks a
layer per region from four small per-NPC numbers. There's no per-NPC texture in memory, so 100
villagers cost the same as 4.

### 3. Hair, beards and headwear (made in code)

Small low-poly pieces built by a generator like `tools/props/plants.py`, made **for each base head**
(its real size, measured once), with a few centimetres of clearance:

- **Hair:** cropped (nothing), short, long tied back, bun, braid, ponytail; colours from a palette
  (black, brown, auburn, fair, grey, white).
- **Beards:** stubble (texture only), short, full, long; **attached to the jaw joint**, so they move
  when the NPC talks.
- **Headwear:** straw hat, felt hat, leather cap, linen coif, headscarf, wool hood. Hats replace hair
  (never sit on top of it), which is what stops anything poking through.

They're rigid attachments on the head (or jaw), exactly like weapons in hand, so they follow every
animation. Each new style is free and can be checked in a close-up sheet the same way as the plants.

### 4. Shape and colour variety (code, already in the game)

Kept from today: a per-NPC height range, a slight build scale, a colour **tint per region** (so two
"smith's hand" tops come out in different browns), and walking pace.

### 5. Voices: tagged pools, matched to the face

- Designed voices are tagged with **sex and age band** (young / adult / old), about 2–3 per band:
  roughly 12–15 voices in all.
- An NPC's voice must match its face's tags: an old face never gets a young voice, and vice versa.
- A small per-NPC **pitch nudge** (±4% playback rate) makes two NPCs sharing a voice sound different.
- Lines stay **per role** (what a person says) and are generated only for the role and voice pairs
  that actually appear in the world, so costs follow the number of different voices actually used,
  not the number of NPCs.

## Unique NPCs from the same parts

Every NPC is a **recipe** in data. Named story characters get a fixed, hand-picked recipe; everyone
else gets a seeded random one, constrained so it stays believable:

```json
"recipes": {
  "nell":   {"body": "woman_skirt", "face": "young_fair_freckles", "top": "dairymaid", "bottom": "dairymaid",
             "hair": "braid_auburn", "headwear": "coif", "voice": "woman_young_1", "lines": "nell"},
  "random_villager_woman": {"body": ["woman_skirt", "woman_work"], "age": ["young", "adult", "old"],
             "top": "any_woman", "bottom": "any_woman", "headwear_chance": 0.4}
}
```

Rules for the random ones:
- Outfit regions are picked from the same body's set, and mismatches can be forbidden per outfit
  (for example, the merchant's coat top only with a merchant or farmhand bottom).
- Hair colour follows age (more grey and white for "old" faces).
- The same seed always makes the same person, so a villager looks the same every time you load.

Characters important to the story (Oswin, Aldric, Captain Thorne, the Apprentice) can still get a
bespoke Meshy model; this system is for everyone else.

## Costs

| Item | How many | Credits |
|---|---|---|
| Base bodies (preview + texture + rig) | 4 | ~140 |
| Outfit retextures | ~8 per body, 32 in all | ~320 (if retexture is 10 each) |
| Face retextures | ~4 per body, 16 in all | ~160 |
| Hair, beards, headwear | any number | 0 (code) |
| Voices | ~12–15 designs | a few voice designs (ElevenLabs) |
| **Total, one time** | | **~620 Meshy credits** |

After that, a new kind of townsperson is a free recipe, and a new outfit is one retexture. The
current 9 bespoke villager models cost about 315 credits for 9 looks; this gives hundreds of looks
for about twice that.

## Phases

1. **Prove the risky part first (about 45 credits).** One base body (man, average), rigged, plus **one**
   retexture. Check that the retexture keeps the original UV layout. If Meshy re-UVs the model, add a
   step that bakes each retexture back onto the base body's UVs in code (sampling the retextured model
   at the nearest surface point), and test that instead.
2. **Region mixing in the game:** the region mask, the texture-array shader path, per-NPC region
   layers, and a close-up sheet of mixed recipes (front, back, walking).
3. **Code-made hair, beards and headwear** for that base head, checked in close-ups for clearance
   and jaw movement.
4. **Voice tags and matching:** tag the existing voices by sex and age, add the face/voice rule and the
   pitch nudge, then design the missing age bands.
5. **The other three base bodies** and their retextures; move the generic villagers and travellers
   to recipes.
6. **Story NPCs as fixed recipes:** Nell, Ebb, Tam, Jory, Maud, Hester (the current bespoke models can
   stay until their recipes look as good).

## Open questions

- **Meshy retexture:** confirm the current price and whether it keeps the UV layout (phase 1 answers both).
- **Seam quality:** whether the neck and waist joins need a soft blend in the mask (a few pixels of fade).
- **Texture memory:** 2K layers (about 21 MB each with mipmaps) would be roughly 1 GB of video memory for
  four bodies with 12 layers each: too much. 1K layers bring that to about 270 MB, and block compression
  (BC1/BC7) cuts it a further 4–8×. Plan on 1K, compressed.
