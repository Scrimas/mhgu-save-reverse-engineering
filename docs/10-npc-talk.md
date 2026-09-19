# 10 — NPC talk data

What an NPC says, when it offers a request, and which event flags the conversation
sets are all in one table per NPC. This is where the **accepted** flags of
[05](05-quests.md#request-flags--base--0x2c56d) and the star-level flags of the
[unlock rules](05-quests.md#board-visibility--scriptcheck_quest_unlocked) are set
during normal play.

## Files — `table/npc/script/npc_NNN_td.ntd`

171 NPCs, three files each, standalone in the romfs:

| File | Content |
|---|---|
| `table/npc/script/npc_NNN_td.ntd` | Talk data: one 37-byte record per text line |
| `<lang>/table/npc/script/npc_NNN_td_<lang>.gmd` | The text; string *i* belongs to record *i* |
| `table/npc/script/npc_NNN_is.nis` | 20-byte records, not read yet |

`NNN` is the NPC ID: 52 Argosy Captain, 1 Bherna Chief, 2 Bherna Gal, 520 Guild
Manager, 502 Wycademy Gal, 701 Wyventurer, 702 Soaratorium Gal, 801 Pub Manager,
802 Questender. The loader is `rNpcTalkData` (`0x23d808`, path format at
`0x155d130`), the selector is `0x243d00`, the condition evaluator `0x2451c8` and the
action executor the function around `0x2479b8`.

Header: f32 `1.0`, u32 record count. Record:

| Offset | Type | Meaning |
|---|---|---|
| `+0` | u32 | Line index |
| `+4` | u8 | Line type. 1 = text line. 2, 7, 8, 10, 14, 15 end a block (mask `0x3161` in the selector) |
| `+5` | u8 | **Talk kind** of the block, on its first line only (0 on the others). See below |
| `+6` | u8 | Direct-lookup ID (compared with a u16 of the request context), rarely used |
| `+7` | u8 | **Village star level test** |
| `+8` | u8 | **Hub star level test** |
| `+9` | 3 × {u16 type, u16 a, s16 b} | Conditions |
| `+27` | u16, u16 | Action 1: type 1 = set event flag, 2 = clear event flag; flag index |
| `+31` | u16, u16, u16 | Action 2: type, value, parameter |

A **block** is a run of lines up to the next end line. The selector collects the
block, tests the star levels and the conditions of every line in it, and plays the
first block of the requested kind that passes.

Star level test, value *v* against the level at [`base + 0x2C4DA` / `+0x2C4DC`](05-quests.md#star-levels--base--0x2c4da):
`1–20` level = *v*, `21–40` level ≥ *v* − 20, `41–60` level ≤ *v* − 40, `0` no test.

Talk kinds seen: 1 ordinary talk, 3 story announcement, **4 chief request offer**,
**5 request report**, 6 chief request report, **8 request offer**, 9 and 11–49
other events. A block of kind 3, 8 or 9 is skipped while the NPC is on hold for that
kind, see [per-NPC bits](#per-npc-bits--base--0x2c62d).

### Conditions

All three must hold. Type 15 is an empty slot that evaluates true. Types 16–21
repeat 1, 2, 11–14 and switch the block to "any of" (**DERIVED** from the selector's
two code paths; 6 request blocks use them).

| Type | Test | Status |
|---|---|---|
| 1 / 2 | event flag *a* set / not set | CONFIRMED (code + save) |
| 11 / 12 | quest *b* cleared / not cleared (`0x523da4`) | CONFIRMED (code + save) |
| 13 / 14 | Village / Hub key quest set *b* all cleared (`0x3b1a18` / `0x3b1d70`) | from code |
| 28 | HR ≥ *b* | from code |
| 64 | true at once if bit 31 of the u32 at `base + 0x2F77` is set, else a runtime test | partly read |
| 65 | bit 20 of the u32 at `base + 0x2F77` | from code, meaning UNRESOLVED |
| 67–70 | village points of Bherna / Kokoto / Pokke / Yukumo ≥ *b* (`0x523b50`) | from code |
| 86 / 87 | a state word is 1 / is not 1. The footbath visitors (NPC 420–428) use 87 for a one-line "have a seat, then we'll talk" and 86 for the real conversation, so this is "seated in the Yukumo footbath" | DERIVED |
| 92 | NPC *b* has none of its three per-NPC bits set | from code |
| 30, 31, 63, 71–84 … | not implemented, always true | from code |

The jump table of the evaluator is at `0x2451fc` (163 types); only the ones that
request blocks use were read.

### Actions

Action 1 sets or clears an event flag. Action 2, jump table at `0x247cac`:

| Type | Effect | Status |
|---|---|---|
| 1 | hand over *parameter* × item/reward *value* (10220's report: 1833 × 1, the Poogie costume) | DERIVED |
| 2 / 3 / 26 | set the speaker's bit (or NPC *parameter*'s) in per-NPC map A / B / C | from code + save |
| others | not read | — |

## Request offers

A request is offered by a block of kind 8 (villagers) or 4 (chiefs). One of its lines
sets the request's **accepted** flag with action 1; the report block (kind 5 / 6)
sets the **completed** flag. The offer conditions of 181 of the 184 requests are in
[`data/request-offer.csv`](../data/request-offer.csv) (generator:
`scratch/py/mkoffer.py`, joins talk data to `request-index.csv` by the accepted flag).

`tools/request_offer.py <save>` lists the requests not accepted yet with what their
NPC still waits for. Read-only.

| Column | Meaning |
|---|---|
| `index`, `quest_id`, `quest_name` | From `request-index.csv` |
| `npc_file` | NPC ID, the `NNN` of the talk file |
| `npc_bit`, `npc_name` | The NPC's bit in the per-NPC maps, which is also its index in `NpcName_<lang>.gmd` and the NPC byte `+0x06` of the request record |
| `talk_kind`, `talk_line` | Block kind (4 / 8) and its first line |
| `accept_flag` | Flag the block sets |
| `offer` | Conditions besides "accepted flag not set yet": `village_star:N`, `hub_star:N` (≥), `village_eq` / `hub_eq`, `flag:N`, `notflag:N`, `cleared:Q`, `group_done:N`, `hr:N`, `npc_idle:NPC`, `footbath`, `condT:a:b` for unread types |

The Argosy Captain (NPC 52), whose *The Perilous Pair* (607) started this:

| Line | Kind | Conditions | Sets |
|---|---|---|---|
| 9 | offer | Hub ★ ≥ 2, flag 394 clear | 394: 10220 accepted |
| 19 | report | 395 clear, 10220 cleared | 395, reward 1833, map A bit |
| 29 | offer | **Village ★ ≥ 6, 396 clear, 395 set** | 396: 607 accepted |
| 36 | report | 397 clear, 607 cleared | 397, reward 1834, map A bit |
| 45 | offer | Hub ★ ≥ 5, 398 clear, 397 set | 398 |
| 64 | offer | Hub ★ ≥ 7, 400 clear, 399 set, condition 64 | 400: 10732 accepted |

So 607 needs 10220 **reported**, not merely cleared. That is why clearing The Fated
Four changed nothing, and it matches the earlier notes that stage and posting village
are not gates.

**Evidence.** Of the 115 requests accepted in the save, every flag, cleared-quest,
star-level and HR condition of their offer block holds: zero violations. `npc_bit`
equals the NPC byte of the request record in 174 of 185 rows (the other 11 are offered
from a different NPC's file). The Captain's report in snapshots `req-2 → req-3` set
exactly what line 19 says: flag 395, flag 796 (action 1 of the next line) and bit 33
of map A. Bit 33 of map A is "flag 1569" of the earlier diff, which is past the end of
the 1536-bit flag map.

## Per-NPC bits — `base + 0x2C62D`

Three 24-byte bitmaps follow the event flags in the same object (`+0x5c0`, `+0x5d8`,
`+0x5f0`; serializer `0x240ce4`):

| Map | Offset | File offset | Blocks talk kind |
|---|---|---|---|
| A | `base + 0x2C62D` | `0x1B92C9` | 8, request offers |
| B | `base + 0x2C645` | `0x1B92E1` | 9 |
| C | `base + 0x2C65D` | `0x1B92F9` | 3, story announcements |

The bit index is the NPC's position in the u16 table at `0x162793c` (188 entries,
lookup `0x23e640`): 1, 2, 3 … 12, 14, 15, 20 … so NPC 52 is bit 33. The same index
orders `NpcName_<lang>.gmd` (entry 33 is "Argosy Captain").

A set bit puts the NPC on hold for that kind. The context builder `0x243bd4` turns
bit A / B / C of the NPC into mask `0x100` / `0x200` / `0x8`, and the selector skips
blocks whose kind has its mask bit set. A request report sets the NPC's map A bit
(action 2). `0x38b904`, a step of the quest flow (called from `0x3866a4`; it also
re-rolls the rotating quests through `0x54b0d4`), passes map A and the length 72 to a
memclr-style import, which wipes all three maps. **DERIVED**: an NPC that just took a
report offers its next request only after the next quest. All maps are empty in every
snapshot taken right after a quest (`req-1`, `req-2`). This explains the observation
"reported 10220, got the costume, Captain offered nothing": bit 33 was set by that
report and is still set in the save.

For an editor the maps only matter as a nuisance: a set bit delays an offer until the
next quest. Setting the accepted flag directly bypasses the conversation entirely.

## Star-level flags

The flags that list a whole star level (Village 4, 12, 16, 25, 29, 34, 1008, 1025,
1035, 1053; Hub 101 … 125; G 1401 … 1413) are set by two announcement blocks of
kind 3, not by quest code:

1. The chief (Bherna Chief 1; Wyventurer 701 for ★7+; Guild Manager 520; Pub Manager
   801 for G) has a block "star level = L, flag *N − 1* clear", often with "urgent quest cleared" (402, 501, 713,
   806, 906, 10768, 11204, 11319). It sets *N − 1* and hands over a reward.
2. The quest counter NPC (the four village Gals 2, 102, 202, 302; Soaratorium Gal
   702; Wycademy Gal 502; Questender 802) has a block "star level = L, *N − 1* set,
   *N* clear" that sets *N*.

Flag *N* is what the unlock script tests. The numeric star level at
`base + 0x2C4DA` / `+0x2C4DC` is the input of both blocks, so it is raised first, by
code that was not located. **UNRESOLVED**: that writer (expected in the quest-result
path next to the urgent key-quest counters).

`script\debug_flag_control` (`arc/debug/dbgResident.arc`, same bytecode as the unlock
script) is a developer shortcut for the same state and confirms two more opcodes:
`0x31 N` sets event flag N, `0x32 N` clears it, `0x33 Q` marks quest Q cleared
(handlers `0x3d2cdc`, `0x3d2d7c`, `0x3d2e28`). Its G-rank entry sets
flags 131, 132, 1400, 1401, 1403, 1405, 1407, 1408, 1409, 1411, 1413 and clears the
urgents 10768, 11204, 11319, 11401. `script\related_flag_control` only sets flag 2
from a talk callback.

## Open questions

- **UNRESOLVED — conditions 64, 65, 102, 113, 114, 121, 139, 140, 151** and the
  action 2 types other than 1, 2, 3, 26.
- **UNRESOLVED — requests 22 and 117** have no offer block that sets their flag.
- **UNRESOLVED — `npc_NNN_is.nis`.**
- **Not yet tested — a write to the per-NPC maps.** Their role rests on the code and
  on one snapshot pair.
