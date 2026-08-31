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
| [05 — Quests](docs/05-quests.md) | Cleared-quest bitmap, quest history log, counters |
| [06 — Methodology](docs/06-methodology.md) | How this was derived, and how to extend it |

Machine-readable: [`data/monster-index.csv`](data/monster-index.csv)

## Quick reference

| Structure | Offset | Layout |
|---|---|---|
| Header nonce | `0x000014` | u32, changes every write, **not** a checksum |
| Deviant permit counts | `0x18F4D8` | 18 × u8 |
| Quest-cleared bitmap | `0x18F900` | 128 bytes = 1024 bits |
| Deviant levels (cleared) | bit `0x18F989`.3 | mixed-width bitfield, 228 bits |
| Deviant levels (unlocked) | bit `0x18FA89`.3 | same layout, `+0x100` bytes |
| Quest counter | `0x192AEA` | u16 |
| Monster hunt tallies | `0x192B40` | u16 × ~139, indexed by monster ID |
| Monster size records | `0x192D62` | (u16 min%, u16 max%) × N, stride 4, same index |
| Weapon usage — Village | `0x254713` | 15 × u16 |
| Weapon usage — Hub | `0x254731` | 15 × u16 |
| Weapon usage — Arena | `0x25474F` | 15 × u16 |
| Quest history log | `0x2546D7` | stride `0xA0` records |

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
  was ever present in the analysed file, so it is unknown whether these structures
  repeat at a per-character stride. **An editor must not assume these offsets are
  absolute for arbitrary saves.** This is the single most important gap.
- **Region portability.** Only the EU/western build was examined. Japanese builds
  may differ.
- **Monster indices 105–112** are consistently zero and were never identified as
  either real monster slots or padding.
- **Roughly a dozen monster indices** below 105 remain unmapped — see
  [02 — Monster records](docs/02-monster-records.md).

## Licence

Released into the public domain. Use freely, including in save editors.
No warranty — verify against your own data before writing to anyone's save.
