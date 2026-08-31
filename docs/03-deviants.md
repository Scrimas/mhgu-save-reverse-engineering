# 03 — Deviants

Deviants (*Nyanta* variants — Redhelm, Dreadqueen, Hellblade, …) have three separate
pieces of save state: a **permit count**, a **cleared-level bitmap**, and an
**unlocked-level bitmap**.

## Deviant index order

**CONFIRMED** by exact fingerprint. The permit array was located by searching for the
player's full 18-value permit vector, including a distinctive outlier, and matched at
exactly one offset in the file. The order is therefore fixed and unambiguous:

| # | Deviant | Levels | | # | Deviant | Levels |
|---|---|---|---|---|---|---|
| 0 | Redhelm Arzuros | 16 | | 9 | Thunderlord Zinogre | 16 |
| 1 | Snowbaron Lagombi | 16 | | 10 | Grimclaw Tigrex | 16 |
| 2 | Stonefist Hermitaur | 16 | | 11 | Hellblade Glavenus | 16 |
| 3 | Dreadqueen Rathian | 16 | | 12 | Nightcloak Malfestio | 6 |
| 4 | Drilltusk Tetsucabra | 16 | | 13 | Rustrazor Ceanataur | 6 |
| 5 | Silverwind Nargacuga | 16 | | 14 | Soulseer Mizutsune | 6 |
| 6 | Crystalbeard Uragaan | 16 | | 15 | Boltreaver Astalos | 6 |
| 7 | Deadeye Yian Garuga | 16 | | 16 | Elderfrost Gammoth | 6 |
| 8 | Dreadking Rathalos | 16 | | 17 | Bloodbath Diablos | 6 |

Deviants 0–11 originate in Generations and have **16 levels**: Lv1–Lv10, then G1–G5,
then EX. Deviants 12–17 are GU-exclusive and have only **6 levels**: G1–G5, then EX.
This asymmetry drives the bitmap layout below.

## Permit counts — `0x18F4D8`

18 consecutive u8, one per deviant, in the index order above. Caps at 99.

```
permits[i] = u8 at 0x18F4D8 + i
```

## Level bitmaps

Two bitmaps of identical layout:

| Bitmap | Base bit address | Meaning |
|---|---|---|
| Cleared | byte `0x18F989`, bit 3 | levels the player has completed |
| Unlocked | byte `0x18FA89`, bit 3 | levels available to select |

The second is exactly `0x100` bytes after the first. Bits are **LSB-first** within
each byte: global bit `g` lives at byte `g >> 3`, mask `1 << (g & 7)`.

Note the base is **not** byte-aligned — it starts three bits into `0x18F989`. Any
implementation must address bits globally rather than walking bytes.

### Block layout

Blocks are **mixed-width**, packed with no padding:

```
def block(i):
    if i < 12:  return (i * 16,             16)   # Gen deviants
    else:       return (192 + (i - 12) * 6,  6)   # GU deviants
```

Total: `12 × 16 + 6 × 6 = 228` bits per bitmap.

Within a block, bit `j` is level `j` in progression order, and the **final** bit
(`j == width - 1`) is EX. So for a Gen deviant bit 0 is Lv1 and bit 15 is EX; for a
GU deviant bit 0 is G1 and bit 5 is EX.

```
bit_index(deviant, level) = base + block(deviant).offset + level
```

A uniform 6-bit stride was tried first and produces impossible states — clears at G3
and above with G1 and G2 unset, which sequential progression forbids. That
contradiction is the tell that the layout is mixed-width. With the correct model
every set bit in the analysed save was accounted for exactly, with none left over.

### Reference implementation

```python
NAMES = ["Redhelm Arzuros","Snowbaron Lagombi","Stonefist Hermitaur",
         "Dreadqueen Rathian","Drilltusk Tetsucabra","Silverwind Nargacuga",
         "Crystalbeard Uragaan","Deadeye Yian Garuga","Dreadking Rathalos",
         "Thunderlord Zinogre","Grimclaw Tigrex","Hellblade Glavenus",
         "Nightcloak Malfestio","Rustrazor Ceanataur","Soulseer Mizutsune",
         "Boltreaver Astalos","Elderfrost Gammoth","Bloodbath Diablos"]

PERMITS  = 0x18F4D8
CLEARED  = 0x18F989 * 8 + 3          # global bit address
UNLOCKED = CLEARED + 0x100 * 8

def block(i):
    return (i * 16, 16) if i < 12 else (192 + (i - 12) * 6, 6)

def get_bit(buf, g):
    return (buf[g >> 3] >> (g & 7)) & 1

def set_bit(buf, g):
    buf[g >> 3] |= 1 << (g & 7)

def read_levels(buf, i):
    """Return the list of cleared level bits for deviant i."""
    off, width = block(i)
    return [get_bit(buf, CLEARED + off + j) for j in range(width)]

def clear_all_but_ex(buf):
    """Set every level except EX, for every deviant, in both bitmaps."""
    for base in (CLEARED, UNLOCKED):
        for i in range(18):
            off, width = block(i)
            for j in range(width - 1):        # width-1 skips the EX bit
                set_bit(buf, base + off + j)
```

Use OR rather than assignment so existing EX clears are preserved.

## Unlock gating

Two gates, and they are independent. Only the first lives in these bitmaps.

**EX requires G5 cleared and HR 100.** Satisfied by setting the level bits.

**CONFIRMED — G-rank deviant levels additionally require hunting the base monster in
G-rank.** This gate is *not* stored in the deviant bitmaps. Setting every level bit
leaves affected deviants displaying "Lv10 cleared" with no G1 or higher quest
offered. Hunting the corresponding base monster once at G-rank immediately releases
them; this was verified by hunting G-rank Arzuros, after which Redhelm's EX quest
appeared without any further save edit.

Where this flag is recorded was never established. The cleared-quest bitmap
(see [05 — Quests](05-quests.md)) is the obvious candidate, but a mapping from
G-rank quests to bits was never derived, so the gate could not be set directly.

Practically: an editor can grant deviant levels, but cannot currently grant G-rank
deviant *access* without the player hunting each base monster once at G-rank.

## Open questions

- **UNRESOLVED — the G-rank base-monster gate.** The highest-value unknown here.
  Likely a bit in the cleared-quest bitmap or a per-monster G-rank flag.
- **UNRESOLVED — deviant tally indices.** Only Rustrazor Ceanataur (121) and Soulseer
  Mizutsune (122) are placed in the monster tally array. The Gen deviants sit below
  index 105 adjacent to their base monsters — Redhelm at 49 next to Arzuros at 48,
  Deadeye at 17 next to Yian Garuga at 16 — but several remain unmapped.
