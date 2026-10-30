#!/usr/bin/env python3
"""Read a run of `bra.w` as a jump table and count how much of it is real.

The Superfrog engine dispatches with

    adda.l (a1)+,a2          ; step a2 to the next record
    move.w (a2),d0           ; read the record's first word
    andi.w #$3f,d0           ; low six bits select a handler
    add.w  d0,d0 / add.w d0,d0
    jsr    (a3,d0.w)         ; a3 is a run of bra.w, 4 bytes per entry

so each table is 64 entries of 4 bytes.  What matters is not that the table
exists but how many of its 64 slots are distinct: a slot that branches to the
same address as most of the others is an unused opcode pointing at a common
default, and the count of distinct targets is the real size of the vocabulary.

Usage: python3 tools/jumptable.py <file> <hex-offset> [count] [--entries N]
"""
import sys, struct
from collections import Counter


def main():
    f = sys.argv[1]
    off = int(sys.argv[2], 16)
    n = int(sys.argv[3]) if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else 64
    d = open(f, "rb").read()
    targets = []
    for i in range(n):
        o = off + i * 4
        op = struct.unpack_from(">H", d, o)[0]
        disp = struct.unpack_from(">h", d, o + 2)[0]
        if op != 0x6000:
            targets.append(None)
            continue
        targets.append(o + 2 + disp)
    c = Counter(t for t in targets if t is not None)
    bad = sum(1 for t in targets if t is None)
    print("table at 0x%06x, %d entries of 4 bytes" % (off, n))
    print("  entries that are not `bra.w`: %d" % bad)
    print("  distinct branch targets     : %d" % len(c))
    if c:
        top, topn = c.most_common(1)[0]
        print("  most common target          : 0x%06x, used by %d of %d slots (%.0f %%)" %
              (top, topn, n, 100.0 * topn / n))
        print("  slots pointing somewhere else: %d" % (n - topn - bad))
    print()
    print("  slot -> target")
    for i, t in enumerate(targets):
        mark = ""
        if c and t == c.most_common(1)[0][0]:
            mark = "  (default)"
        print("    %3d ($%02X) -> %s%s" %
              (i, i, ("0x%06x" % t) if t is not None else "NOT a bra.w", mark))


main()
