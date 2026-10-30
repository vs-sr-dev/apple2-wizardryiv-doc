#!/usr/bin/env python3
"""Render Universe's two picture formats.

Nothing on the disc stores the geometry, the plane count or the palette
position -- they come from the copper list in `copper.prg` (320 x 200, six
bitplanes, `BPLCON2 = $001B` with `KILLEHB` clear, 32 colour registers) and
from the two blob sizes that recur across the whole volume:

    48,064 bytes = 6 planes x 8,000 + 64      a picture
    64,064 bytes = 8 planes x 8,000 + 64      a picture and two 1-bit masks

Both are **separated** planar -- each plane is one contiguous 8,000-byte run,
not interleaved by row -- and both carry the palette in the last 64 bytes as
32 big-endian `$0RGB` words, four bits per gun.

The one thing that has to be right or the picture comes out as noise is
**Extra-Half-Brite**: six planes give pixel values 0..63 against a 32-entry
palette, and values 32..63 are the corresponding colour at half brightness.
A renderer with 32 entries and no EHB draws the top half of every image black
or wrapped, which looks exactly like a wrong stride and is not one.

    python3 tools/picture.py <blob> <out.png> [--masks] [--no-ehb]
"""
import sys, argparse
from PIL import Image

W, H, PLANE = 320, 200, 8000


def palette(b):
    pal = []
    for i in range(32):
        v = int.from_bytes(b[-64 + 2 * i:-64 + 2 * i + 2], 'big')
        pal.append((((v >> 8) & 15) * 17, ((v >> 4) & 15) * 17, (v & 15) * 17))
    # Extra-Half-Brite: 32..63 are the same colours at half brightness
    return pal + [(r // 2, g // 2, bl // 2) for r, g, bl in pal]


def planes(b, n):
    px = [[0] * W for _ in range(H)]
    for m in range(n):
        base = m * PLANE
        for y in range(H):
            row = px[y]
            o = base + y * (W // 8)
            for xb in range(W // 8):
                v = b[o + xb]
                if not v:
                    continue
                x = xb * 8
                for i in range(8):
                    if v & (0x80 >> i):
                        row[x + i] |= 1 << m
    return px


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('blob')
    ap.add_argument('out')
    ap.add_argument('--masks', action='store_true',
                    help='also write <out>.mask0.png / .mask1.png (64,064 only)')
    ap.add_argument('--no-ehb', action='store_true')
    args = ap.parse_args()

    b = open(args.blob, 'rb').read()
    if len(b) not in (48064, 64064):
        print('warning: %d bytes, not one of the two known picture sizes'
              % len(b), file=sys.stderr)
    pal = palette(b)
    if args.no_ehb:
        pal = pal[:32] + [(0, 0, 0)] * 32
    px = planes(b, 6)
    im = Image.new('RGB', (W, H))
    im.putdata([pal[v] for row in px for v in row])
    im.save(args.out)
    print('%s  %dx%d  6 planes + EHB  -> %s' % (args.blob, W, H, args.out))

    if args.masks and len(b) == 64064:
        for k in (6, 7):
            m = Image.new('1', (W, H))
            d = []
            for y in range(H):
                o = k * PLANE + y * (W // 8)
                for xb in range(W // 8):
                    v = b[o + xb]
                    d += [(v >> (7 - i)) & 1 for i in range(8)]
            m.putdata(d)
            p = args.out.replace('.png', '.mask%d.png' % (k - 6))
            m.save(p)
            print('  mask plane %d -> %s' % (k - 6, p))


if __name__ == '__main__':
    main()
