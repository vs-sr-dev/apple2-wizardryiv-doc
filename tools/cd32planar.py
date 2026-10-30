#!/usr/bin/env python3
"""Render Amiga planar bitmaps -- interleaved or contiguous, indexed or HAM8.

The geometry is never stored with the data on this disc; it comes out of the
copper list and the loader's setup code, so every figure here is passed in on
the command line and the source of each is recorded in `docs/07-graphics.md`.

    python3 tools/planar.py <file> <out.png> --w 640 --h 512 --planes 8 \\
            --interleaved --ham8 --order 2,3,4,5,6,7,0,1 \\
            --pal <file>:<offset>:<count>:rgb24
    python3 tools/planar.py <file> <out.png> --w 320 --h 256 --planes 4 \\
            --offset 0 --pal-rgb12 <file>:<offset>
"""
import sys, argparse
from PIL import Image


def read_planar(d, off, w, h, planes, interleaved, order):
    """Return a list of rows of pixel values."""
    bpr = w // 8
    px = [[0] * w for _ in range(h)]
    for m in range(planes):
        bit = order[m]
        for y in range(h):
            if interleaved:
                base = off + y * bpr * planes + m * bpr
            else:
                base = off + m * bpr * h + y * bpr
            row = px[y]
            for xb in range(bpr):
                b = d[base + xb]
                if not b:
                    continue
                x0 = xb * 8
                for k in range(8):
                    if b & (0x80 >> k):
                        row[x0 + k] |= 1 << bit
    return px


def ham8(px, pal):
    out = []
    for row in px:
        r = g = b = 0
        line = []
        for v in row:
            ctrl = v & 3
            data = v >> 2
            if ctrl == 0:
                r, g, b = pal[data]
            elif ctrl == 1:
                b = (data << 2) | (data >> 4)
            elif ctrl == 2:
                r = (data << 2) | (data >> 4)
            else:
                g = (data << 2) | (data >> 4)
            line.append((r, g, b))
        out.append(line)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("out")
    ap.add_argument("--w", type=int, required=True)
    ap.add_argument("--h", type=int, required=True)
    ap.add_argument("--planes", type=int, required=True)
    ap.add_argument("--offset", type=lambda s: int(s, 0), default=0)
    ap.add_argument("--interleaved", action="store_true")
    ap.add_argument("--ham8", action="store_true")
    ap.add_argument("--order", default=None,
                    help="comma list: destination bit of each memory plane")
    ap.add_argument("--pal-rgb24", default=None, help="FILE:OFFSET:COUNT")
    ap.add_argument("--pal-rgb12", default=None, help="FILE:OFFSET:COUNT")
    ap.add_argument("--scale", type=int, default=1)
    ap.add_argument("--squash", type=int, default=1, help="divide width by N")
    a = ap.parse_args()

    d = open(a.file, 'rb').read()
    order = [int(x) for x in a.order.split(',')] if a.order else list(range(a.planes))
    px = read_planar(d, a.offset, a.w, a.h, a.planes, a.interleaved, order)

    pal = []
    if a.pal_rgb24:
        f, o, n = a.pal_rgb24.split(':')
        pd = open(f, 'rb').read()
        o = int(o, 0)
        pal = [(pd[o + 3 * i], pd[o + 3 * i + 1], pd[o + 3 * i + 2]) for i in range(int(n))]
    elif a.pal_rgb12:
        f, o, n = a.pal_rgb12.split(':')
        pd = open(f, 'rb').read()
        o = int(o, 0)
        for i in range(int(n)):
            v = int.from_bytes(pd[o + 2 * i:o + 2 * i + 2], 'big')
            r = (v >> 8) & 0xf
            g = (v >> 4) & 0xf
            b = v & 0xf
            pal.append((r * 17, g * 17, b * 17))

    if a.ham8:
        rows = ham8(px, pal)
    else:
        if not pal:
            n = 1 << a.planes
            pal = [(i * 255 // (n - 1),) * 3 for i in range(n)]
        rows = [[pal[v % len(pal)] for v in row] for row in px]

    im = Image.new("RGB", (a.w, a.h))
    im.putdata([p for row in rows for p in row])
    if a.squash > 1:
        im = im.resize((a.w // a.squash, a.h), Image.LANCZOS)
    if a.scale > 1:
        im = im.resize((im.width * a.scale, im.height * a.scale), Image.NEAREST)
    im.save(a.out)
    print("%s  %dx%d  %d planes  %s -> %s" %
          (a.file, a.w, a.h, a.planes, "HAM8" if a.ham8 else "indexed", a.out))


if __name__ == "__main__":       # importable: _work/usgstrip.py reuses read_planar
    main()
