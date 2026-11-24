# LYCANTROPE — Armor

Armor Rowan can find and wear (HER-07: visible armor swaps). There are **14 sets**, each with four matching pieces: **Head (HED)**, **Arms (ARM)**, **Torso (TRS)** and **Legs (LEG)**. The pieces of a set share a number, so `HED-06`, `ARM-06`, `TRS-06` and `LEG-06` are the Wolfhide set. You can mix pieces from different sets freely. The idea tracker reads this file, so every piece and rule can be approved or denied.

---

## How to read an entry

`- [TRS-05] **Name** — what it looks like · weight class · Def · Poise · Wt · Res · Req. Prompt: "…" (where found)`

- **Def** is physical defense. It plugs into the damage formula `after = raw · raw / (raw + defense)` (ROADMAP §7.3). The defense of all worn pieces adds up.
- **Poise** adds to stagger resistance (CMB-10).
- **Wt** is weight. Total weight against equip load (`40 + 1.5 × Endurance`) decides the roll type (CMB-26): under 30% fast, under 70% medium, above that slow.
- **Res** is a resistance change for the damage types in CMB-18 (fire, frost, radiant) and the status buildups in CMB-19 (bleed, poison, frost, stone). `+` means it takes less, `−` means it takes more.
- **Req** is the attribute requirement (STA-04: Might, Finesse, Vigor, Endurance, Spirit, Fortune; every attribute starts at 10). What happens when you don't meet it is set by ARS-01 below.
- **Prompt** is the Meshy prompt. The batch script adds the shared style line (ART-02).
- ⭐ = needed for the First Playable.

**Weight classes and typical per-set totals:**

| Class | Total Def | Total Poise | Total Wt | Typical requirements |
|---|---|---|---|---|
| Light | 15–30 | 0–6 | 4–9 | Finesse, Spirit or Fortune |
| Medium | 32–55 | 8–20 | 10–20 | Endurance, Vigor |
| Heavy | 60–90 | 24–45 | 22–34 | Might + Endurance |

---

## Rules (ARS)

- [ARS-01] **Under-requirement penalty** — You can always wear a piece. If you don't meet its requirement, it gives only half its Def and Poise, and weighs 50% more, which pushes you toward a slower roll. Each requirement is checked separately, and the piece's tooltip shows the shortfall in red. ⭐ *(DS)*
- [ARS-02] **Set bonuses** — Wearing all four pieces of one set grants its listed bonus. Two or three pieces give nothing extra, so mixing sets is allowed but committing to one is rewarded. *(NEW)*
- [ARS-03] **Armor upgrades at the smith** — Armor goes from +1 to +5 using the same ores as weapons, and like weapons (CMB-24, per your note) it needs a smith NPC. Each level gives +8% Def and Poise. Requirements don't change. *(DS)*
- [ARS-04] **One rune socket on torso pieces** — Medium and heavy torso pieces have a single rune socket (CMB-25) for a resistance or stat rune. *(SK, MW)*
- [ARS-05] **Generate sets whole, split by bone** — For each set, Meshy generates the complete outfit on a male mannequin in A-pose (image-to-3D or text-to-3D), auto-rigged on Rowan's skeleton. `normalize.py` then splits it into the four slot meshes by which bone each vertex follows: head and neck → Head; forearms and hands → Arms; spine, chest and upper arms → Torso; hips, legs and feet → Legs. Every piece then fits Rowan, and any mix of sets still lines up at the seams. *(DOC, NEW)*

---

## 1. Farmhand's Garb (set 01)

Rowan's own clothes at the start of the game. **Req:** none. **Set bonus:** stamina regenerates 10% faster. *(Light; total Def 16, Poise 0, Wt 4.)*

