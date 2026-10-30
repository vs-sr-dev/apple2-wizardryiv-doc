#!/usr/bin/env python3
"""Parse the resource directory at the head of a `Cores/*.bin` file.

Each unpacked Core file begins with a four-character world tag and then a
table of big-endian longword offsets into the same file.  The table's length
is not stored: it ends where the first resource begins, so the tool takes the
smallest non-zero offset as the end of the table and checks that the result
divides evenly.

Reported per file: the tag, the number of slots, which slots are **zero**
(an empty record) and which slots **share an offset** with another slot.
Comparing those two sets across the seven worlds is the point -- a slot that
is filled in six worlds and zero in the seventh is a record the engine still
has a place for.

    python3 tools/coredir.py FILE [FILE ...]
"""
import sys, collections


def parse(d):
    tag = d[:4].decode('latin-1')
    offs = []
    i = 4
    first = None
    while True:
        v = int.from_bytes(d[i:i + 4], 'big')
        if v and (first is None or v < first):
            first = v
        if first is not None and i + 4 > first:
            break
        if i > 4096:
            break
        offs.append(v)
        i += 4
    return tag, offs, first


def main():
    allslots = {}
    for p in sys.argv[1:]:
        d = open(p, 'rb').read()
        tag, offs, first = parse(d)
        zero = [k for k, v in enumerate(offs) if v == 0]
        c = collections.Counter(v for v in offs if v)
        dup = {v: [k for k, x in enumerate(offs) if x == v] for v, n in c.items() if n > 1}
        print("### %s  tag=%r  %d bytes  %d slots  (table 4..%d)"
              % (p.split('/')[-1], tag, len(d), len(offs), first))
        print("    zero slots (%d): %s" % (len(zero), zero))
        for v, ks in sorted(dup.items()):
            print("    slots %s all point at 0x%06x" % (ks, v))
        print()
        allslots[tag] = offs
    if len(allslots) > 1:
        n = max(len(v) for v in allslots.values())
        print("### slot occupancy across %d worlds (`.` = zero, `#` = filled)" % len(allslots))
        print("    slot  " + "".join("%-6s" % t for t in allslots))
        for k in range(n):
            row = "".join("  %s   " % ('#' if k < len(v) and v[k] else '.')
                          for v in allslots.values())
            filled = sum(1 for v in allslots.values() if k < len(v) and v[k])
            if 0 < filled < len(allslots):
                row += "   <-- filled in %d of %d" % (filled, len(allslots))
            print("    %4d  %s" % (k, row))


main()
