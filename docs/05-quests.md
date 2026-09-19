# 05 — Quests

Every quest in the game (Village, Hub, G-rank, Arena, Training, Special Permit,
Prowler and the built-in event quests) is tracked by **one list index**, shared by
three parallel bitmaps (cleared, seen, failed). The full index table is
[`data/quest-index.csv`](../data/quest-index.csv); its `group`, `alt` and `expansion`
columns are bytes `+4` … `+6` of the `quest_group` entry described below.

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
        +4  u8   group: 0 = regular, 1-10 = key quests of Village ★1-★10,
                 11-17 = key quests of Hub ★1-★7, 19-22 = G★1-G★4,
                 24-33 = urgents that raise the Village star level to 1-10,
                 34-46 = urgents that raise the Hub star level to 1-13,
                 47-86 = twin quests in pairs (47/48, 49/50, ...), 127 event Hub,
                 128 event Arena, 129 Prowler
        +5  u8   alternative set inside a key group (quests sharing a value count once)
        +6  u8   1 = quest added by the XX / Generations Ultimate expansion, 0 = from
                 the first game. DERIVED: 1 on every G-rank and Village ★7-★10 quest,
                 0 on every Village ★1-★6 and Hub ★1-★3 quest
```

The executable's clear check (`0x523DA4` in the v1.4 NSO, ARM32) takes a bitmap
pointer and a quest ID. It linearly searches the loaded list from index 1 for the ID,
and tests `bitmap[index]`. An ID that is not found falls back to index 0. The setters
for the seen bitmap (`0x523E44`) and the third bitmap (`0x526B98`) address it as
`cleared + 0x100` and `cleared + 0x200`, using the same index.

The group byte is read by the key-quest counters `0x3b1964` / `0x3b1a18` (Village,
groups 1–10) and `0x3b1d70` (Hub, groups 11–23), which count total and cleared
quests of one group. For groups 47–86 the cleared setter (`0x523f30` via `0x526a38`)
also sets the partner quest of the pair (group ± 1), e.g. 308 ↔ 309. The urgent
groups are read by the star level update, see
[star levels](#star-levels--base--0x2c4da).

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

### Third bitmap — failed quests

**DERIVED.** The only setter (`0x526b98`) is called from the quest result code
(`0x388d60`) on the branch where the quest did *not* succeed, and only if the quest
ended in end state 5 (`0x3a5ed0` case 4 tests byte `+0x50` of the quest object). The
success branch sets the cleared bit instead. No code clears the bit again.

The only reader (`0x526c84`) is the Hunter's Notes unlock `0x55515c`: a monster's
entry opens if its quest is cleared **or** has this bit, so a failed attempt still
counts as having met the monster.

13 bits are set in the analysed save: 10318, 11422, 11457, 11468, 40401, 41411,
41511, 41611, 41614, 41616, 1010150, 1011001, 1011030. That fits: all are hard
quests (Old Fatalis, Boltreaver EX …), and 11422 is failed but never cleared. Which
of the failure kinds state 5 is (three faints, time up, abandon) was not separated.
It is not board visibility: none of these quests is hidden.

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
| 1 / 2 / 3 / 4 | Home village Kokoto / Pokke / Yukumo / Bherna of a quest that is *not* a villager request. **DERIVED** from the members: 1 holds the Verdant Hills tours and *Alas, Astalos Again*, 2 Arctic Ridge and Gammoth, 3 Misty Peaks and Mizutsune, 4 Glavenus. Same village order as 5–8. Whether a board filters on it was not checked |
| 5 / 6 / 7 / 8 | Kokoto / Pokke / Yukumo / Bherna |
| 9 | Prowler |
| 10 | Every board |
| 11 | Special Permit |

The 5–8 mapping comes from the quest names (Jurassic Frontier quests at 5, Popo and
Giaprey at 6, *The Yukumo Gal Special* at 7, Moofah quests at 8). It agrees with the
village field of the request table below.

Almost every quest with a value of 1–8 is a villager request. It appears only after
the request has been accepted, and only on that village's board.

## Board visibility — `script\check_quest_unlocked`

**CONFIRMED.** Whether a board lists a quest is not stored per quest. Each time a
list is built the game runs a script with the quest ID and shows the quest only if
the script returns 1. The script reads state that *is* in the save: the
[event flags](#request-flags--base--0x2c56d), the cleared bitmap, HR and the Hub
star level. The full rule table is
[`data/quest-unlock.csv`](../data/quest-unlock.csv), and
[`tools/quest_unlock.py`](../tools/quest_unlock.py) evaluates it against a save and
prints what each locked quest is missing.

The script is the resource `script\check_quest_unlocked` (type `rCommonScript`) in
`loc/arc/village/common.arc`. It is byte-identical in the base game and v1.4.

### Rule syntax in the CSV

All predicates of a rule must hold (`AND`).

| Predicate | Meaning | Save field |
|---|---|---|
| `flag:N` | event flag N is set | bit N of `base + 0x2C56D` |
| `cleared:Q` | quest Q is cleared | cleared bitmap |
| `atleast:K:Q1\|Q2…` | at least K of the listed quests are cleared | cleared bitmap |
| `all:Q1\|Q2…` | all listed quests are cleared (the key quests of one Hub level, `quest_group` group 11–22) | cleared bitmap |
| `hr:N` | HR ≥ N | u16 `base + 0x28` |
| `hub_star:N` | Hub star level ≥ N | u16 `base + 0x2C4DC` |
| `always` | no condition | |
| *(empty)* | event quest (ID ≥ 1 000 000): not in the script, listed whenever it is installed | |

How the 1302 rules split: 762 quests need one event flag, 293 one cleared quest, 122
an `atleast`, 118 nothing, 96 an HR, 37 a full key-quest set, 25 a Hub star level.

The flags that open a whole star level:

| Board | Flags, in star order |
|---|---|
| Village ★1–★6 | 4, 12, 16, 25, 29, 34 |
| Village ★7–★10 | 1008 (+1069, 1070), 1025 (+1029), 1035 (+1050), 1053 |
| Hub ★1–★7 | 101, 105, 109, 113, 117, 121, 125 |
| G★1–G★4 | 1401, 1405, 1409, 1413 (+1415) |

For 148 of the villager-request quests the rule is exactly `flag:<accepted flag>` of
the request table, which was found independently. 19 chief requests use another flag.

**The G-rank deviant gate** of [03](03-deviants.md) is an ordinary rule: G1 needs
Lv10 cleared **and** one G-rank quest against the base monster, for example
`41111` (Grimclaw G1) = `cleared:41110 AND atleast:1:11405|11462`. EX is
`cleared:<G5> AND hr:100`. Lv1 needs one Hub quest against the base monster (10124
for Redhelm) or 10768.

### Evidence

1. Evaluated on the analysed save, the rules unlock 1116 quests and lock 186. All
   990 quests with the seen bit set are among the unlocked ones, with **zero
   violations**, and no locked quest is seen or cleared. One wrong field would show
   up here: a wrong offset for the Hub star level produced 25 violations at once.
2. The rule for 607 is `flag:396`, the bit whose controlled write made the quest
   appear ([above](#request-flags--base--0x2c56d)). On the snapshot taken before
   that write the tool reports 607 locked for that reason.
3. The deviant rules match the behaviour recorded in [03](03-deviants.md): G-rank
   Arzuros released Redhelm's G-rank levels.

4. Controlled write of a flag that no request uses: setting event flag 1059 alone
   (`0x1B928D` `0x00 → 0x08`, both slots) made the five Village ★10 quests whose rule
   is `flag:1059` appear: *Advanced: Wrong One Silver*, *Heart of Gold*, *Steel
   Yourself*, *Karma Chameleos* and *Empire of the Sun*. The last three are also in
   the rotating table below, and their bits (29–31) were set at the time.

5. Controlled write of cleared bits: setting the cleared bit of *Misty Opportunity?*
   (11404, `0x18F976` `0x4A → 0xCA`) made *Appeal from Authority* (11446) appear on the
   G★4 list. Its rule is `all:… AND atleast:1:11404 AND hr:13`, and 11404 was the
   only missing part.
6. The same write set the cleared bit of *The White Brute* (619, `0x18F926`
   `0x30 → 0x38`), the whole rule of *It's Electric* (618). 618 did **not** appear: it
   is a rotating quest and its rotation bit was clear. Setting that bit (next
   section) listed it. Rule and rotation are both required, as decoded.

`hub_star` has had no controlled write of its own; it rests on the code and on the
consistency test. `hr` was only part of the 11446 rule, where it already held.

### Script format

```
0x00  f32   1.0
0x04  u32   instruction count (5535)
0x08  instruction[count]:
        u32  line number
        u8   opcode
        cstr operand A
        cstr operand B
