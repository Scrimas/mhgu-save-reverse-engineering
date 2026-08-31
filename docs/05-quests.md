# 05 — Quests

The weakest-mapped area of the save. The structures are located; the **quest ID to
bit index mapping is not solved**, which is what an editor would actually need.

## Cleared-quest bitmap — `0x18F900`

128 bytes = 1024 bits. LSB-first within each byte, as elsewhere in this format.

**CONFIRMED — one bit per quest, set on first clear.** A controlled test cleared a
single previously-uncleared G-rank quest. Exactly one bit in the whole block changed:
`0x18F965` bit 7, `0 → 1`. No other bit in the region moved.

**CONFIRMED — deviant quests are not tracked here.** A separate controlled test
cleared a new deviant level (Rustrazor Ceanataur G2, previously only G1). This block
did not change at all. Deviant progress lives exclusively in the deviant level
bitmaps described in [03 — Deviants](03-deviants.md).

In the analysed save 272 of 1024 bits were set. The block is one of several; the
region beyond `0x18F980` was not surveyed, so 1024 is a lower bound on total quest
capacity, not the true size.

### Unsolved: quest ID → bit index

The obvious hypothesis — that the bit index is the quest ID, or a fixed offset from
it — was tested and **falsified**. Known quest IDs recovered from the history log
were checked against the bitmap: under every linear mapping tried, a quest known to
be cleared landed on a bit that was zero.

The bitmap therefore uses a compact internal slot index, dense over quests that
actually exist, unrelated to the sparse quest ID space. Recovering it needs a
per-quest table, most plausibly built by clearing known quests one at a time and
recording which bit moves — the same controlled-diff technique used throughout, but
requiring one quest per data point.

## Quest history log — `0x2546D7`

A record array of recently completed quests.

| Field | Offset in record | Type |
|---|---|---|
| Quest ID | `+0x00` | u16 |
| Quest name | `+0x02` | UTF-16LE, null-terminated |

Record stride is `0xA0` bytes. The trailing portion of each record was not
identified — plausibly timestamp, venue, party and reward data.

This log is the most useful entry point for anyone attacking the quest system: it
pairs numeric IDs with human-readable names in plaintext, so a partial quest ID table
can be harvested from a well-played save by walking the records with no prior
knowledge.

### Quest IDs observed

| ID | Quest |
|---|---|
| `0xA1C4` | Rustrazor Ceanataur G2 |
| `0xA228`–`0xA22C` | Soulseer Mizutsune G2 … EX |
| `0xA2F1`–`0xA2F4` | Elderfrost Gammoth G3 … EX |

Deviant quest IDs are consecutive within a deviant and ascend with level, so a
deviant's full ID range can be extrapolated from any two known points. The base
offsets differ per deviant and no formula was derived.

## Counters

| Offset | Type | Behaviour |
|---|---|---|
| `0x192AEA` | u16 | Increments by 1 per completed quest |
| `0x25476E` | u16 | Increments by 1 per completed quest |

Both were observed advancing in lockstep across two independent quest completions.
They hold different values, so they count different things — plausibly total quests
versus quests counted toward the Guild Card. Neither was pinned to a specific
on-screen figure.

`0x25476E` sits immediately after the Arena weapon-usage array, so it may belong to
the Guild Card statistics block rather than the quest system.

## Open questions

- **UNRESOLVED — quest ID to bit index.** The blocking problem for quest editing.
- **UNRESOLVED — bitmap extent.** Only `0x18F900`–`0x18F97F` was surveyed. MHGU has
  well over 1024 quests across Village, Hub, Arena, Special Permit and Prowler, so
  further blocks must exist.
- **UNRESOLVED — quest history record layout** beyond ID and name.
- **UNRESOLVED — key/unlock quest flags.** Urgent quests and rank-up gates are likely
  tracked separately from plain clears.

## A caution on bulk edits

Marking every bit in the cleared-quest bitmap is a bad idea. Roughly three quarters
of the bits in the surveyed block were clear, so setting them all would mark hundreds
of quests cleared — including quests that were never unlocked, and quests that may
not exist. A save in that state can look fine for hours and break at a rank
transition or an unlock check. Prefer setting known bits, and pay the cost of
mapping them first.
