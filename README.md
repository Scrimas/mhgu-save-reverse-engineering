# MHGU Switch Save Format — Reverse-Engineering Notes

Structural notes on the Monster Hunter Generations Ultimate save file as written by
the Nintendo Switch release, recovered by differential analysis against a live save.

The goal of these documents is to describe **how the save is organised**, not to
describe any one player's data. Where a concrete value is quoted it is only ever as
evidence for a structural claim.

## Scope and provenance

| | |
|---|---|
| Title | Monster Hunter Generations Ultimate |
| Title ID | `0100770008DD8000` (EU / western release) |
| Platform | Nintendo Switch, observed through the Ryujinx emulator |
| File | `system` (and `system_backup`), 5,159,100 bytes |
| Method | Controlled before/after diffing of a real save (see [methodology](docs/06-methodology.md)) |

All offsets are **absolute byte offsets into `system`**, little-endian, from a save
containing a single character. See [Open questions](#open-questions) before assuming
they are portable.

## Documents

| Document | Covers |
|---|---|
| [01 — Container](docs/01-container.md) | File layout, commit slots, encryption and integrity |
| [02 — Monster records](docs/02-monster-records.md) | Hunt tallies, size records, the monster index table |
| [03 — Deviants](docs/03-deviants.md) | Permit counts, level bitmaps, unlock gating |
| [04 — Weapon usage](docs/04-weapon-usage.md) | Guild Card weapon usage counters |
| [05 — Quests](docs/05-quests.md) | Quest bitmaps and the full quest index, history log, counters |
| [06 — Methodology](docs/06-methodology.md) | How this was derived, and how to extend it |
| [07 — Equipment](docs/07-equipment.md) | Character slots, equipment box, talismans, transmog, dye, My Sets |
| [08 — Hunter Arts and Canteen](docs/08-progression.md) | Hunter Art unlocks, Canteen ingredients and dishes |
| [09 — Awards](docs/09-awards.md) | Guild Card award bitfield |
| [10 — NPC talk data](docs/10-npc-talk.md) | Talk tables: request offers, star-level flags, per-NPC bits |

Machine-readable: [`data/monster-index.csv`](data/monster-index.csv), [`data/quest-index.csv`](data/quest-index.csv), [`data/request-index.csv`](data/request-index.csv), [`data/quest-unlock.csv`](data/quest-unlock.csv), [`data/request-offer.csv`](data/request-offer.csv), [`data/hunter-arts.csv`](data/hunter-arts.csv), [`data/offsets.json`](data/offsets.json)

## Quick reference

| Structure | Offset | Layout |
|---|---|---|
| Header nonce | `0x000014` | u32, changes every write, **not** a checksum |
| Deviant permit counts | `0x18F4D8` | 18 × u8 |
| Quests cleared | `base + 0x2C77` | 1509 bits, index = position in `quest_group`, see [`quest-index.csv`](data/quest-index.csv) |
| Quests seen (NEW cleared) | `base + 0x2D77` | same indexing, `+0x100` bytes |
| Villager request flags | `base + 0x2C56D` | 1536-bit event flag map; per-request accepted/completed bits in [`request-index.csv`](data/request-index.csv). Accepted = quest posted on the board |
| Quest unlock rules | script, not a save field | the board runs `script\check_quest_unlocked` per quest; it reads event flags, cleared bits, HR and the Hub star level. Rules in [`quest-unlock.csv`](data/quest-unlock.csv), evaluator [`tools/quest_unlock.py`](tools/quest_unlock.py) |
| Request offer conditions | talk data, not a save field | per-NPC tables `table/npc/script/npc_NNN_td.ntd`; conditions in [`request-offer.csv`](data/request-offer.csv), evaluator [`tools/request_offer.py`](tools/request_offer.py) |
| Per-NPC talk hold bits | `base + 0x2C62D` | 3 × 24 bytes after the event flags, bit = NPC name index. Set = NPC skips request offers / kind 9 talk / announcements until the next quest (DERIVED), see [10](docs/10-npc-talk.md) |
| Village / Hub star level | `base + 0x2C4DA` / `+0x2C4DC` | u16 each, 1–10 / 1–13 |
| Deviant levels (cleared) | bit `0x18F989`.3 | quest indices 947–1174 (Special Permit), 228 bits |
| Deviant levels (seen) | bit `0x18FA89`.3 | same layout, `+0x100` bytes |
| Quest counter | `0x192AEA` | u16 |
| Monster hunt tallies | `0x192B40` | u16, index 1–137 (`0x192B40 + 2i`) |
| Monster capture counts | `0x192C52` | u16, index 1–137 (`0x192C52 + 2i`) |
| Monster size records | `0x192D62` | (u16 min%, u16 max%), stride 4, index 1–137 |
| Weapon usage — Village | `0x254713` | 15 × u16 |
| Weapon usage — Hub | `0x254731` | 15 × u16 |
| Weapon usage — Arena | `0x25474F` | 15 × u16 |
| Quest history log | `0x2546D7` | stride `0xA0` records |
| Character slot pointers | `0x34` | 3 × u32, relative to `0x24` |
| Equipment box | `base + 0x62EE` | 2000 × 36 bytes; transmog at `+0x04` |
| My Sets (dye lives here) | `base + 0x208C8` | stride `0x88`; pigment 5 × RGBA at `+0x6A` |
| Hunter Arts unlocked | `base + 0x2C13` | 24-byte bitfield, IDs 1–70 and 83–190 |
| Canteen dishes | `base + 0x2C67D` | 13-byte bitfield, 99 dishes |
| Canteen ingredients | `base + 0x2F8F` | 6-byte bitfield, 45 ingredients |
| Awards earned | `base + 0xC8115` | 132-bit bitfield, one run per location grid |

## Confidence levels

Every claim in these documents carries one of three tags:

- **CONFIRMED** — verified by at least two independent lines of evidence, normally a
  controlled write plus an observed in-game change, or two separate diffs agreeing.
- **DERIVED** — follows from a confirmed structure plus a single observation.
  Very likely correct, not independently cross-checked.
- **UNRESOLVED** — known to exist, layout or meaning not established.

Nothing here is from official documentation or leaked source. It is all inference
from observed bytes, and it is incomplete.

## Open questions

- **Multiple character slots.** MHGU supports several characters per save. Only one
  was ever present in the analysed file. The header's slot-pointer table (`0x34`,
  see [07](docs/07-equipment.md#character-slots)) puts character 1 at `0x18CC9C`,
  and every offset above falls inside that character's block. So they are most
  likely `base + const`, but this has not been tested with a second character.
  **An editor should resolve the base through the pointer, not hard-code it.**
- **Region portability.** Only the EU/western build was examined. Japanese builds
  may differ.
- **Monster indices 106–112** carry no known monster (the Switch editor labels them
  *Unknown*), and index 134 is unnamed. Names for 105 and 113–137 are taken from the
  editor, not yet read back in-game — see
  [02 — Monster records](docs/02-monster-records.md).

## Licence

Released into the public domain. Use freely, including in save editors.
No warranty — verify against your own data before writing to anyone's save.
