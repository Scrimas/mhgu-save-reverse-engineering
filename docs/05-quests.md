# 05 — Quests

Every quest in the game (Village, Hub, G-rank, Arena, Training, Special Permit,
Prowler and the built-in event quests) is tracked by **one list index**, shared by
three parallel bitmaps (cleared, seen, and one unresolved). The full index table is
[`data/quest-index.csv`](../data/quest-index.csv).

## Quest bitmaps — `base + 0x2C77`

| Bitmap | Offset (relative) | Slot 1 absolute | Meaning |
|---|---|---|---|
| Cleared | `base + 0x2C77` | `0x18F913` | quest cleared at least once |
| Seen | `base + 0x2D77` | `0x18FA13` | quest has been highlighted on the board (clears **NEW**) |
| Third | `base + 0x2E77` | `0x18FB13` | **UNRESOLVED**, see below |

Each bitmap is 1509 bits (189 bytes, list indices 0–1508), LSB-first as elsewhere:

```
byte = bitmap + (index >> 3)
mask = 1 << (index & 7)
```

Index 0 is a placeholder and is never set. Nothing is stored past index 1508 up to
the next `0x100` boundary. The 19 bytes `0x18F900`–`0x18F912` hold something else and
are **not** part of the quest bitmap. Earlier revisions of this document put the
bitmap at `0x18F900`, so their bit numbers are 152 higher than the list indices.

### The index is a position in the game's quest list

**CONFIRMED.** The bit index is the quest's position in the game resource
`quest\quest_group` (type `rQuestGroup`, in `loc/arc/village/common.arc`), and has
no arithmetic relation to the quest ID. That is why every ID-based formula failed.

The resource layout:

```
0x00  u32   header (0x40800000)
0x04  u32   entry count (1509)
0x08  entry[count], 7 bytes each, packed:
        +0  u32  quest ID (entry 0 = 0, the placeholder)
        +4  u8   group (0 = regular, 1-40 = unlock chains, 127 event Hub,
                 128 event Arena, 129 Prowler); DERIVED from the distribution only
        +5  u8   almost always 0
        +6  u8   0/1, meaning UNRESOLVED
```

The executable's clear check (`0x523DA4` in the v1.4 NSO, ARM32) takes a bitmap
pointer and a quest ID. It linearly searches the loaded list from index 1 for the ID,
and tests `bitmap[index]`. An ID that is not found falls back to index 0. The setters
for the seen bitmap (`0x523E44`) and the third bitmap (`0x526B98`) address it as
`cleared + 0x100` and `cleared + 0x200`, using the same index.

The list is identical in the base game and the v1.4 update.

Evidence that the index is correct, all from the analysed save:

- A controlled diff that cleared G-rank quest 11463 (*Seregios Scuffle*) moved
  exactly one bit, which is index 795.
- All six quests in the history log (814, 11234, 11302, 11303, 11357, 11463) are set.
- The 228 Special Permit quests occupy indices 947–1174. This is exactly the deviant
  level bitmap of [03 — Deviants](03-deviants.md), found independently: global bit
  `0x18F913*8 + 947` is `0x18F989` bit 3.
- Every cleared quest is also seen, and no bit is set outside the list, in any of
  the three bitmaps.

### Quest ID scheme

IDs are decimal, `E P T SS NN`:

| Digit(s) | Meaning |
|---|---|
| `E` (×1 000 000) | 1 = built-in event quest |
| `P` (×100 000) | 1 = Prowler-only quest |
| `T` (×10 000) | 0 Village, 1 Hub, 2 Arena, 3 Training, 4 Special Permit |
| `SS` | star level: Village 1–10, Hub 1–7, G-rank 11–14 (G★1–G★4). Special Permit: deviant 1–18, in the order of [03](03-deviants.md) |
| `NN` | sequence. Special Permit: level, 1–10 = Lv1–Lv10, 11–15 = G1–G5, 16 = EX. The 6 GU deviants only have 11–16 |

`rank` in the CSV comes from byte `0x12` of each quest's `questData` resource,
which matches `SS` for every regular quest and also gives the rank of event quests.

### List order

| Indices | Contents |
|---|---|
| 1–337 | Village (1049 and 1050 appear twice, see below) |
| 338–865 | Hub, Low → High → G-rank |
| 866–946 | Prowler Village, Prowler Hub |
| 947–1174 | Special Permit |
| 1175–1287 | Training (Prowler Training at 1182–1189) |
| 1288–1304 | Arena, Prowler Arena |
| 1305–1508 | Event quests (Hub, then Arena), 15 of them `DUMMY` placeholders |

| Category | Entries |
|---|---|
| Village | 335 (+2 duplicates) |
| Hub (incl. G-rank) | 528 |
| Special Permit | 228 |
| Training | 105 |
| Arena | 11 |
| Prowler (Village / Hub / Training / Arena) | 40 / 41 / 8 / 6 |
| Event (Hub / Prowler Hub / Arena / Prowler Arena) | 112 / 34 / 30 / 13 |

