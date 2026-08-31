# 02 — Monster records

Two parallel arrays, both indexed by the same internal **monster index**.

| Structure | Offset | Element | Applies to |
|---|---|---|---|
| Hunt tally | `0x192B40` | u16 | all monsters |
| Size record | `0x192D62` | (u16 min%, u16 max%), stride 4 | large monsters only |

```
tally[i]   = u16 at 0x192B40 + 2*i
size_min[i] = u16 at 0x192D62 + 4*i
size_max[i] = u16 at 0x192D62 + 4*i + 2
```

## Index space

**CONFIRMED** by cross-referencing which indices carry size records against which
carry only tallies:

| Range | Contents | Size records? |
|---|---|---|
| 0–71 | Large monsters | yes |
| 72–104 | Small monsters | **no** |
| 105–112 | Always zero — padding or unused slots | — |
| 113–138 | Additional large monsters, incl. GU-exclusive deviants | yes |
| 139+ | Not part of these arrays | — |

The small-monster block at 72–104 is the structural detail that defeats naive
alignment attempts. Small monsters have hunt counts but **no** size record, so any
code that walks both arrays in lockstep desynchronises at index 72 and every
subsequent mapping is wrong. This cost considerable effort to discover.

A handful of large monsters also lack size records — those with no size variation in
game, such as Nakarkos. Absence of a size record is therefore not proof of a small
monster.

## Hunt tallies — `0x192B40`

u16, one per monster, counting monsters slain or captured.

**CONFIRMED — deviant hunts do not roll up into the base monster.** Killing two
Rustrazor Ceanataur incremented index 121 (Rustrazor) from 1 to 3 while leaving
index 20 (Shogun Ceanataur) at 2 and index 90 (small Ceanataur) at 18. A displayed
base count and a displayed deviant count are independent totals; the family total is
their sum.

## Size records — `0x192D62`

Two u16 per large monster, the smallest and largest specimen seen, as a percentage
of the base size. Crown thresholds are derived from these by the game.

**CONFIRMED** twice by controlled hunts:

| Hunt | Offset touched | Change | Index |
|---|---|---|---|
| 2 × G-rank Arzuros | `0x192E22` / `0x192E24` | min 100→91, max 113→120 | 48 |
| Deviant Ceanataur | `0x192F46` / `0x192F48` | min 100→97, max 106→113 | 121 |

Both land exactly on `0x192D62 + 4*index`, and both indices independently agree with
the tally array — the two structures cross-validate each other.

`(0, 0)` means never hunted. To mark a monster hunted, a non-zero tally **and** a
non-zero size record are both needed for large monsters; small monsters need only
the tally.

Writing min/max within roughly 90–115% marks a monster as hunted without fabricating
gold or silver crown records.

## Monster index table

Recovered by writing self-identifying markers — each slot `i` set to `100 + i`, then
read back off the in-game Monster List, so the game itself reports its own indices.
See [methodology](06-methodology.md).

Confidence:
- **[C]** CONFIRMED — controlled write or hunt diff, two independent lines
- **[V]** DERIVED, count-validated — marker readout, and the stored value matches an
  independently reported hunt count
- unmarked — DERIVED from the marker readout alone

### Large monsters, 0–71

