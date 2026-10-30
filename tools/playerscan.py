#!/usr/bin/env python3
"""Find and validate 'The Player' packed modules.

Superfrog's music is not a ProTracker module and not an OctaMED module, so a
scan for `M.K.` / `MMD0` finds nothing.  It is stored in the format of the
replayer *The Player*, whose four-byte magic is the version string itself:

    'P41A'   The Player 4.1A     (Superfrog, Arcade Pool)
    'P40B'   The Player 4.0B     (Super Stardust)
    'P50A' 'P60A' 'P61A'         later versions, checked for and not present

Header, read from the files themselves:

    +0  char[4]  magic
    +4  UBYTE    number of patterns
    +5  UBYTE    highest sample used
    +6  UBYTE    song length in positions
    +7  UBYTE    0
    +8  ULONG    offset of the sample-descriptor table
    +12 ULONG    offset of the pattern-offset table
    ...

The validation used here is deliberately weak and structural: the two header
offsets must land inside the file and be non-zero, and the byte at +7 must be
zero.  It is enough to separate a real module from a coincidental longword.

Usage: python3 tools/playerscan.py <dir>...
"""
import os, sys, struct
from collections import Counter

MAGICS = [b"P41A", b"P40A", b"P40B", b"P50A", b"P60A", b"P61A", b"P4.1", b"PLR!"]


def check(d, off):
    if off + 16 > len(d):
        return None
    npat, nsamp, songlen, zero = d[off + 4], d[off + 5], d[off + 6], d[off + 7]
    if zero != 0:
        return None
    if not (1 <= songlen <= 128):
        return None
    if not (1 <= npat <= 128):
        return None
    # +5 is not "samples used": L3MU/L5MU/L6MU carry 32, 36 and 33 here, so the
    # field is wider than the 31 ProTracker slots and the bound is loosened to
    # a sanity check rather than a format claim.
    if not (1 <= nsamp <= 64):
        return None
    a = struct.unpack_from(">I", d, off + 8)[0]
    b = struct.unpack_from(">I", d, off + 12)[0]
    if a == 0 or b == 0:
        return None
    if off + a > len(d) or off + b > len(d):
        return None
    return dict(patterns=npat, samples=nsamp, songlen=songlen, t1=a, t2=b)


def main():
    rows = []
    raw = Counter()
    for root in sys.argv[1:]:
        for dp, dn, fn in os.walk(root):
            for f in sorted(fn):
                p = os.path.join(dp, f)
                d = open(p, "rb").read()
                rel = p[len(root):].replace(os.sep, "/")
                for i in range(len(d) - 4):
                    m = bytes(d[i:i + 4])
                    if m in MAGICS:
                        raw[m] += 1
                        r = check(d, i)
                        if r:
                            rows.append((rel, len(d), i, m.decode("latin1"), r))
    print("raw magic occurrences:")
    for m, v in sorted(raw.items()):
        print("  %-6s %4d" % (m.decode("latin1"), v))
    print()
    print("=== validated modules: %d ===" % len(rows))
    print("%-52s %9s %8s %-6s %5s %5s %8s" %
          ("file", "size", "offset", "magic", "pat", "smp", "songlen"))
    for rel, n, off, m, r in rows:
        print("%-52s %9d %8d %-6s %5d %5d %8d" %
              (rel, n, off, m, r["patterns"], r["samples"], r["songlen"]))
    print()
    c = Counter(r[3] for r in rows)
    for m, v in c.most_common():
        print("  %-6s %3d modules" % (m, v))
    print("  total bytes in files that are a module at offset 0: %d" %
          sum(n for rel, n, off, m, r in rows if off == 0))


main()
