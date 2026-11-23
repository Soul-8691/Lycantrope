# Dialogue conventions

Rules for everyone who writes dialogue for The Dreamlands, people and Claude alike. `validate.py` checks the rules marked ✔.

## How Morrowind dialogue works (what the writing must fit)

- The player clicks a **topic**. The game shows the **first response from the top** whose conditions all match the speaker. Order matters: put specific responses (one NPC, one faction) **above** general ones (anyone in town). ✔ (unreachable responses are flagged)
- A topic word inside a response becomes a **clickable link** and is added to the player's topics. Mention a topic only when you want it learned. ✔ (topics nobody can learn, and vanilla topic names, are flagged)
- **Greetings** are the topics `Greeting 0` to `Greeting 9`. They're checked in order, and the first match is said when the window opens.
- A response can run a short **result script**: `AddTopic "name"`, `Journal tdl_main 20`, `Set tdl_x to 1`, `ModDisposition 10`.
- Text variables: `%PCName`, `%PCRace`, `%PCClass`, `%PCRank`, `%NextPCRank`, `%Name`, `%Race`, `%Class`, `%Faction`, `%Rank`, `%Cell`. ✔

## Style

- **Short.** One to four sentences. Aim under 400 characters; never over 512. ✔ If there's more to say, make it a second topic.
- **The dark ages, plainly spoken.** No modern idioms ✔. No fake-Shakespeare either: avoid *thee/thou/verily*. Common folk are blunt and concrete (barges, tallow, tithes, the Watch, the abbey bells). Scholars may be ornate, with a Lovecraftian flavour.
- **Hearsay, not exposition.** Rumours are what people *think* they know. They exaggerate, get details wrong, and disagree with each other. Let the player piece things together.
- **One voice per character.** Follow the character sheet's `voice` and `sample_lines`.
- **The player:** "you" or `%PCName`. Never *he/she* for the player unless the response is filtered on `PcSex`.
- **Knowledge follows the story.** An NPC only knows what has happened by that story state (see the bible). If unsure, have them not know.
- **No Tamriel.** No Vvardenfell, Dunmer, septims, Daedra or Nine Divines. ✔ Money is "coin", "silver" or "pennies".
- **No racism.** No slurs or ethnic descriptors, the same filters as the story tools. ✔ Lovecraft's prejudices stay out. Strangeness belongs to monsters and dreams, never to peoples.

## Writing a line (YAML)

```yaml
topic: latest rumors
type: topic                  # topic (default) | greeting | voice | persuasion
order: 50                    # files for the same topic merge in this order (lower = earlier)
defaults:                    # applied to every line below (when-conditions merge)
  when: { cell: Arkham }
lines:
  - key: pell_calm           # stable, unique in the topic; the response ID is derived from it
    text: "Rumours? I sell candles, not gossip."
    when:
      speaker: tdl_pell      # NPC id   | race, class, faction, rank, sex, cell, disposition
      global: { tdl_ws_arkham: "== 0" }      # also: local, not_local, journal, dead, item
      function: { pc_level: ">= 5" }          # any Morrowind function, snake_case or CamelCase
      not_faction: tdl_watch                  # also: not_id, not_class, not_race, not_cell
    result: AddTopic "the Collegium"
    story: both              # v1 | v2 | both
    status: draft            # draft | reviewed
    locked: false            # true = hand-edited; generation must not change it ✔ (--check-locked)
    voice: false             # true = goes to voice_lines.csv for ElevenLabs
```

Comparisons are written `"== 0"`, `">= 30"`, `"< 5"`, `"!= 1"`. Morrowind allows **6** filters per response ✔ (speaker, race, class, faction, cell, rank, sex and disposition don't count toward that).

Journals live in `dialogue/journals/`:

```yaml
journal: tdl_main
name: The Dreamer in the Shop
entries:
  - index: 10
    text: "Abner Pell has sent me to the Collegium with a crate of candles."
  - index: 100
    text: "..."
    finished: true
```