**Duplicates.** Village quests 1049 and 1050 appear at indices 313–314 and again at
315–316. The search stops at the first match, so 315–316 are never read. They are
flagged in the CSV and should be left alone.

### Third bitmap

Not board visibility: none of these are hidden quests. 13 bits are set in the analysed save: 10318, 11422, 11457, 11468, 40401, 41411,
41511, 41611, 41614, 41616, 1010150, 1011001, 1011030. This is a mix of regular,
permit and event quests, all of them seen, and some not cleared. **UNRESOLVED**

### Controlled writes

**CONFIRMED — cleared.** Setting the cleared bit of an uncleared Village ★2 quest
(202, *Harvest Tour: Dunes*) made it display as cleared in-game.

**CONFIRMED — the second bitmap is "seen", not "unlocked".** Evidence:

- Setting it for a hidden Village ★6 quest (607, *The Perilous Pair*), together with
  the cleared bit, did **not** make the quest appear.
- A visible quest (612, *Break the Brachydios*) had the bit clear and showed
  **NEW**.
- With the bit restored to 0, Hub ★2 *Poisonous Pest* (10227) showed **NEW**. Moving
  the cursor onto it and saving flipped exactly one bit across all three bitmaps:
  its seen bit, index 392, 0 → 1. Opening a list without highlighting anything
  changes nothing.

