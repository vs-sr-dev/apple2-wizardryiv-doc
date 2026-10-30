#!/usr/bin/env python3
"""Reconstruct AGA palette state from a copper list.

On this disc every colour reaches the chips through the copper and never
through `LoadRGB4`/`LoadRGB32`, and the palette is 24-bit: each entry is
written twice, once with `BPLCON3` LOCT clear (the high nibble of each gun)
and once with LOCT set (the low nibble).  `BPLCON3` bits 15-13 select which
bank of 32 the `COLOR00..COLOR31` registers address.

The tool walks the list, tracks BANK and LOCT, and prints the palette as it
stands when it reaches a chosen instruction offset (`--at`), so the palette
in force for a given `BPLCON0` can be quoted exactly.

    python3 tools/copperpal.py FILE START [--at OFFSET]
"""
import sys, argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("start", type=lambda s: int(s, 0))
    ap.add_argument("--at", type=lambda s: int(s, 0))
    a = ap.parse_args()
    d = open(a.file, 'rb').read()

    def w(o):
        return int.from_bytes(d[o:o + 2], 'big')

    pal = {}          # absolute index -> [r,g,b] 8-bit
    bank, loct = 0, 0
    o = a.start
    stop = a.at if a.at else None
    while o + 4 <= len(d):
        x, y = w(o), w(o + 2)
        if stop is not None and o >= stop:
            break
        if x & 1:
            if x == 0xFFFF and y == 0xFFFE:
                break
        elif x == 0x106:
            bank, loct = (y >> 13) & 7, (y >> 9) & 1
        elif 0x180 <= x <= 0x1BE:
            idx = bank * 32 + (x - 0x180) // 2
            r, g, b = (y >> 8) & 0xf, (y >> 4) & 0xf, y & 0xf
            cur = pal.setdefault(idx, [0, 0, 0])
            if loct:
                cur[0] = (cur[0] & 0xf0) | r
                cur[1] = (cur[1] & 0xf0) | g
                cur[2] = (cur[2] & 0xf0) | b
            else:
                cur[0] = (cur[0] & 0x0f) | (r << 4)
                cur[1] = (cur[1] & 0x0f) | (g << 4)
                cur[2] = (cur[2] & 0x0f) | (b << 4)
        o += 4
    nz = {k: v for k, v in pal.items() if any(v)}
    print("# %s from 0x%06x%s" % (a.file, a.start,
                                  " to 0x%06x" % a.at if a.at else " (whole list)"))
    print("# %d colour indices touched, %d non-black" % (len(pal), len(nz)))
    for k in sorted(pal):
        r, g, b = pal[k]
        print("  %3d  #%02x%02x%02x" % (k, r, g, b))


main()