| # | Monster | | # | Monster |
|---|---|---|---|---|
| 0 | *unmapped* | | 36 | *unmapped* |
| 1 | *unmapped* | | 37 | Uragaan |
| 2 | Gold Rathian | | 38 | Crystalbeard Uragaan |
| 3 | Dreadqueen Rathian **[V]** | | 39 | Lagiacrus |
| 4 | Rathalos | | 40 | Royal Ludroth **[V]** |
| 5 | Silver Rathalos | | 41 | Agnaktor |
| 6 | Dreadking Rathalos | | 42 | Alatreon |
| 7 | Khezu | | 43 | Duramboros |
| 8 | Yian Kut-Ku **[V]** | | 44 | Nibelsnarf |
| 9 | Gypceros **[V]** | | 45 | Zinogre |
| 10 | Plesioth | | 46 | Thunderlord Zinogre |
| 11 | Kirin | | 47 | Amatsu |
| 12 | Velocidrome **[V]** | | 48 | **Arzuros [C]** |
| 13 | Gendrome **[V]** | | 49 | Redhelm Arzuros |
| 14 | Iodrome **[V]** | | 50 | *unmapped* |
| 15 | Cephadrome **[V]** | | 51 | Snowbaron Lagombi **[V]** |
| 16 | Yian Garuga | | 52 | Volvidon **[V]** |
| 17 | Deadeye Yian Garuga | | 53 | Brachydios |
| 18 | Daimyo Hermitaur **[V]** | | 54 | Kecha Wacha **[V]** |
| 19 | Stonefist Hermitaur | | 55 | Tetsucabra **[V]** |
| 20 | Shogun Ceanataur | | 56 | Drilltusk Tetsucabra |
| 21 | Blangonga | | 57 | Zamtrios |
| 22 | *unmapped* | | 58 | Najarala |
| 23 | *unmapped* | | 59 | Seltas Queen |
| 24 | Kushala Daora | | 60 | Gore Magala |
| 25 | Chameleos | | 61 | Shagaru Magala |
| 26 | Teostra | | 62 | Seltas **[V]** |
| 27 | Bulldrome **[V]** | | 63 | *unmapped* |
| 28 | Tigrex | | 64 | *unmapped* |
| 29 | Grimclaw Tigrex | | 65 | *unmapped* |
| 30 | Akantor | | 66 | Hellblade Glavenus **[V]** |
| 31 | Lavasioth | | 67 | Astalos |
| 32 | *unmapped* | | 68 | Mizutsune **[V]** |
| 33 | Silverwind Nargacuga **[V]** | | 69 | Gammoth |
| 34 | Ukanlos | | 70 | Nakarkos |
| 35 | *unmapped* | | 71 | *unmapped* |

### Small monsters, 72–104

| # | Monster | | # | Monster | | # | Monster |
|---|---|---|---|---|---|---|---|
| 72 | Aptonoth | | 83 | Cephalos | | 94 | Altaroth |
| 73 | Apceros | | 84 | Bullfango | | 95 | Jaggi |
| 74 | Kelbi | | 85 | Popo | | 96 | Jaggia |
| 75 | Mosswine | | 86 | Giaprey | | 97 | Ludroth |
| 76 | Hornetaur | | 87 | Anteka | | 98 | Uroktor |
| 77 | Vespoid | | 88 | Remobra | | 99 | Slagtoth |
| 78 | Felyne | | 89 | Hermitaur | | 100 | Gargwa |
| 79 | Melynx | | 90 | Ceanataur | | 101 | Zamite |
| 80 | Velociprey | | 91 | Blango | | 102 | Konchu |
| 81 | Genprey | | 92 | Thenoplos | | 103 | Maccao |
| 82 | Ioprey | | 93 | Bnahabra | | 104 | Larinoth |

### GU block, 113–138

| # | Monster |
|---|---|
| 121 | **Rustrazor Ceanataur [C]** |
| 122 | Soulseer Mizutsune **[V]** |
| others | **UNRESOLVED** |

Index 121 is confirmed twice over — the tally diff and the size-record diff from the
same controlled hunt both point at it.

## Reliability of the table

The mapping reproduces **16 of 16** independently reported hunt counts, spread across
large monsters, small monsters and a GU-block deviant. That is far beyond
coincidence and the table can be relied on in bulk.

Individual entries are weaker than the aggregate. The readout was transcribed by hand
from 15 screens, and seven entries came back duplicated. Five were adjacent rows on
the same screen sharing one value — the signature of a transcription slip, not a
structural feature. Where the stored value could be checked against a known hunt
count the ambiguity resolved cleanly, which is what the **[V]** tag records; those
are the entries listed above. Their partners are consequently unplaced, which is why
several very common monsters — **Rathian, Nargacuga, Lagombi, Glavenus, Seregios,
Great Maccao, Malfestio** — are absent from the table despite certainly existing
below index 105.

**Anyone extending this work should redo the marker pass and transcribe it
mechanically** — screenshot OCR, or reading fewer entries per pass. The technique is
sound; only the hand transcription was lossy.

## Open questions

- **UNRESOLVED — indices 105–112.** Consistently zero. Either padding, or eight
  monsters never hunted in the analysed save. A marker pass covering this range
  would settle it immediately.
- **UNRESOLVED — most of 113–138.** Only two entries placed. A second marker pass
  using a distinct value range (e.g. `1000 + i`) over 105–199 would map the rest.
- **UNRESOLVED — ~12 indices below 105**, listed above as *unmapped*.
- **UNRESOLVED — captures vs kills.** The Guild Card renders counts as `N(M)`, where
  `M` appears to be captures. The tally array holds only one number per monster, so
  the capture count lives in a structure not yet located.