**Board visibility is not stored in these bitmaps.** For 607 the reason is that it
is a villager request. See [Villager requests](#villager-requests--tableactivitydataatd).

## Where a quest is posted — `questData + 0x11`

Byte `0x11` of each quest's `questData` resource names the board that lists it
(field name from the [MHXX rQuestData notes](https://github.com/svanheulen/mhff/wiki/MHXX-rQuestData-Format)):

| Value | Board |
|---|---|
| 1–4 | One village only (7 quests each at most; meaning of 1–4 vs 5–8 unresolved) |
| 5 / 6 / 7 / 8 | Kokoto / Pokke / Yukumo / Bherna |
| 9 | Prowler |
| 10 | Every board |
| 11 | Special Permit |

The 5–8 mapping comes from the quest names (Jurassic Frontier quests at 5, Popo and
Giaprey at 6, *The Yukumo Gal Special* at 7, Moofah quests at 8). It agrees with the
village field of the request table below.

Almost every quest with a value of 1–8 is a villager request. It appears only after
the request has been accepted, and only on that village's board.

## Villager requests — `table/activityData.atd`

A standalone table in the romfs. Header: u32 `0x40A00000`, u32 count 184. It is followed by
184 records of 55 bytes. The full table is in [`data/request-index.csv`](../data/request-index.csv).

| Offset | Type | Meaning |
|---|---|---|
| `+0x00` | u32 | Record index |
| `+0x04` | u8 | Kind: 0 = quest, 1 = delivery, 2 = unknown, 3 = end marker |
| `+0x05` | u8 | Stage: 5–10 match Village ★1–★6, 11–14 Village ★7–★10, 15–21 Hub ★1–★7, 22–25 G1–G4, 26 late G4. Inferred from the stars of the quests. |
| `+0x06` | u8 | NPC. Records with the same NPC form one character's request list. |
| `+0x07` | u8 | Village: 0 Bherna, 1 Kokoto, 2 Pokke, 3 Yukumo |
| `+0x16` | u32 | Quest ID, for kind 0 |
| `+0x1A` | u32 | Prerequisite quest. Set on one record only: 625 needs 10730. |
| `+0x25` | u16 + u8 | Reward ID and count. Item IDs for tickets (Kokoto Ticket ×2 …); the Argosy Captain's 10220 reward, `0x6D9`, arrived in-game as a Poogie costume. |
| `+0x33` | u16 | **Accepted** flag index into the [request flag bitmap](#request-flags--base--0x2c56d) |
| `+0x35` | u16 | **Completed** flag index (always accepted + 1) |

Record 40 is *The Perilous Pair*: Argosy Captain (NPC `0x21`), Kokoto, stage 10.

**CONFIRMED — the posted-in village is not why 607 is hidden.** It was checked on the ★6 board in
Bherna and in Kokoto, and it was absent from both.

### Request flags — `base + 0x2C56D`

| Field | Offset | File offset | Size | Status |
|---|---|---|---|---|
| Event flag bitmap | `base + 0x2C56D` | `0x1B9209` | 192 bytes, 1536 bits, LSB-first | CONFIRMED |
| Three more maps | `base + 0x2C62D` | `0x1B92C9` | 3 × 24 bytes | UNRESOLVED |
| Two u32 | `base + 0x2C675` | `0x1B9311` | 8 bytes, change on every save (RNG-like) | UNRESOLVED |

The block is one object of the game (flags at `+0x500`, serializer `0x240ce4`). Each
request record names two bits in the first map:

- **accepted** (`record + 0x33`): the NPC's request is active. For kind 0 this is
  what **posts the quest on the village board**.
- **completed** (`record + 0x35`): reported back to the NPC, reward given.

The indices are not regular (`300 + 2·record` holds only for the first 17 records),
so take them from [`data/request-index.csv`](../data/request-index.csv).

**CONFIRMED**, three independent lines:

1. All 184 records agree with the quest bitmaps: accepted ⇔ quest seen (one
   exception, accepted but never hovered), completed ⇒ cleared. This offset is the
   only byte-aligned one in the character block with zero violations.
2. Reporting *Ahoy! Royal Ludroth!* (10220) to the Argosy Captain set exactly bit
   395, its completed flag, plus three unrelated flags (41, 796, 1569).
3. Controlled write: setting bit 396 alone (`0x1B923A` `0x0C → 0x1C`, both slots)
   made *The Perilous Pair* (607) appear on the Kokoto ★6 board. Hovering it then
   set its seen bit as usual.

In the executable, the quest-list builder `0x79da8c` tests the accepted flag
(`record + 0x3a` in memory) and the request memo UI (`cUIOHNActivityMemo`) reads
both. The loader is `rActivityData` `0x3c9ce0` (float version 5.0, 64-byte records
in memory, parser `0x13c00`).

### What did not unlock 607 through play

Clearing *The Fated Four* (621), then clearing and reporting the Captain's other
request (10220), did not make him offer 607. The stage gate was already met (five
other stage-10 requests cleared), and per-NPC order is not the gate (607's stage is
lower than 10220's). The posted-in village is not the reason either.

Other flags those steps changed, meaning **UNRESOLVED**: Fated Four set `+0x2C60`
bit 2 and `+0x315B` / `+0x316F` bit 2; the Captain report set `+0x3161` / `+0x3175`
bit 3 and `+0x2FA0` / `+0x2FA8` bit 6.

**UNRESOLVED — what makes an NPC offer a request.** No code sets the accepted flag
from the request record: none of the 43 callers of the flag setter `0x244f14` reads
it. The setter is reached from the NPC talk script interpreter (`0x3d2e1c`, flag
index taken from script data), and conditions go through the jump-table evaluator
at `0x2451f8`. The offer condition therefore lives in the talk scripts, not in
`activityData.atd`. `record + 0x31` (u16, mostly 0, 500 on some) is unexplained.

### Editing

To mark a quest cleared, set its cleared bit, and its seen bit if you don't want a
leftover NEW marker. Use OR, as always. This does not make a hidden quest appear.

To make a villager-request quest appear, set its **accepted** flag in the request
flag bitmap. Leave the completed flag alone: the NPC sets it, and hands over the
reward, when the cleared quest is reported.

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
| `0xA1C4` (41412) | Rustrazor Ceanataur G2 |
| `0xA228`–`0xA22C` (41512–41516) | Soulseer Mizutsune G2 … EX |
| `0xA2F1`–`0xA2F4` (41713–41716) | Elderfrost Gammoth G3 … EX |

These follow the Special Permit scheme above: `40000 + 100 × deviant + level`,
with the deviant numbered from 1.

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

- **UNRESOLVED — the third bitmap** (`base + 0x2E77`).
- **UNRESOLVED — flag bytes +4/+6** of `quest_group` entries. Byte +4 looks like
  unlock-chain grouping (values 1–40 on Village and Hub key quests), but this is
  inferred from the distribution only.
- **UNRESOLVED — the 19 bytes at `0x18F900`** that precede the bitmap.
- **UNRESOLVED — quest history record layout** beyond ID and name. The documented
  u16 ID cannot hold event IDs (≥ 1 000 000). Either the field is wider, or event
  quests log differently.
- **UNRESOLVED — board visibility of every-board quests.** Villager requests are
  solved (accepted flag, see [Request flags](#request-flags--base--0x2c56d)). For
  quests posted on every board, the unlock rule has not been studied. Needed to
  grant access to locked quests, including the G-rank deviant gate of
  [03](03-deviants.md).
- **UNRESOLVED — the NPC offer condition** for villager requests (talk scripts).
- **UNRESOLVED — the other 1168 event flags** and the three 24-byte maps after them.
- **UNRESOLVED — `questData+0x11` values 1–4** versus 5–8.

## A caution on bulk edits

Setting every bit is still a bad idea. Index 0, the duplicate slots 315–316, the
`DUMMY` event entries, and the space past index 1508 are not real quests. Key
quests and urgents may also drive state stored elsewhere, such as HR, village
progress and story flags, which a bitmap edit does not touch. Set the bits for real
quests from the CSV, and expect rank progression to still need the key quests
cleared in play.
