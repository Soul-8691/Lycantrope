# World bible (for dialogue)

What NPCs can know, by place and story state. Keep this short and factual. Lore detail belongs in [STORY.md](../STORY.md), [STORY_V2_IDEAS.md](../STORY_V2_IDEAS.md) and [ANNOTATIONS.md](../ANNOTATIONS.md). This file is what a *townsperson* would know.

The story isn't decided yet: **V1** is the portal story in STORY.md, and **V2** is the *Dream-Quest* story. Lines that fit either are tagged `story: both`.

## The age

- A dark age. Walled towns, abbeys and bells, plague in living memory, tithes, river barges, a Reeve and a town council. Few people read; the Collegium's scholars do.
- No firearms. Crossbows, bows, swords, cudgels. Coin is silver pennies and the odd gold piece.
- Faith: the abbey and its priests, plus older country customs (hill fires, charms over doors). Keep religion generic and unnamed.

## Arkham

- A walled town on the **Miskatonic** river, with a stone **bridge**, a **market square**, the **abbey** with its bells, the **old burying-ground** on the hill, and the **Collegium** with its chained library.
- Roads: the **Aylesbury Pike** inland (bandits, shepherds, the Dunwich hills beyond); the coast road south to **Kingsport** (fishing port under great cliffs; the house on the cliff that no road reaches).
- **People everyone knows:**
  - **Abner Pell:** the chandler. Candles, tallow, rope, lamp oil, oddments. Grumbling and kind. The player works in his shop.
  - **Captain Mercy Thorne:** captain of the Arkham Watch. Grey, patient; held the bridge against river-pirates in her youth.
  - **Magister Henry Armitage:** keeper of the Collegium library. In dialogue, call him **Master Armitage**. "Magister" is a vanilla Morrowind topic and would show as a link.
  - **The Reeve:** the town's chief official. Cautious, unpopular when he shuts gates.
  - **The abbot**, and the abbey's bells.
- **Factions:** the Arkham Watch (`tdl_watch`), the Miskatonic Collegium (`tdl_collegium`).

## Arkham's states (`tdl_ws_arkham`)

| Value | State | What everyone knows | V1 detail | V2 detail |
|---|---|---|---|---|
| 0 | **calm** | Ordinary worries: poor fishing, lost sheep, prices. Odd signs nobody takes seriously: lights in the clouds, bad dreams, the Kingsport cliff-house. | — | — |
| 1 | **afflicted** | Fear. Shutters barred, people leaving, the abbey bells ringing all night, the north gate shut after dark. | The sky opened over the burying-ground. Small brown things and horned raiders came through. Pell was cut down on his doorstep (he lived; his left arm is useless). The Watch lost men. | The **nightmare sickness**: people sleepwalk, talk to someone who isn't there, all dream the same black ships sailing the clouds. No monsters in the streets. |
| 2 | **mending** | Relief, rebuilding, songs about the player (bad ones), prices back to "a scandal." People wary of the sky and of sleep. | The sky has been whole since. Pell has new windows. | The sickness has lifted. Sunsets look golden in a way people can't explain. |

**Nobody in Arkham knows:**
- the Archsage's past;
- the words "Dreamlands", "Kadath" or "Nyarlathotep";
- what the sky-things are.

Scholars might know the old names from books, but would say them nervously.