```

The interpreter (`0x3d17f8`, opcode table at `0x3d5874`) runs top to bottom with
`[WORK0]` = quest ID. A failed test skips forward to a marker opcode, there is no
other control flow.

| Opcode | Meaning |
|---|---|
| `0x20 [WORK0] N` | if quest ID ≥ N, skip to the next `0x24` (one section per ID range) |
| `0x0E [WORK0] Q` | label: if quest ID = Q, jump to the next `0x26`, the rule body |
| `0x13 [HR] N` | between labels: if HR < N, skip to `0x23`. The labels after it need HR ≥ N |
| `0x27` | no label matched: skip to `0x23` |
| `0x41 N` | `[WORK1]` = event flag N (`[0x1884c58] + 0x500`) |
| `0x76 Q` | `[WORK1]` = quest Q cleared (`0x523da4`) |
| `0x7E` | `[WORK1]` = Hub star level (`[0x18979f0] + 0x3e2`) |
| `0x9E N` | `[WORK1]` = all quests of `quest_group` group N + 10 cleared (`0x3b1d70`) |
| `0x52 [WORK2] 0`, `0x50 [WORK2] [WORK1]` | `WORK2 = 0`, `WORK2 += WORK1`: counts cleared quests |
| `0xA1 a b`, `0xA7 a b` | require a = b, a ≥ b. On failure the script returns 0 |
| `0x16 [HR] N` | if HR < N, skip to the next `0x26` (an alternative body) |
| `0x31 N`, `0x32 N` | set / clear event flag N. Not in this script; used by `script\debug_flag_control` |
| `0x33 Q` | mark quest Q cleared. Same |
| `0x03` | return 1 |
| `0x02` | end of section, return −1: not in the script, treated as locked |

`[HR]` is the u16 at `+0x554` of the player object. `[FESTA_HR]` appears in 14
alternative bodies for a convention build and is dropped from the CSV. One label has
an empty quest ID, a typo in the shipped script.

The board's list filler is `0x54b994`. For each quest of the star level it asks
`0x3b2174` → `0x3d7e90`, which runs the script and caches the answer. Event quests
skip the script (`0x3b9870`: ID / 1 000 000 mod 10 = 1). Which archives get loaded
(`0x3b8090`) depends only on the ID and the place, not on the save.

### Rotating quests — `base + 0x504B`

**CONFIRMED.** A second filter applies to 51 quests held in a table in the executable
(`0x162cde4`, 8 bytes each: quest ID and a u32 parameter), listed in
[`data/rotating-quests.csv`](../data/rotating-quests.csv). Such a quest is listed only
if its bit, the table index, is set in the u64 at `base + 0x504B` (file `0x191CE7`).
A quest of this table needs its script rule **and** its bit.

The game re-rolls the field in `0x54b1c4`. In the snapshots it changed after every
completed quest and never otherwise. Entries 0–7 are the four village pairs 308/309,
319/320, 324/325, 329/330, of which one each stays set; 8/9 are 618/619. The rest are
elder dragon and other repeating hunts (10329–10333, 10641–10643, 10756–10761,
11316–11318, 11412–11417, 11458–11460, …). The low byte of the parameter is 100, 80,
50, 40, 25 or 0, **DERIVED** to be the chance in percent; the other bytes are
**UNRESOLVED**.

Controlled write: with its rule satisfied, *It's Electric* (618, bit 8) stayed hidden
while the bit was clear. Setting it (`0x191CE8` `0xBE → 0xBF`, both slots) listed the
quest next to its partner 619. `tools/quest_unlock.py` reports such quests as
`rotated`.

### Star levels — `base + 0x2C4DA`

| Field | Offset | File offset | Type | Analysed save |
|---|---|---|---|---|
| Village star level | `base + 0x2C4DA` | `0x1B9176` | u16, 1–10 | 10 |
| Hub star level | `base + 0x2C4DC` | `0x1B9178` | u16, 1–13 | 13 |

They are fields `+0x3e0` / `+0x3e2` of the object serialized by `0x507e20`, the
block just before the event flags (149 bytes from `base + 0x2C4D8`; it also holds
four 32-byte pet names). The Hub value is **CONFIRMED** by the consistency test
above. The Village value is **CONFIRMED** the same way by the talk data: the
request offer blocks test it (`village_star` in
[`request-offer.csv`](../data/request-offer.csv)) and all accepted requests agree. The
talk data also sets the star-level flags from these two numbers, see
[10](10-npc-talk.md#star-level-flags).

**What raises them — CONFIRMED (code + controlled write).** `0x50cbd0` walks `quest_group`. For every urgent
group it counts the members and how many of them are cleared. If a group has members,
all of them are cleared, and the stored level is lower than the group's level, the
level is set to the group's level. It never lowers a level, and a level can be
skipped. Two exceptions: while the Village level is 5 only 601 counts in group 29,
and while it is 9 only 1005 counts in group 33, so the final bosses in those groups
do not hold the level back.

The function runs right after the cleared bit is set in the quest result code
(`0x388e54`), from talk condition 64 while its latch is clear (`0x3f12fc`), and from a
setup sequence at `0x6aa5d0` that an ordinary load does not go through.

Controlled write: the Hub level was lowered from 13 to 12 (`0x1B9178`
`0x0D → 0x0C`, both slots) with every urgent still cleared. After loading the
character, walking through four villages and saving, the file still held 12. After
one cleared quest (1038, not an urgent) it held 13 again. **CONFIRMED**: loading does
not recompute the level, clearing any quest does. For an editor: write the level
together with the urgents' cleared bits, or just the cleared bits and let the next
quest clear raise the level. The star-level *flags* still
need the two conversations of [10](10-npc-talk.md#star-level-flags), or a direct
edit.

| Level | Group | Urgents (the quest list shows an urgent under the level it unlocks) |
|---|---|---|
| Village 1 | 24 | — (no member, never applies) |
| Village 2 | 25 | 206 *Vaulting Outlaw* (Village 2) |
| Village 3 | 26 | 303 *Tusked Tantrum* (Village 3) |
| Village 4 | 27 | 402 *The Nocturnal Enchanter* (Village 4) |
| Village 5 | 28 | 501 *The Dark Age* (Village 5) |
| Village 6 | 29 | 601 *The Scorching Blade* (Village 6), 620 *Stop the Wheel* (Village 6) |
| Village 7 | 30 | 713 *Research Team's First Rodeo* (Village 7) |
| Village 8 | 31 | 806 *Primal Forest Arachnids* (Village 8) |
| Village 9 | 32 | 906 *Wish upon a...Gravios?* (Village 9) |
| Village 10 | 33 | 1005 *Beware the Comet of Disaster* (Village 10), 1026 *Grave Peril* (Village 10), 1017 *King of Hellfire* (Village 10), 1018 *The Seat of a God* (Village 10), 1019 *Stormlord* (Village 10), 1039 *Blazing Black of a Dark God* (Village 10) |
| Hub 1 | 34 | — (no member, never applies) |
| Hub 2 | 35 | 10216 *The New Tenant* (Hub 2) |
| Hub 3 | 36 | 10307 *A Shocking Scoundrel* (Hub 3) |
| Hub 4 | 37 | 10335 *Two-headed Carcass* (Hub 3) |
| Hub 5 | 38 | 10531 *A Plesioth in the Misty Peaks* (Hub 5) |
| Hub 6 | 39 | 10606 *A Bewitching Dance* (Hub 6), 10608 *The Unshakable Mountain God* (Hub 6) |
| Hub 7 | 40 | 10710 *Seer of Swords* (Hub 7) |
| Hub 8 | 41 | 10722 *Hellfire Star* (Hub 7) |
| Hub 9 | 42 | 10768 *Legendary Skills?* (Hub 7) |
| Hub 10 | 43 | 11204 *Dirty Deals* (Hub G2) |
| Hub 11 | 44 | 11319 *Giant Dragon Invasion* (Hub G3) |
| Hub 12 | 45 | 11401 *Sky Render* (Hub G4) |
| Hub 13 | 46 | 11432 *Castle on the Run* (Hub G4) |

Hub level 0 means the Hub is not joined yet: the constructor writes Village 1, Hub 0,
and the Guild Manager's first conversation sets Hub 1 (talk action 1 type 10,
`0x247bf0`). In the analysed save every group is fully cleared, which gives 10 / 13,
the stored values.

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
| Per-NPC bits A / B / C | `base + 0x2C62D` | `0x1B92C9` | 3 × 24 bytes, one bit per NPC: on hold for request offers / kind 9 talk / story announcements. See [10](10-npc-talk.md#per-npc-bits--base--0x2c62d) | map B CONFIRMED by write, A and C from code |
| Two u32 | `base + 0x2C675` | `0x1B9311` | 8 bytes, change on every save. The first (`+0x608` of the object) is a random number: talk conditions 106–108 compare it modulo 10000 with a threshold, which makes a line appear with a fixed chance | from code |

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
   395, its completed flag, plus 41, 796 and "1569". The talk data explains two of
   them: 796 is set by the next line of the same conversation, and 1569 is past the
   end of this map, it is bit 33 (the Captain) of per-NPC map A.
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

Other flags those steps changed, meaning **UNRESOLVED**. The quest block serializer
(`0x51d12c`) places them: Fated Four set bit 10 of the u32 at `base + 0x2C5F` and bit
34 of the 20-byte maps at `base + 0x3157` / `+0x316B`; the Captain report set bit 83
of the same two maps and bit 14 of the 8-byte words at `base + 0x2F9F` / `+0x2FA7`.
Such fields come in pairs, a state word and a copy that drives a one-time notice.

**What makes an NPC offer a request** is in the NPC's talk data, see
[10 — NPC talk data](10-npc-talk.md) and [`data/request-offer.csv`](../data/request-offer.csv).
The Captain offers 607 when the Village star level is ≥ 6 and flag 395 is set, which
is 10220 **reported** to him. The report also puts him on hold (per-NPC map A) until
the next quest, so in that session he had nothing to offer. No code sets the accepted
flag from the request record: the talk action does (`0x247a00`), and conditions go
through the evaluator `0x2451c8`. `record + 0x31` (u16) is the Wycademy points the
report pays: it equals the parameter of talk action 2 type 4 in the report block on
all five records where it is not 0 (500 four times, 200 once). **DERIVED**

### Editing

To mark a quest cleared, set its cleared bit, and its seen bit if you don't want a
leftover NEW marker. Use OR, as always. This does not make a hidden quest appear by
itself, but it can satisfy the `cleared` / `atleast` / `all` rule of another quest.

To make a hidden quest appear, satisfy its rule from
[`data/quest-unlock.csv`](../data/quest-unlock.csv): set the event flag, or the
cleared bit of the prerequisite, or raise HR or the Hub star level.
`tools/quest_unlock.py <save> <quest id>` prints what is missing. Flag rules are
confirmed by two controlled writes (396 and 1059), `cleared` / `all` / `atleast` by
one (11404 → 11446, 619 → 618). A rotating quest also needs its bit at
`base + 0x504B`, which lasts until the next completed quest.

For a villager-request quest the flag is its **accepted** flag. Leave the completed
flag alone: the NPC sets it, and hands over the reward, when the cleared quest is
reported.

Setting a star-level flag lists the quests, it does not replay what the game does
when that level is reached in play (urgent notices, HR, cutscenes), so expect the
other progress fields to stay as they were.

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

- **Not separated — which failure** sets the [third bitmap](#third-bitmap--failed-quests)
  (end state 5).
- **UNRESOLVED — the 20 bytes before the bitmap** (`base + 0x2C63`, 12 + 8 bytes,
  fields `+0xd78` / `+0xd84` of the quest object). The 3 × 24 bytes before them
  (`base + 0x2C13`) are the Hunter Arts bitmap of [08](08-progression.md) and two
  copies that drive notices. The same serializer walk also lands on the Canteen
  ingredients of 08 (`base + 0x2F8F`), which cross-checks the field map.
- **UNRESOLVED — quest history record layout** beyond ID and name. The documented
  u16 ID cannot hold event IDs (≥ 1 000 000). Either the field is wider, or event
  quests log differently.
- **Not checked — whether a board filters on `questData+0x11` values 1–4.**

## A caution on bulk edits

Setting every bit is still a bad idea. Index 0, the duplicate slots 315–316, the
`DUMMY` event entries, and the space past index 1508 are not real quests. Key
quests and urgents also drive state stored elsewhere: HR and the star-level event
flags, which a bitmap edit does not touch. The numeric star levels at
`base + 0x2C4DA` are recomputed from the urgents' cleared bits only when a quest is
cleared, not on load, see [star levels](#star-levels--base--0x2c4da).
Set the bits for real quests from the CSV. Rank progression then still needs either
the key quests cleared in play or those fields edited as well.
