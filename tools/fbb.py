"""Render the planar art in cdraw/.

Three families, all 6 bitplanes (64 colours) and all big-endian planar:

    blockNN.fbb64    96000 = 320 x 400, interleaved   -- tile bank
                     86016 = 448 x 256, separated     -- block04, title screen
    objectsNN.fbb64 103392 = 384 x 359, interleaved   -- sprite sheet
    mplxNN.dat       varies, 288 wide, interleaved    -- parallax layers
    transparencyNN.fbb        352 wide, interleaved

The matching .pal is a raw run of Amiga 12-bit $0RGB words: 256 bytes
(128 entries) beside a block, 64 bytes (32 entries) beside an mplx.
"""
import argparse, struct
from PIL import Image


def palette(path, n):
    d = open(path, 'rb').read()
    out = []
    for i in range(min(n, len(d) // 2)):
        w = struct.unpack_from('>H', d, i * 2)[0]
        out.append(((w >> 8 & 15) * 17, (w >> 4 & 15) * 17, (w & 15) * 17))
    return out


def render(d, off, w, planes, h, interleaved=True, pal=None):
    bpr = w // 8
    img = Image.new('P', (w, h))
    px = img.load()
    for y in range(h):
        for p in range(planes):
            base = off + ((y * planes + p) if interleaved else (p * h + y)) * bpr
            if base + bpr > len(d):
                break
            row, bit = d[base:base+bpr], 1 << p
            for xb, byte in enumerate(row):
                if not byte:
                    continue
                for k in range(8):
                    if byte >> (7 - k) & 1:
                        px[xb*8 + k, y] |= bit
    flat = []
    for c in (pal or [])[:256]:
        flat += list(c)
    flat += [0] * (768 - len(flat))
    img.putpalette(flat)
    return img


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('file'); ap.add_argument('out')
    ap.add_argument('--width', type=int, default=320)
    ap.add_argument('--planes', type=int, default=6)
    ap.add_argument('--height', type=int, default=0)
    ap.add_argument('--off', type=lambda s: int(s, 0), default=0)
    ap.add_argument('--pal'); ap.add_argument('--separate', action='store_true')
    a = ap.parse_args()
    d = open(a.file, 'rb').read()
    h = a.height or (len(d) - a.off) // (a.width // 8 * a.planes)
    pal = palette(a.pal, 1 << a.planes) if a.pal else None
    render(d, a.off, a.width, a.planes, h, not a.separate, pal).save(a.out)
    print('%s  %dx%d %d planes %s -> %s'
          % (a.file, a.width, h, a.planes,
             'separated' if a.separate else 'interleaved', a.out))
