#!/usr/bin/env python3
"""List the villager requests not accepted yet and what their NPC still waits for. Read-only.

The conditions in ../data/request-offer.csv come from the NPC talk data
(see ../docs/10-npc-talk.md). Conditions this tool cannot evaluate are printed as "?".

Usage:  request_offer.py [path/to/system]
"""
import sys, csv, pathlib

BASE      = 0x18CC9C        # character slot 1
HR        = 0x28            # u16
CLEARED   = 0x2C77          # quest bitmap, index from quest-index.csv
VIL_STAR  = 0x2C4DA         # u16
HUB_STAR  = 0x2C4DC         # u16
FLAGS     = 0x2C56D         # event flag bitmap
NPC_HOLD  = 0x2C62D         # per-NPC bits, map A: no request offers until the next quest

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "system"
    buf = pathlib.Path(path).read_bytes()
    index = {}
    for row in csv.DictReader(open(DATA / "quest-index.csv")):
        index.setdefault(int(row["quest_id"]), int(row["index"]))

    def bit(off, i):
        return (buf[BASE + off + (i >> 3)] >> (i & 7)) & 1
    u16 = lambda off: int.from_bytes(buf[BASE + off:BASE + off + 2], "little")
    hr, vil, hub = u16(HR), u16(VIL_STAR), u16(HUB_STAR)

    def missing(c):
        """None if the condition holds, a description if not, '?...' if unknown."""
        kind, _, arg = c.partition(":")
        if kind == "flag":         return None if bit(FLAGS, int(arg)) else f"event flag {arg}"
        if kind == "notflag":      return None if not bit(FLAGS, int(arg)) else f"event flag {arg} must be clear"
        if kind == "cleared" and arg.isdigit() and int(arg) in index:
            return None if bit(CLEARED, index[int(arg)]) else f"clear {arg}"
        if kind == "village_star": return None if vil >= int(arg) else f"Village star level {arg}"
        if kind == "hub_star":     return None if hub >= int(arg) else f"Hub star level {arg}"
        if kind == "hr":           return None if hr >= int(arg) else f"HR {arg}"
        return "?" + c

    print(f"HR {hr}, Village star level {vil}, Hub star level {hub}")
    for row in csv.DictReader(open(DATA / "request-offer.csv")):
        if bit(FLAGS, int(row["accept_flag"])):
            continue
        alts = row["offer"].split(" OR ") if " OR " in row["offer"] else None
        conds = alts or [c for c in row["offer"].split(" AND ") if c]
        miss = [m for m in map(missing, conds) if m]
        if alts and len(miss) < len(alts):          # any alternative holds
            miss = []
        hold = row["npc_bit"] and bit(NPC_HOLD, int(row["npc_bit"]))
        need = "; ".join(miss) if miss else "ready"
        print(f"{row['index']:>4}  {row['quest_id']:>6}  {row['quest_name'] or '(delivery)':<34} "
              f"{row['npc_name']:<20} flag {row['accept_flag']:>4}  <- {need}{'  [NPC on hold]' if hold else ''}")

if __name__ == "__main__":
    main()