- [HED-01] **Wool Cap** — A knitted, patched wool cap. · Light · Def 2 · Poise 0 · Wt 0.4 · Res: frost +2% · Req: — . Prompt: "simple patched knitted wool cap, peasant" ⭐ *(start)*
- [ARM-01] **Work Gloves** — Worn leather work gloves and rolled sleeves. · Light · Def 3 · Poise 0 · Wt 0.6 · Res: — · Req: — . Prompt: "worn brown leather work gloves with rolled linen shirt sleeves" ⭐ *(start)*
- [TRS-01] **Patched Travelling Coat** — Brown wool coat over a linen shirt, patched at the elbows. · Light · Def 7 · Poise 0 · Wt 2.0 · Res: frost +3% · Req: — . Prompt: "patched brown wool travelling coat over a linen shirt, rope belt, peasant" ⭐ *(start)*
- [LEG-01] **Work Trousers & Boots** — Sturdy trousers tucked into scuffed boots. · Light · Def 4 · Poise 0 · Wt 1.0 · Res: — · Req: — . Prompt: "sturdy brown work trousers tucked into scuffed leather boots" ⭐ *(start)*

## 2. Militia Padding (set 02)

Quilted gear from the burned watchtower's stores. **Req:** Endurance 11. **Set bonus:** +10% stamina. *(Light/medium; total Def 26, Poise 6, Wt 7.)*

- [HED-02] **Kettle Hat** — A dented, broad-brimmed iron helmet. · Light · Def 6 · Poise 2 · Wt 1.4 · Res: — · Req: Endurance 11. Prompt: "dented iron kettle hat helmet with a wide brim" ⭐ *(Ruined Watchtower)*
- [ARM-02] **Padded Mittens** — Quilted gloves with leather palms. · Light · Def 4 · Poise 1 · Wt 1.0 · Res: — · Req: Endurance 11. Prompt: "quilted padded cloth gloves with leather palms" ⭐ *(Ruined Watchtower)*
- [TRS-02] **Gambeson** — Thick quilted jacket in faded militia colors. · Light · Def 10 · Poise 2 · Wt 3.0 · Res: bleed +10% · Req: Endurance 11. Prompt: "thick quilted gambeson jacket, faded green and tan, militia" ⭐ *(Ruined Watchtower)*
- [LEG-02] **Padded Leggings** — Quilted leggings and shin-wraps. · Light · Def 6 · Poise 1 · Wt 1.6 · Res: — · Req: Endurance 11. Prompt: "quilted padded leggings with cloth shin wraps and boots" ⭐ *(Ruined Watchtower)*

## 3. Ranger's Leathers (set 03)

Supple leathers of the Wolfwood's old wardens. **Req:** Finesse 14. **Set bonus:** the crossbow reloads 20% faster. *(Light; total Def 24, Poise 2, Wt 6.)*

- [HED-03] **Ranger's Hood** — Deep green hood with a leather half-mask. · Light · Def 5 · Poise 0 · Wt 0.8 · Res: poison +5% · Req: Finesse 12. Prompt: "deep green ranger hood with a leather half face mask" *(Hunter's Lodge)*
- [ARM-03] **Archer's Bracers** — Laced leather bracers and a shooting glove. · Light · Def 4 · Poise 0 · Wt 0.8 · Res: — · Req: Finesse 14. Prompt: "laced leather archer bracers and a shooting glove" *(Hunter's Lodge)*
- [TRS-03] **Ranger's Jerkin** — Fitted leather jerkin with a green cloak. · Light · Def 9 · Poise 1 · Wt 2.6 · Res: poison +5% · Req: Finesse 14. Prompt: "fitted leather ranger jerkin with a short green hooded cloak and belts" *(Hunter's Lodge)*
- [LEG-03] **Ranger's Breeches** — Soft breeches and quiet, high boots. · Light · Def 6 · Poise 1 · Wt 1.8 · Res: — · Req: Finesse 12. Prompt: "soft leather breeches and tall quiet ranger boots" *(Hunter's Lodge)*

## 4. Bandit's Spoils (set 04)

Mismatched loot stitched together by a lucky bandit chief. **Req:** Fortune 12. **Set bonus:** +15% loot drop chance. *(Light/medium; total Def 30, Poise 6, Wt 9.)*

