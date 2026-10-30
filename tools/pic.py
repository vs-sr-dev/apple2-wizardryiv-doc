#!/usr/bin/env python3
"""Decode and render the `pics/` screens.

Container (after CrunchMania):

    0   UWORD  width in pixels
    2   UWORD  height in rows
    4   UWORD  bitplanes
    6   UWORD  0
    8   ULONG  unpacked bitmap size = width/8 * height * planes
    12  IFF ByteRun1 (PackBits) stream

The bitmap is interleaved planar: `planes` consecutive rows of width/8 bytes
per display line.

    python tools/pic.py <pic> [<pal>] -o out.png [--separated]
"""
import sys, struct


def unrle(b):
    out = bytearray()
    i = 0
    while i < len(b):
        n = b[i]; i += 1
        if n < 0x80:
            out += b[i:i + n + 1]; i += n + 1
        elif n > 0x80:
            out += bytes([b[i]]) * (257 - n); i += 1
    return bytes(out)


def decode(path):
    b = open(path, 'rb').read()
    w, h, pl, _, sz = struct.unpack_from('>HHHHI', b, 0)
    bm = unrle(b[12:])
    if len(bm) != sz:
        raise ValueError("ByteRun1 gave %d bytes, header declares %d" % (len(bm), sz))
    return w, h, pl, bm


def to_indices(w, h, pl, bm, separated=False):
    bpr = w // 8
    px = [[0] * w for _ in range(h)]
    for y in range(h):
        for p in range(pl):
            off = (p * h + y) * bpr if separated else (y * pl + p) * bpr
            row = bm[off:off + bpr]
            for xb in range(bpr):
                v = row[xb]
                for bit in range(8):
                    if v & (0x80 >> bit):
                        px[y][xb * 8 + bit] |= 1 << p
    return px


def load_pal(path):
    """A .pal file is 128 entries of two big-endian words: the AGA LOCT pair.
    The first word carries the high nibble of each gun, the second the low."""
    pb = open(path, 'rb').read()
    n = len(pb) // 4
    pal = [(0, 0, 0)] * 256
    for i in range(n):
        hi, lo = struct.unpack_from('>HH', pb, i * 4)
        pal[i] = ((((hi >> 8) & 15) << 4) | ((lo >> 8) & 15),
                  (((hi >> 4) & 15) << 4) | ((lo >> 4) & 15),
                  ((hi & 15) << 4) | (lo & 15))
    return pal


def main():
    args = [a for a in sys.argv[1:]]
    out = None; sep = False
    if '-o' in args:
        i = args.index('-o'); out = args[i + 1]; del args[i:i + 2]
    if '--separated' in args:
        sep = True; args.remove('--separated')
    w, h, pl, bm = decode(args[0])
    sys.stderr.write("%dx%d, %d planes, %d bytes\n" % (w, h, pl, len(bm)))
    pal = load_pal(args[1]) if len(args) > 1 else [(0, 0, 0)] * 256
    px = to_indices(w, h, pl, bm, sep)
    from PIL import Image
    im = Image.new('RGB', (w, h))
    im.putdata([pal[px[y][x]] for y in range(h) for x in range(w)])
    im.save(out or 'out.png')


if __name__ == '__main__':
    main()
