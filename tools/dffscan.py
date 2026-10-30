#!/usr/bin/env python3
"""Both forms of the custom-chip base load, plus the raw absolute histogram.

Platform notes, section 4: a scan that only looks for `lea $dff000,aN`
(4?f9) counts zero on a program that uses `movea.l #$dff000,aN` (2?7c), and
vice versa.  Run both, always, and put the raw byte histogram of
`00 DF F0 xx` beside them so the two can be reconciled.

    python3 tools/dffscan.py FILE [FILE ...]
"""
import sys, collections

REGNAME = {}
try:
    import importlib.util, os
    _s = importlib.util.spec_from_file_location(
        "regscan", os.path.join(os.path.dirname(os.path.abspath(__file__)), "regscan.py"))
    # regscan runs main() on import, so read its REG table textually instead
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "regscan.py"),
               encoding='utf-8').read()
    import re
    for m in re.finditer(r"0x([0-9A-Fa-f]{3}):'([A-Z0-9]+)'", src):
        REGNAME[int(m.group(1), 16)] = m.group(2)
except Exception:
    pass


def scan(name, d):
    lea = movea = 0
    sites = []
    for i in range(0, len(d) - 6, 2):
        if d[i + 2:i + 6] != b'\x00\xdf\xf0\x00':
            continue
        op = int.from_bytes(d[i:i + 2], 'big')
        if (op & 0xf1ff) == 0x41f9:                 # lea  $dff000,aN
            lea += 1
            sites.append((i, 'lea', (op >> 9) & 7))
        elif (op & 0xf1ff) == 0x207c:               # movea.l #$dff000,aN
            movea += 1
            sites.append((i, 'movea.l', (op >> 9) & 7))
    hist = collections.Counter()
    for i in range(len(d) - 3):
        if d[i:i + 3] == b'\x00\xdf\xf0':
            hist[d[i + 3]] += 1
    print("### %s" % name)
    print("  lea $dff000,aN      (4?f9) : %d" % lea)
    print("  movea.l #$dff000,aN (2?7c) : %d" % movea)
    for off, kind, reg in sites:
        print("      0x%06x  %-8s a%d" % (off, kind, reg))
    print("  raw `00 DF F0 xx` histogram (%d hits, %d distinct 4th bytes):"
          % (sum(hist.values()), len(hist)))
    for b, n in sorted(hist.items()):
        nm = REGNAME.get(b, REGNAME.get(b & 0xfe, ''))
        print("      00 DF F0 %02X  x%-4d %s" % (b, n, nm))
    print()


for p in sys.argv[1:]:
    scan(p, open(p, 'rb').read())