- [HED-04] **Bandit's Mask & Hood** — Ragged hood with a dark cloth face mask. · Light · Def 5 · Poise 1 · Wt 0.8 · Res: — · Req: Fortune 12. Prompt: "ragged bandit hood with a dark cloth face mask" *(bandit camps)*
- [ARM-04] **Studded Bracers** — Leather bracers with iron studs and a stolen ring. · Light · Def 6 · Poise 1 · Wt 1.4 · Res: bleed +5% · Req: Fortune 12. Prompt: "leather bracers with iron studs, gold ring on one finger" *(bandit camps)*
- [TRS-04] **Stolen Brigandine** — Riveted brigandine over a patched shirt, with a coin pouch. · Medium · Def 12 · Poise 3 · Wt 4.6 · Res: bleed +5% · Req: Fortune 12, Endurance 11. Prompt: "riveted brigandine vest over a patched shirt, belts and coin pouches" *(bandit chief)*
- [LEG-04] **Bandit's Breeches** — Patched breeches with knee guards from three different armors. · Light · Def 7 · Poise 1 · Wt 2.2 · Res: — · Req: Fortune 12. Prompt: "patched breeches with mismatched metal knee guards and worn boots" *(bandit camps)*

## 5. Chainmail (set 05)

Plain, dependable riveted mail. **Req:** Endurance 14, Might 12. **Set bonus:** +10% slash resistance. *(Medium; total Def 40, Poise 12, Wt 14.)*

- [HED-05] **Mail Coif** — Mail hood under a simple steel cap. · Medium · Def 8 · Poise 3 · Wt 2.6 · Res: bleed +10% · Req: Endurance 12. Prompt: "chainmail coif hood with a simple round steel cap" *(Brackenvale, roads)*
- [ARM-05] **Mail Gloves** — Mail mittens over leather gloves. · Medium · Def 7 · Poise 2 · Wt 2.2 · Res: — · Req: Endurance 12. Prompt: "chainmail mittens over leather gloves" *(Brackenvale, roads)*
- [TRS-05] **Hauberk** — Knee-length mail shirt with a belted surcoat. · Medium · Def 16 · Poise 5 · Wt 6.0 · Res: bleed +10% · Req: Endurance 14, Might 12. Prompt: "knee-length chainmail hauberk with a plain belted cloth surcoat" *(Wolfwood)*
- [LEG-05] **Mail Chausses** — Mail leggings with leather boots. · Medium · Def 9 · Poise 2 · Wt 3.2 · Res: — · Req: Endurance 12. Prompt: "chainmail leggings with tall leather boots" *(Wolfwood)*

## 6. Wolfhide (set 06)

Heavy pelts over leather, made by the smith from Grimtooth's hide and wolf pelts. **Req:** Vigor 14. **Set bonus:** frost resistance +15% and wolves (ENM-02) notice you from half as far away. *(Medium; total Def 36, Poise 10, Wt 12.)*

