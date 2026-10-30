#!/usr/bin/env python3
"""Find and score Amiga palettes in a tree.

A palette here is a run of big-endian words whose top nibble is zero -- the
`$0RGB` form `LoadRGB4` and a copper `MOVE COLORnn` both take.  For each run of
at least 16 such words this reports the length, and applies the two tests
section 7 of the platform notes asks for:

  * **precision** -- does any gun need more than four bits?  (It cannot, in a
    12-bit word; the test matters when the palette is stored as 8-bit triples,
    which nothing here is, so this reports the *count* instead.)
  * **Extra-Half-Brite** -- for a 64-entry run, are entries 32..63 entries
    0..31 at half brightness?  32 of 32 means the display is ECS EHB and not
    an AGA 64-colour palette.

    python tools/palettes.py <path> [<path> ...]
"""
import sys, os, struct


def half(w):
    return ((w >> 8 & 15) // 2) << 8 | ((w >> 4 & 15) // 2) << 4 | (w & 15) // 2


def runs(d, minlen=16):
    out = []
    i = 0
    n = len(d) // 2
    while i < n:
        j = i
        while j < n and (d[2 * j] & 0xF0) == 0:
            j += 1
        if j - i >= minlen:
            out.append((i * 2, j - i))
        i = max(j + 1, i + 1)
    return out


def main():
    for p in sys.argv[1:]:
        files = []
        if os.path.isdir(p):
            for dp, dn, fn in os.walk(p):
                dn.sort()
                for f in sorted(fn):
                    files.append(os.path.join(dp, f))
        else:
            files = [p]
        for f in files:
            d = open(f, 'rb').read()
            for off, ln in runs(d):
                w = [struct.unpack_from('>H', d, off + 2 * k)[0] for k in range(ln)]
                if len(set(w)) < 4:
                    continue           # a run of zeros is not a palette
                note = ''
                if ln >= 64:
                    ehb = sum(1 for k in range(32) if w[32 + k] == half(w[k]))
                    note = 'EHB %d/32' % ehb
                print("%-34s off %6d  %3d entries  distinct %3d  %s" %
                      (os.path.basename(f), off, ln, len(set(w)), note))


if __name__ == '__main__':
    main()
