"""Read the `ImgA` sprite containers -- `MainSp.img`, `backpack.img`,
`taxi.img`, `3dView.img`.

    'ImgA'
    UWORD  image count
    ULONG  offset of each image

and each image is

    UWORD  0
    UWORD  width in pixels
    UWORD  height in rows
    UWORD  flags -- the high byte is the number of plane slots (6 here)
    UWORD  total size, header included
    UWORD  plane offset x N     -- relative to the image header

A plane offset of **zero** means the plane is all zeros and is not stored;
two slots holding the same offset share one buffer.  So the size field
counts only the distinct non-zero planes, and the format gets a free 2:1 on
flat artwork without any codec at all.

    img.py FILE                 list every image
    img.py FILE N OUT.png       render image N (grey ramp, no palette on disc)
"""
import sys, struct


def images(d):
    assert d[:4] == b'ImgA', 'not an ImgA container'
    n = struct.unpack_from('>H', d, 4)[0]
    for j, o in enumerate(struct.unpack_from('>%dI' % n, d, 6)):
        _, w, h, flags, total = struct.unpack_from('>5H', d, o)
        np = flags >> 8
        po = list(struct.unpack_from('>%dH' % np, d, o + 10)) if np else []
        yield j, o, w, h, flags, total, po


def render(d, o, w, h, po):
    bpr = (w + 15) // 16 * 2
    px = bytearray(w * h)
    for p, off in enumerate(po):
        if not off:
            continue
        for y in range(h):
            row = o + off + y * bpr
            for xb in range(bpr):
                b = d[row + xb]
                if not b:
                    continue
                for k in range(8):
                    if b & (0x80 >> k):
                        x = xb * 8 + k
                        if x < w:
                            px[y * w + x] |= 1 << p
    return px


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    if len(sys.argv) > 3:
        idx = int(sys.argv[2])
        from PIL import Image
        for j, o, w, h, flags, total, po in images(d):
            if j != idx:
                continue
            px = render(d, o, w, h, po)
            im = Image.frombytes('P', (w, h), bytes(px))
            n = 1 << max(1, len(po))
            flat = []
            for i in range(256):
                v = min(255, i * 255 // max(1, n - 1))
                flat += [v, v, v]
            im.putpalette(flat)
            im.convert('RGB').save(sys.argv[3])
            print('%s  %dx%d' % (sys.argv[3], w, h))
        sys.exit()
    tot = 0
    for j, o, w, h, flags, total, po in images(d):
        bpr = (w + 15) // 16 * 2
        stored = len({x for x in po if x})
        print('%4d @0x%-6X %4dx%-4d flags=%04X size=%-6d planes stored %d/%d '
              '%s' % (j, o, w, h, flags, total, stored, len(po),
                      ' '.join('%d' % x for x in po)))
        tot += bpr * h * stored
    print('%d images, %d bytes of plane data' % (j + 1, tot))
