#!/usr/bin/env python3
"""Validate the documented MHGU save structures against a real save file.

Reads a save using ONLY the offsets and layouts described in ../docs, and prints
what it finds. If the documentation is correct, the output is self-evidently
sensible: permit counts in range, weapon totals reconciling, monster names lining
up with plausible hunt counts.

Usage:  validate.py [path/to/system]
"""
import sys, csv, pathlib

PERMITS   = 0x18F4D8
CLEARED   = 0x18F989 * 8 + 3
UNLOCKED  = CLEARED + 0x100 * 8
TALLIES   = 0x192B40
SIZES     = 0x192D62
WEAPONS   = {"village": 0x254713, "hub": 0x254731, "arena": 0x25474F}
QUESTBITS = (0x18F900, 128)

DEVIANTS = ["Redhelm Arzuros","Snowbaron Lagombi","Stonefist Hermitaur","Dreadqueen Rathian",
            "Drilltusk Tetsucabra","Silverwind Nargacuga","Crystalbeard Uragaan","Deadeye Yian Garuga",
            "Dreadking Rathalos","Thunderlord Zinogre","Grimclaw Tigrex","Hellblade Glavenus",
            "Nightcloak Malfestio","Rustrazor Ceanataur","Soulseer Mizutsune","Boltreaver Astalos",
            "Elderfrost Gammoth","Bloodbath Diablos"]
WEAPON_ORDER = ["Great Sword","Sword and Shield","Hammer","Lance","Heavy Bowgun","Light Bowgun",
                "Long Sword","Switch Axe","Gunlance","Bow","Dual Blades","Hunting Horn",
                "Insect Glaive","Charge Blade","Prowler"]

def block(i):
    return (i * 16, 16) if i < 12 else (192 + (i - 12) * 6, 6)

def bit(buf, g):
    return (buf[g >> 3] >> (g & 7)) & 1

def u16(buf, o):
    return int.from_bytes(buf[o:o+2], "little")

def main(path):
    buf = pathlib.Path(path).read_bytes()
    print(f"file: {path}  ({len(buf)} bytes)")
    if len(buf) != 5159100:
        print("  WARNING: unexpected size; offsets may not apply")

    print("\n--- deviants (permit / cleared levels / highest cleared) ---")
    for i, name in enumerate(DEVIANTS):
        off, width = block(i)
        lv = [bit(buf, CLEARED + off + j) for j in range(width)]
        top = max((j for j, v in enumerate(lv) if v), default=None)
        label = "none" if top is None else ("EX" if top == width - 1 else f"level {top+1}")
        print(f"  {name:22s} permit {buf[PERMITS+i]:3d}  cleared {sum(lv):2d}/{width}  highest: {label}")

    print("\n--- weapon usage ---")
    tot = [0]*15
    for venue, base in WEAPONS.items():
        row = [u16(buf, base + 2*w) for w in range(15)]
        for w in range(15):
            tot[w] += row[w]
        print(f"  {venue:8s} " + " ".join(f"{v:4d}" for v in row))
    print("  " + "-"*8 + " " + " ".join(f"{v:4d}" for v in tot) + "   <- all")
    main_w = max(range(15), key=lambda w: tot[w])
    print(f"  most used: {WEAPON_ORDER[main_w]} ({tot[main_w]})")

    print("\n--- monsters (named entries with a non-zero tally) ---")
    idx = {}
    csvp = pathlib.Path(__file__).parent.parent / "data" / "monster-index.csv"
    if csvp.exists():
        for r in csv.DictReader(csvp.open()):
            if r["monster"]:
                idx[int(r["index"])] = r["monster"]
    shown = 0
    for i in sorted(idx):
        t = u16(buf, TALLIES + 2*i)
        if not t:
            continue
        mn, mx = u16(buf, SIZES + 4*i), u16(buf, SIZES + 4*i + 2)
        size = "-" if 72 <= i <= 104 else f"{mn}%-{mx}%"
        print(f"  [{i:3d}] {idx[i]:24s} {t:4d} hunts   size {size}")
        shown += 1
    print(f"  ({shown} of {len(idx)} named indices have hunts)")

    lo, n = QUESTBITS
    print(f"\n--- quests ---")
    print(f"  cleared bitmap 0x{lo:X}: {sum(bin(b).count('1') for b in buf[lo:lo+n])} / {n*8} bits set")

if __name__ == "__main__":
    default = pathlib.Path.home()/".config/Ryujinx/bis/user/save/0000000000000001/0/system"
    main(sys.argv[1] if len(sys.argv) > 1 else default)
