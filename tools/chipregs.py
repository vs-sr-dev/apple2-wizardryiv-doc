#!/usr/bin/env python3
"""Every custom-chip register reached as d16(An), for a chosen base register.

The inherited `regscan.py` walks forward linearly from each `lea $dff000,aN`
and stops at the first rts.  On gs2.run that finds one access, because the base
is loaded in one routine and used in another: a5 is a *global* chip base held
across calls, which the linear walk cannot follow.

This scan does the opposite and does not try to be clever: it finds every
instruction word whose effective-address field is d16(An) for the given An,
takes the following word as the displacement, and keeps it when it is an even
value below 0x200 -- i.e. a real custom register offset.  That over-counts
(a displacement can land inside an immediate), so the count is an upper bound;
what it is good for is telling you *which* registers appear at all, and where,
so the sites can be read by hand.

    python3 tools/chipregs.py FILE [--reg 5] [--only BLTSIZE,BLTCON0]
"""
import sys, argparse, collections, struct, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REG = {}
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "regscan.py"),
           encoding="utf-8").read()
start = src.index("REG = {")
blob = src[start:src.index("\n}\n", start) + 3]
exec(blob, REG)
REG = REG["REG"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--reg", type=int, default=5, help="address register number")
    ap.add_argument("--only")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    d = open(a.file, "rb").read()
    want = set(a.only.split(",")) if a.only else None
    # EA field for d16(An) is mode 5, reg N -> low 6 bits = 0b101_NNN
    ea = 0x28 | a.reg
    hits = collections.defaultdict(list)
    for o in range(0, len(d) - 4, 2):
        w = struct.unpack_from(">H", d, o)[0]
        if (w & 0x3F) != ea:
            continue
        disp = struct.unpack_from(">H", d, o + 2)[0]
        if disp & 1 or disp >= 0x200:
            continue
        name = REG.get(disp, "$%03X" % disp)
        if want and name not in want:
            continue
        hits[name].append(o)

    tot = sum(len(v) for v in hits.values())
    print("%s : %d candidate d16(a%d) chip accesses in %d registers"
          % (os.path.basename(a.file), tot, a.reg, len(hits)))
    for name in sorted(hits, key=lambda n: -len(hits[n])):
        offs = hits[name]
        s = " ".join("0x%06x" % x for x in offs[:a.limit or 8])
        more = "" if len(offs) <= (a.limit or 8) else " +%d more" % (len(offs) - (a.limit or 8))
        print("  %-10s x%-4d %s%s" % (name, len(offs), s, more))


if __name__ == "__main__":
    main()
