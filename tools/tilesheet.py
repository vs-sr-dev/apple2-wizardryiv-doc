#!/usr/bin/env python3
"""tilesheet.py -- render a bank of 16x16, 4-bitplane Amiga tiles as a sheet,
and render each bitplane separately in monochrome.

The geometry is not stored anywhere on this disc.  It is *derived*, and two
independent measurements agree on it, which is why it is quoted rather than
guessed:

  1. every unpacked graphics piece on the disc -- all eighteen of them, the six
     level `.PAK` streams, the four streams embedded in `alfred`, `frontend.pak`
     and the seven `.unpack` files -- has a length that is an exact multiple of
     128 bytes.  128 = 16 x 16 pixels / 8 bits x 4 planes.  Dividing instead by
     160 (five planes) leaves a remainder on five of the eighteen, so four
     planes is the only count consistent with all of them;
  2. for each of the seven `<name>.unpack` / `<name>.map` pairs, the largest
     tile index appearing in the 1,024-byte map is exactly (length / 128) - 1.
     Seven out of seven.  A tileset of N tiles indexed 0..N-1 by a 32x32 map.

The checklist asks for planes to be rendered one at a time in monochrome before
any conclusion about geometry is drawn, because six coherent images and two
solid stencils is a different diagnosis from six streams of noise.

Usage:
  tilesheet.py FILE OUT.png [--across 16] [--scale 2]
  tilesheet.py FILE OUT_prefix --planes    (one PNG per bitplane)
"""
import sys, argparse, zlib, struct

TW, TH, PLANES = 16, 16, 4
TILE = TW * TH // 8 * PLANES        # 128


def png(path, w, h, rgb):
    raw = b''.join(b'\x00' + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))
    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    out = b'\x89PNG\r\n\x1a\n'
    out += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    out += chunk(b'IDAT', zlib.compress(raw, 9))
    out += chunk(b'IEND', b'')
    open(path, 'wb').write(out)


def plane_row_offset(base, p, y, layout):
    """Byte offset of plane `p`, row `y` of the tile starting at `base`.

    contig  plane 0's 32 bytes, then plane 1's, ...  (plane-contiguous)
    inter   row 0 planes 0..3, row 1 planes 0..3, ... (row-interleaved)

    Both cost exactly 128 bytes per tile, so the length evidence cannot choose
    between them; the render can.
    """
    if layout == 'contig':
        return base + p * (TH * TW // 8) + y * (TW // 8)
    return base + y * (TW // 8) * PLANES + p * (TW // 8)


def decode_tile(blob, ti, layout='inter'):
    """Return a 16x16 array of 0..15 colour indices for tile `ti`."""
    base = ti * TILE
    px = [[0] * TW for _ in range(TH)]
    for p in range(PLANES):
        for y in range(TH):
            o = plane_row_offset(base, p, y, layout)
            if o + 1 >= len(blob):
                continue
            word = (blob[o] << 8) | blob[o + 1]
            for x in range(TW):
                if word & (0x8000 >> x):
                    px[y][x] |= (1 << p)
    return px


# a neutral 16-entry ramp: the palette is not stored with the tiles, and this
# renders index values, not colours.  Any claim about actual colours would need
# a copper list, and this disc stores none.
RAMP = [(i * 17, i * 17, i * 17) for i in range(16)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file')
    ap.add_argument('out')
    ap.add_argument('--across', type=int, default=16)
    ap.add_argument('--scale', type=int, default=2)
    ap.add_argument('--planes', action='store_true')
    ap.add_argument('--layout', choices=('inter', 'contig'), default='inter',
                    help='tile-internal bitplane layout; printed either way')
    a = ap.parse_args()

    blob = open(a.file, 'rb').read()
    n = len(blob) // TILE
    if len(blob) % TILE:
        print("WARNING: %d bytes is not a whole number of 128-byte tiles "
              "(remainder %d)" % (len(blob), len(blob) % TILE))
    print("%s: %d bytes = %d tiles of 16x16x4, layout=%s"
          % (a.file, len(blob), n, a.layout))

    if a.planes:
        for p in range(PLANES):
            cols = a.across
            rows = (n + cols - 1) // cols
            W, H = cols * TW, rows * TH
            buf = bytearray(W * H * 3)
            for ti in range(n):
                gx, gy = (ti % cols) * TW, (ti // cols) * TH
                base = ti * TILE
                for y in range(TH):
                    o = plane_row_offset(base, p, y, a.layout)
                    if o + 1 >= len(blob):
                        continue
                    word = (blob[o] << 8) | blob[o + 1]
                    for x in range(TW):
                        v = 255 if (word & (0x8000 >> x)) else 0
                        i = ((gy + y) * W + gx + x) * 3
                        buf[i] = buf[i + 1] = buf[i + 2] = v
            png("%s-plane%d.png" % (a.out, p), W, H, bytes(buf))
            print("  wrote %s-plane%d.png  (%dx%d)" % (a.out, p, W, H))
        return

    cols = a.across
    rows = (n + cols - 1) // cols
    S = a.scale
    W, H = cols * TW * S, rows * TH * S
    buf = bytearray(W * H * 3)
    for ti in range(n):
        px = decode_tile(blob, ti, a.layout)
        gx, gy = (ti % cols) * TW * S, (ti // cols) * TH * S
        for y in range(TH):
            for x in range(TW):
                r, g, b = RAMP[px[y][x]]
                for dy in range(S):
                    for dx in range(S):
                        i = ((gy + y * S + dy) * W + gx + x * S + dx) * 3
                        buf[i], buf[i + 1], buf[i + 2] = r, g, b
    png(a.out, W, H, bytes(buf))
    print("  wrote %s  (%dx%d, %d tiles across)" % (a.out, W, H, cols))


if __name__ == '__main__':
    main()