- [HED-06] **Wolf-Skull Helm** — A wolf's skull worn as a helm, with a pelt hanging behind. · Medium · Def 8 · Poise 3 · Wt 2.0 · Res: frost +5% · Req: Vigor 12. Prompt: "helmet made from a large wolf skull with grey fur pelt hanging down the back" *(smith, Grimtooth's pelt)*
- [ARM-06] **Fur Bracers** — Fur-trimmed leather bracers with claw toggles. · Medium · Def 6 · Poise 2 · Wt 1.8 · Res: frost +5% · Req: Vigor 12. Prompt: "leather bracers trimmed with grey wolf fur, claw toggles" *(smith)*
- [TRS-06] **Wolfpelt Mantle** — Thick grey wolf-pelt mantle over hardened leather. · Medium · Def 14 · Poise 3 · Wt 5.2 · Res: frost +10% · Req: Vigor 14. Prompt: "thick grey wolf pelt mantle over hardened leather chest armor" *(smith, Grimtooth's pelt)*
- [LEG-06] **Fur-Lined Leggings** — Leather leggings with fur cuffs and wrapped boots. · Medium · Def 8 · Poise 2 · Wt 3.0 · Res: frost +5% · Req: Vigor 12. Prompt: "leather leggings with grey fur cuffs and fur-wrapped boots" *(smith)*

## 7. Mirewalker (set 07)

Waxed oilcloth and waders worn by the Blackmire's stilt-folk. **Req:** Endurance 16. **Set bonus:** no slowdown in shallow water, and leeches (MON-04) can't latch on. *(Medium; total Def 34, Poise 8, Wt 12.)*

- [HED-07] **Veiled Swamp Hat** — Wide-brimmed waxed hat with a mosquito veil. · Medium · Def 6 · Poise 2 · Wt 1.4 · Res: poison +10% · Req: Endurance 14. Prompt: "wide brimmed waxed swamp hat with a hanging mesh mosquito veil" *(Mirewatch)*
- [ARM-07] **Oilcloth Gauntlets** — Long waxed gloves with bone buttons. · Medium · Def 6 · Poise 1 · Wt 1.6 · Res: poison +10% · Req: Endurance 14. Prompt: "long waxed oilcloth gauntlet gloves with bone buttons" *(Mirewatch)*
- [TRS-07] **Waxed Longcoat** — Stiff, dark, waxed longcoat over a mail vest. · Medium · Def 13 · Poise 3 · Wt 5.0 · Res: poison +15% · Req: Endurance 16. Prompt: "stiff dark waxed oilcloth longcoat over a short chainmail vest" *(Sunken Shrine)*
- [LEG-07] **Bog Waders** — Thigh-high waxed waders strapped over trousers. · Medium · Def 9 · Poise 2 · Wt 4.0 · Res: poison +10% · Req: Endurance 14. Prompt: "thigh high waxed leather bog waders with straps" *(Mirewatch)*

## 8. Frostfang Furs (set 08)

Mountain gear lined with Frost Yeti fur. **Req:** Vigor 18, Endurance 14. **Set bonus:** immune to frost slow (CMB-19). *(Medium; total Def 44, Poise 12, Wt 16.)*

- [HED-08] **Fur Hood & Goggles** — Thick fur hood with carved bone snow goggles. · Medium · Def 9 · Poise 3 · Wt 2.4 · Res: frost +10% · Req: Vigor 16. Prompt: "thick white fur hood with carved bone snow goggles" *(Summit Shelter)*
- [ARM-08] **Yeti-Fur Gauntlets** — Huge fur-backed gauntlets with leather palms. · Medium · Def 8 · Poise 2 · Wt 2.6 · Res: frost +10% · Req: Vigor 16. Prompt: "large gauntlets backed with shaggy white yeti fur, leather palms" *(Frost Yeti drops)*
- [TRS-08] **Yeti-Fur Coat** — Long shaggy coat over layered leather and mail. · Medium · Def 17 · Poise 5 · Wt 7.0 · Res: frost +20% · Req: Vigor 18, Endurance 14. Prompt: "long shaggy white yeti fur coat over layered leather and chainmail" *(Summit Shelter)*
- [LEG-08] **Snow Boots & Leggings** — Fur-lined leggings and spiked snow boots. · Medium · Def 10 · Poise 2 · Wt 4.0 · Res: frost +10% · Req: Vigor 16. Prompt: "fur lined leggings with heavy spiked snow boots" *(Frostfang Foothold)*

## 9. Sage's Vestments (set 09)

Robes in the style of Aldric Greymantle, the mentor. **Req:** Spirit 18. **Set bonus:** Rites (CMB-29) cast 20% faster. *(Light; total Def 18, Poise 0, Wt 5.)*

- [HED-09] **Sage's Hood** — Deep grey hood stitched with faint silver runes. · Light · Def 3 · Poise 0 · Wt 0.6 · Res: radiant +5% · Req: Spirit 16. Prompt: "deep grey wizard hood stitched with faint silver runes" *(Aldric's camp)*
- [ARM-09] **Wrapped Sleeves** — Rune-inked cloth wraps around the forearms. · Light · Def 3 · Poise 0 · Wt 0.6 · Res: — · Req: Spirit 16. Prompt: "wide wizard robe sleeves with rune inked cloth wraps around the forearms" *(Aldric's camp)*
- [TRS-09] **Greymantle Robe** — Layered grey robes with a satchel and a silver clasp. · Light · Def 7 · Poise 0 · Wt 2.4 · Res: radiant +10%, fire +5% · Req: Spirit 18. Prompt: "layered grey wizard robes with a leather satchel and a silver clasp" *(Aldric's camp)*
- [LEG-09] **Traveller's Sandals** — Robe skirts over wrapped trousers and sturdy sandals. · Light · Def 5 · Poise 0 · Wt 1.4 · Res: — · Req: Spirit 16. Prompt: "long robe skirts over wrapped cloth trousers and sturdy leather sandals" *(Aldric's camp)*

## 10. Watch Plate (set 10)

Full steel plate of the realm's old guard. **Req:** Might 20, Endurance 18. **Set bonus:** +15% poise. *(Heavy; total Def 64, Poise 28, Wt 24.)*

- [HED-10] **Great Helm** — Flat-topped steel great helm with breathing holes. · Heavy · Def 13 · Poise 6 · Wt 4.2 · Res: — · Req: Might 18. Prompt: "flat topped steel great helm with eye slit and breathing holes" *(Old Watch Road)*
- [ARM-10] **Plate Gauntlets** — Articulated steel gauntlets and vambraces. · Heavy · Def 12 · Poise 5 · Wt 3.8 · Res: — · Req: Might 18. Prompt: "articulated steel plate gauntlets with vambraces" *(Old Watch Road)*
- [TRS-10] **Steel Cuirass** — Breastplate and pauldrons over mail, with a faded tabard. · Heavy · Def 25 · Poise 11 · Wt 10.0 · Res: bleed +15% · Req: Might 20, Endurance 18. Prompt: "steel plate cuirass with rounded pauldrons over chainmail, faded blue tabard" *(Brackenvale crypt vault)*
- [LEG-10] **Plate Greaves** — Steel greaves, knee cops and sabatons. · Heavy · Def 14 · Poise 6 · Wt 6.0 · Res: — · Req: Might 18, Endurance 16. Prompt: "steel plate greaves with knee cops and sabatons" *(Old Watch Road)*

## 11. Orcish Bonemail (set 11)

Hide and bone armor of the Ashen warband. **Req:** Might 22. **Set bonus:** +20% strike resistance, and guard breaks drain 15% less stamina. *(Heavy; total Def 62, Poise 30, Wt 25.)*

- [HED-11] **Horned Bone Helm** — Massive horned skull helm lashed with hide. · Heavy · Def 12 · Poise 7 · Wt 4.0 · Res: — · Req: Might 20. Prompt: "massive horned beast skull helmet lashed with hide straps, orcish" *(Orc Warcamp)*
- [ARM-11] **Tusk Bracers** — Hide bracers studded with tusks and teeth. · Heavy · Def 11 · Poise 5 · Wt 3.6 · Res: bleed +10% · Req: Might 20. Prompt: "hide bracers studded with tusks and teeth, orcish" *(Orc Warcamp)*
- [TRS-11] **Bonemail Hauberk** — Overlapping bone plates sewn onto thick hide. · Heavy · Def 25 · Poise 12 · Wt 11.0 · Res: fire +10% · Req: Might 22, Endurance 16. Prompt: "chest armor of overlapping bone plates sewn onto thick hide, orcish war armor" *(Orc Warcamp chief)*
- [LEG-11] **Bone Greaves** — Hide leggings with bone shin plates and fur boots. · Heavy · Def 14 · Poise 6 · Wt 6.4 · Res: — · Req: Might 20. Prompt: "hide leggings with bone shin plates and fur boots, orcish" *(Orc Warcamp)*

## 12. Emberforged (set 12)

Dark iron plate reforged in the Cinder Forge; the seams still glow. **Req:** Might 24, Endurance 22, Spirit 14. **Set bonus:** immune to burn buildup, and your heavy attacks leave a short fire trail. *(Heavy; total Def 72, Poise 34, Wt 28.)*

- [HED-12] **Emberforged Helm** — Dark iron helm with glowing seams and a grilled visor. · Heavy · Def 14 · Poise 7 · Wt 4.6 · Res: fire +15% · Req: Might 22, Spirit 14. Prompt: "dark iron helmet with glowing orange cracks along the seams, grilled visor" *(Cinder Forge)*
- [ARM-12] **Emberforged Gauntlets** — Heavy gauntlets with ember-glowing knuckles. · Heavy · Def 13 · Poise 6 · Wt 4.2 · Res: fire +15% · Req: Might 22. Prompt: "heavy dark iron gauntlets with glowing orange cracks at the knuckles" *(Cinder Forge)*
- [TRS-12] **Emberforged Cuirass** — Layered dark iron plate with a molten core glow. · Heavy · Def 29 · Poise 14 · Wt 12.6 · Res: fire +25%, frost −10% · Req: Might 24, Endurance 22, Spirit 14. Prompt: "layered dark iron plate chest armor with a glowing molten core and glowing seams" *(Cinder Colossus, BOS-05)*
- [LEG-12] **Emberforged Greaves** — Dark iron greaves with glowing knee plates. · Heavy · Def 16 · Poise 7 · Wt 6.6 · Res: fire +15% · Req: Might 22, Endurance 20. Prompt: "dark iron leg armor with glowing orange cracks at the knee plates" *(Cinder Forge)*

## 13. Dread Plate (set 13)

The black plate of the Dark Lord's Dread Knights (ENM-19). **Req:** Might 28, Endurance 26. **Set bonus:** +25% poise, and Dread Knights hesitate before attacking you. Radiant damage hurts more in it. *(Heavy; total Def 84, Poise 44, Wt 33.)*

- [HED-13] **Dread Helm** — Spiked black helm with a narrow, glowing visor. · Heavy · Def 17 · Poise 9 · Wt 5.4 · Res: radiant −10% · Req: Might 26. Prompt: "spiked black steel helmet with a narrow visor glowing faint purple, dark knight" *(Dread Knight drops)*
- [ARM-13] **Dread Gauntlets** — Clawed black gauntlets with spiked couters. · Heavy · Def 15 · Poise 8 · Wt 5.0 · Res: radiant −10% · Req: Might 26. Prompt: "clawed black steel gauntlets with spiked elbows, dark knight" *(Dread Knight drops)*
- [TRS-13] **Dread Cuirass** — Massive black plate with a crown sigil and a torn cape. · Heavy · Def 33 · Poise 18 · Wt 14.6 · Res: fire +10%, frost +10%, radiant −15% · Req: Might 28, Endurance 26. Prompt: "massive black plate armor chest with an abstract crown sigil, spiked pauldrons and a torn dark cape" *(Duskhold)*
- [LEG-13] **Dread Greaves** — Heavy black greaves with spiked knee plates. · Heavy · Def 19 · Poise 9 · Wt 8.0 · Res: radiant −10% · Req: Might 26, Endurance 24. Prompt: "heavy black steel greaves with spiked knee plates, dark knight" *(Dread Knight drops)*

## 14. Mantle of the First Hero (set 14)

The ancient hero's own armor, the Dawnblade's first owner. One piece lies in each Crown Shard dungeon (STY-03). **Req:** a balanced build (Vigor 25, Finesse 20, Might 20, Spirit 20). **Set bonus:** the Dawnblade deals 15% more damage and radiant resistance rises by 20%. *(Medium; total Def 56, Poise 20, Wt 18.)*

- [HED-14] **Circlet of the First Hero** — Simple gold circlet with a sun-stone, and an open-faced mail hood. · Medium · Def 11 · Poise 4 · Wt 2.4 · Res: radiant +10% · Req: Spirit 20. Prompt: "simple gold circlet with a sun stone over an open faced chainmail hood, ancient hero" *(Wolfwood dungeon)*
- [ARM-14] **Vambraces of the First Hero** — Engraved bronze vambraces with sun motifs. · Medium · Def 11 · Poise 4 · Wt 2.8 · Res: radiant +5% · Req: Finesse 20. Prompt: "engraved bronze vambraces with sun motifs and leather gloves, ancient hero" *(Blackmire dungeon)*
- [TRS-14] **Breastplate of the First Hero** — Bronze-and-steel breastplate under a weathered white tabard with a sun emblem. · Medium · Def 21 · Poise 8 · Wt 8.4 · Res: radiant +15%, frost +5%, fire +5% · Req: Vigor 25, Might 20. Prompt: "bronze and steel breastplate under a weathered white tabard with a sun emblem, ancient hero" *(Frostfang dungeon)*
- [LEG-14] **Greaves of the First Hero** — Bronze greaves and tall boots with engraved knee plates. · Medium · Def 13 · Poise 4 · Wt 4.4 · Res: radiant +5% · Req: Vigor 20. Prompt: "bronze greaves with engraved sun knee plates and tall leather boots, ancient hero" *(Ashen dungeon)*
