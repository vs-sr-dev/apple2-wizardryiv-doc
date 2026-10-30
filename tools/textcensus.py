#!/usr/bin/env python3
"""How much of this disc is prose, against which denominator, and in what encoding.

"Prose" is defined here and the definition is a defensible floor, not a
maximum: a printable run of at least MIN bytes that contains a space, a
lowercase letter, and at least two words.  Anything looser counts opcode
soup; anything tighter loses menu labels.

Two denominators are reported because they differ by a large factor on a
compressed disc and quoting one without saying which is meaningless:

  on disc    bytes in the ISO 9660 volume
  resident   bytes after every container is unpacked

The encoding census counts bytes by range so that "7-bit ASCII" is a
measurement rather than an assumption.

Usage: python3 tools/textcensus.py <dir> [--min N] [--label NAME] [--max N]
"""
import os, sys, re
from collections import Counter

MIN = 12


def prose_runs(d, mn):
    out = []
    cur = bytearray()
    start = 0
    for i, b in enumerate(d):
        if 32 <= b < 127 or b in (9, 10, 13):
            if not cur:
                start = i
            cur.append(b)
        else:
            if len(cur) >= mn:
                out.append((start, bytes(cur)))
            cur = bytearray()
    if len(cur) >= mn:
        out.append((start, bytes(cur)))
    keep = []
    for off, b in out:
        s = b.decode("latin1")
        if " " not in s:
            continue
        if not any(c.islower() for c in s):
            continue
        if len([w for w in s.split() if len(w) > 1]) < 2:
            continue
        keep.append((off, s))
    return keep


def main():
    root = sys.argv[1]
    mn = int(sys.argv[sys.argv.index("--min") + 1]) if "--min" in sys.argv else MIN
    mx = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 0
    label = sys.argv[sys.argv.index("--label") + 1] if "--label" in sys.argv else root

    total = 0
    prose = 0
    byfile = []
    enc = Counter()
    for dp, dn, fn in os.walk(root):
        for f in sorted(fn):
            p = os.path.join(dp, f)
            d = open(p, "rb").read()
            rel = p[len(root):].replace(os.sep, "/")
            total += len(d)
            for b in d:
                if b < 0x20:
                    enc["ctrl <0x20"] += 1
                elif b < 0x80:
                    enc["ASCII 0x20-0x7E"] += 1
                elif b < 0xA0:
                    enc["0x80-0x9F"] += 1
                else:
                    enc["0xA0-0xFF"] += 1
            r = prose_runs(d, mn)
            n = sum(len(s) for _, s in r)
            prose += n
            if n:
                byfile.append((rel, len(d), n, len(r)))

    print("=== %s ===" % label)
    print("denominator (all bytes)  : %d" % total)
    print("prose bytes (min %d)      : %d  = %.3f %% of the denominator" %
          (mn, prose, 100.0 * prose / total))
    print("runs                     : %d" % sum(r[3] for r in byfile))
    print()
    print("=== byte-value census (the encoding question, measured) ===")
    for k in ("ctrl <0x20", "ASCII 0x20-0x7E", "0x80-0x9F", "0xA0-0xFF"):
        print("  %-18s %12d  %6.3f %%" % (k, enc[k], 100.0 * enc[k] / total))
    print()
    print("=== files by prose bytes ===")
    print("%-56s %10s %9s %6s %6s" % ("file", "bytes", "prose", "runs", "share"))
    for rel, n, pr, runs in sorted(byfile, key=lambda r: -r[2])[:30]:
        print("%-56s %10d %9d %6d %5.1f%%" % (rel, n, pr, runs, 100.0 * pr / n))
    print()
    print("  files with any prose: %d" % len(byfile))
    if mx:
        print()
        print("=== longest runs, truncated to %d chars ===" % mx)
        allr = []
        for dp, dn, fn in os.walk(root):
            for f in sorted(fn):
                p = os.path.join(dp, f)
                d = open(p, "rb").read()
                rel = p[len(root):].replace(os.sep, "/")
                for off, s in prose_runs(d, mn):
                    allr.append((len(s), rel, off, s))
        allr.sort(reverse=True)
        for ln, rel, off, s in allr[:40]:
            print("  %-40s 0x%06x %5d  %s" % (rel, off, ln, s[:mx].replace("\n", " ")))


main()
