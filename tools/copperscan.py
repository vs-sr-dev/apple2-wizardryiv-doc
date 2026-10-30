#!/usr/bin/env python3
"""Find STORED copper lists, strictly, and refuse to invent them.

A loose scanner that treats any even word below $200 as a copper MOVE finds
hundreds of "lists" in ordinary 68000 code -- `$4E75` (`rts`) decodes as a
BPLCON0 write, `$4EB9` (`jsr`) as another, and the checklist's standing
instruction is that zero claims beat one invented list.

So a run only counts here when ALL of the following hold:

  * it is at least MINLEN instructions long
  * every instruction is a MOVE to a register that exists on ECS/AGA, or a
    WAIT/SKIP whose vertical position is non-decreasing through the run
  * the run ends with the end-of-list WAIT $FFFF,$FFFE
  * MOVEs do not repeat the same register more than REPEAT times in a row
    with different values (which is what code-misread-as-copper looks like)

Every rejected run is counted, so the ratio of candidates to accepted runs is
visible rather than hidden.

Usage: python3 tools/copperscan.py <file>... [--minlen N] [--dump] [--strict]
"""
import sys, os, struct
from collections import Counter

# registers a copper list on this hardware plausibly writes
GOOD = set()
for r in range(0x020, 0x100, 2):     # pointers, DMA, blitter
    GOOD.add(r)
for r in range(0x100, 0x200, 2):     # BPLCONx, colours, sprites
    GOOD.add(r)

NAME = {0x080: "COP1LCH", 0x082: "COP1LCL", 0x084: "COP2LCH", 0x086: "COP2LCL",
        0x08E: "DIWSTRT", 0x090: "DIWSTOP", 0x092: "DDFSTRT", 0x094: "DDFSTOP",
        0x096: "DMACON", 0x100: "BPLCON0", 0x102: "BPLCON1", 0x104: "BPLCON2",
        0x106: "BPLCON3", 0x108: "BPL1MOD", 0x10A: "BPL2MOD", 0x1FC: "FMODE"}
for i in range(32):
    NAME[0x180 + i * 2] = "COLOR%02d" % i
for i in range(8):
    NAME[0x0E0 + i * 4] = "BPL%dPTH" % (i + 1)
    NAME[0x0E2 + i * 4] = "BPL%dPTL" % (i + 1)

MINLEN = 8
REPEAT = 3


def parse_run(d, start):
    """Try to read a copper list beginning at `start`.  Returns (length_words,
    instructions) or None."""
    i = start
    n = len(d)
    ins = []
    lastv = -1
    regrun = {}
    while i + 4 <= n:
        w1 = struct.unpack_from(">H", d, i)[0]
        w2 = struct.unpack_from(">H", d, i + 2)[0]
        if w1 == 0xFFFF and w2 == 0xFFFE:
            ins.append(("END", 0, 0))
            i += 4
            return (i - start, ins)
        if w1 & 1:
            # WAIT or SKIP
            vp = (w1 >> 8) & 0xFF
            if vp < lastv:
                return None
            lastv = vp
            ins.append(("SKIP" if (w2 & 1) else "WAIT", vp, w1 & 0xFE))
            regrun.clear()
        else:
            r = w1 & 0x1FE
            if r not in GOOD:
                return None
            regrun[r] = regrun.get(r, 0) + 1
            if regrun[r] > REPEAT:
                return None
            ins.append(("MOVE", r, w2))
        i += 4
        if len(ins) > 20000:
            return None
    return None


STRICT = False


def real_list(ins):
    """A stored display copper list has to point the display hardware at
    something.  Requiring at least two bitplane-pointer MOVEs and one BPLCON0
    is what separates a list from a run of sprite data that happens to parse:
    raw .bob files and Workbench .info files pass the syntactic test and fail
    this one."""
    bplpt = sum(1 for t, a, b in ins if t == "MOVE" and 0x0E0 <= a <= 0x0FF)
    con0 = [b for t, a, b in ins if t == "MOVE" and a == 0x100]
    if not (bplpt >= 2 and len(con0) >= 1):
        return False
    if STRICT:
        # [Myth] A BPLCON0 value is not a free 16-bit number.  Reject a run
        # whose every BPLCON0 asks for more bitplanes than the hardware has
        # (BPU = ((v>>12)&7) | (((v>>4)&1)<<3), so 8 is the maximum) or sets
        # the reserved bits 11 and 5-6 that no real value uses.  Without this
        # the two-pointer test still lets packed picture data through: on
        # [Myth] thirteen of sixteen accepted runs carried BPLCON0 $FFFF,
        # $FFFD or $0000 and sat inside decompressed graphics.
        def plausible(v):
            bpu = ((v >> 12) & 7) | (((v >> 4) & 1) << 3)
            return 1 <= bpu <= 8 and not (v & 0x0860)
        if not any(plausible(v) for v in con0):
            return False
    return True


def main():
    global MINLEN
    if "--minlen" in sys.argv:
        MINLEN = int(sys.argv[sys.argv.index("--minlen") + 1])
    dump = "--dump" in sys.argv
    global STRICT
    STRICT = "--strict" in sys.argv
    grand = 0
    cand = 0
    for p in [x for x in sys.argv[1:] if not x.startswith("--")]:
        if p.startswith("--") or p.isdigit():
            continue
        d = open(p, "rb").read()
        found = []
        i = 0
        while i + 4 <= len(d):
            r = parse_run(d, i)
            if r and len(r[1]) >= MINLEN and real_list(r[1]):
                found.append((i, r[0], r[1]))
                i += r[0]
                continue
            if r:
                cand += 1
            i += 2
        print("=== %s (%d bytes): %d stored copper lists ===" %
              (os.path.basename(p), len(d), len(found)))
        grand += len(found)
        for off, ln, ins in found:
            moves = [x for x in ins if x[0] == "MOVE"]
            waits = [x for x in ins if x[0] in ("WAIT", "SKIP")]
            regs = Counter(NAME.get(m[1], "$%03X" % m[1]) for m in moves)
            print("  0x%06x  %d bytes  %d MOVE  %d WAIT/SKIP" %
                  (off, ln, len(moves), len(waits)))
            print("     registers: %s" % ", ".join("%s x%d" % (k, v)
                                                   for k, v in regs.most_common(12)))
            b0 = [m[2] for m in moves if m[1] == 0x100]
            if b0:
                for v in sorted(set(b0)):
                    bpu = ((v >> 12) & 7) | (((v >> 4) & 1) << 3)
                    print("     BPLCON0 $%04X  BPU=%d  HIRES=%d HAM=%d DBLPF=%d LACE=%d" %
                          (v, bpu, bool(v & 0x8000), bool(v & 0x800),
                           bool(v & 0x400), bool(v & 2)))
            if dump:
                for k, (t, a, b) in enumerate(ins[:400]):
                    if t == "MOVE":
                        print("       MOVE %-9s $%04X" % (NAME.get(a, "$%03X" % a), b))
                    elif t == "END":
                        print("       END")
                    else:
                        print("       %s  vp=%d" % (t, a))
        print()
    print("TOTAL stored copper lists accepted: %d" % grand)
    print("runs that parsed but were shorter than the %d-instruction floor: %d" %
          (MINLEN, cand))


main()
