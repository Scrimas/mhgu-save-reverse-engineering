# 09 — Awards

The Guild Card's award grid is one LSB-first bitfield: one bit per award, set once
earned. Neither save editor maps it. Its MHXX 3DS offset (`0x1B8A`, 13 bytes) is
commented out in their `Offsets.cs` and reads as all zeros on Switch.

| Structure | Offset | Size | Valid bits | Confidence |
|---|---|---|---|---|
| Awards earned | `base + 0xC8115` (slot 1: `0x254DB1`) | 17 bytes | 0–131 (132) | CONFIRMED |

Offsets are **relative to the character base** (see
[07 — Equipment § Character slots](07-equipment.md#character-slots)). The field sits
inside the Guild Card block (`base + 0xC71BD`), directly after the last quest-history
record, and is followed by zero bits 132–135.

## Layout

The in-game award screen has one grid per location. Each grid is stored as a
contiguous run, in on-screen reading order (left to right, top to bottom):

| Bits | Grid | Slots |
|---|---|---|
| 0–29 | Wycademy | 30 |
| 30–54 | Bherna | 25 of 26, see below |
| 55–69 | Kokoto | 15 |
| 70–84 | Pokke | 15 |
| 85–99 | Yukumo | 15 |
| 100–101 | no visible award, see below | 2 |
| 102–131 | Soaratorium | 30 |

```
earned(bit) = (buf[base + 0xC8115 + (bit >> 3)] >> (bit & 7)) & 1
```

## Evidence

Known-plaintext match. Each of the six in-game grids was read as a bit vector
(lit = 1, empty = 0) and searched for in the save. All six appear, in grid order,
inside one 132-bit window. Every bit agrees, and the field's popcount (74) equals the
number of lit slots across all six screens. A 131-slot vector matching by chance is
not plausible.

**CONFIRMED** by a controlled write. Setting bit 0 made Wycademy slot 1 appear
in-game as *Bherna Chief's Ornamental Belt* ("completed all 1★ and 2★ Village
Quests"), and no other award appeared or vanished. The bit was then cleared again.

**`?` slots are computed, not stored.** Once bit 0 was set, Wycademy slots 2 and 3
turned from empty to `?`. A `?` marks the next tier of an award series already
started, so it follows from the earned bits and has no bit of its own. Wycademy
slot 29 showed `?` before the write and stores 0.

## Open questions

- **UNRESOLVED — Bherna's 26th slot**, *A Pat on the Back* ("your first step into
  the world of monster hunting", crossed-swords icon, earned). Bherna's first 25
  slots fill bits 30–54 and Kokoto starts immediately at 55, so slot 26 is not in the
  Bherna run. It is **not** bit 100 or 101 either: clearing bit 101 and setting bit
  100 changed nothing on any of the six grids. Possibly granted unconditionally or
  stored elsewhere.
- **UNRESOLVED — bits 100–101.** No visible effect in either state. The analysed save
  has 100 = 0 and 101 = 1; leave them as found.
- **UNRESOLVED — award names/IDs.** Only positions are mapped; names come from the
  in-game descriptions.
