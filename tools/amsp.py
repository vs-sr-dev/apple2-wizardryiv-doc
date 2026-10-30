"""Walk the `AmSp` sprite banks -- `gamemenu.spr` and the 71 `WallNN.VGM`.

The record layout is not documented anywhere; it is the arithmetic the game
does at hunk 0x25208 of `captiveII`, which rewrites the header in place as it
walks:

    'AmSp'
    UWORD  sprite count
    repeat:
        UWORD  w0     bytes per row = w0*2, minus one if bit 15 of w0 was set
        UWORD  height in rows
        UWORD  plane count
        UWORD  flags  -- negative means one extra plane follows: a mask
        UWORD  (spare; the loader writes the plane count back here)
        BYTE[] plane 0, plane 1, ... , mask
    record length = 10 + planes*planeSize (+planeSize if masked), made even

A file may hold several `AmSp` banks back to back; every `WallNN.VGM` holds
exactly four and the walk lands on the file size to the byte in all 71.

    amsp.py FILE                list every bank and sprite
    amsp.py FILE B N OUT.png    render sprite N of bank B
"""
import sys, struct


def banks(d):
    o = 0
    while o + 6 <= len(d) and d[o:o + 4] == b'AmSp':
        n = struct.unpack_from('>H', d, o + 4)[0]
        p = o + 6
        recs = []
        for _ in range(n):
            w0, h, planes, flags = struct.unpack_from('>4h', d, p)
            bpr = (w0 * 2) & 0xFFFF
            if w0 & 0x8000:
                bpr = (bpr - 1) & 0xFFFF
            psz = (bpr * h) & 0xFFFF
            tot = (psz * planes) & 0xFFFF
            mask = flags < 0
            if mask:
                tot = (tot + psz) & 0xFFFF
            tot = ((tot + 11) & 0xFFFF) & ~1
            recs.append((p, bpr, h, planes, mask, psz, tot))
            p += tot
        yield o, n, p - o, recs
        o = p


def render(d, rec):
    p, bpr, h, planes, mask, psz, tot = rec
    w = bpr * 8
    px = bytearray(w * h)
    for pl in range(planes):
        base = p + 10 + pl * psz
        for y in range(h):
            row = base + y * bpr
            for xb in range(bpr):
                b = d[row + xb]
                if not b:
                    continue
                for k in range(8):
                    if b & (0x80 >> k):
                        px[y * w + xb * 8 + k] |= 1 << pl
    return px, w, h


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    if len(sys.argv) > 4:
        bi, si = int(sys.argv[2]), int(sys.argv[3])
        from PIL import Image
        for i, (o, n, ln, recs) in enumerate(banks(d)):
            if i != bi:
                continue
            px, w, h = render(d, recs[si])
            im = Image.frombytes('P', (w, h), bytes(px))
            nc = 1 << recs[si][3]
            flat = []
            for j in range(256):
                v = min(255, j * 255 // max(1, nc - 1))
                flat += [v, v, v]
            im.putpalette(flat)
            im.convert('RGB').save(sys.argv[4])
            print('%s  %dx%d %d planes%s'
                  % (sys.argv[4], w, h, recs[si][3],
                     ' + mask' if recs[si][4] else ''))
        sys.exit()
    end = 0
    for i, (o, n, ln, recs) in enumerate(banks(d)):
        print('bank %d @%-8d %3d sprites %8d bytes' % (i, o, n, ln))
        for j, r in enumerate(recs):
            print('    %3d  %4dx%-4d %d planes%s  %6d bytes'
                  % (j, r[1] * 8, r[2], r[3], ' +mask' if r[4] else '      ',
                     r[6]))
        end = o + ln
    print('walk ends at %d, file is %d bytes, slack %d'
          % (end, len(d), len(d) - end))
