"""Render the OGFX chunk of a level: the object/sprite bank.

Each entry is a 12-byte header -- width, height, a flags long, and the offset
of the mask -- followed by the pixels and then a mask of the same size, both
six bitplanes interleaved by row, like the tiles.
"""
import struct, sys, os
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from lev2 import parse
from render import palette

def frames(b, o):
    n = struct.unpack_from('>H', b, o+8)[0]
    offs = [struct.unpack_from('>I', b, o+10+4*i)[0] for i in range(n)]
    out = []
    for f in offs:
        p = o + f
        w, h = struct.unpack_from('>HH', b, p)
        flags, moff = struct.unpack_from('>II', b, p+4)
        if not (0 < w <= 256 and 0 < h <= 256):
            out.append(None); continue
        bpr = (w + 15)//16*2
        px = bytearray(w*h); msk = bytearray(w*h)
        for y in range(h):
            for pl in range(6):
                ro = p + 12 + (y*6 + pl)*bpr
                mo = p + moff + (y*6 + pl)*bpr
                for xb in range(bpr):
                    v = b[ro+xb] if ro+xb < len(b) else 0
                    m = b[mo+xb] if mo+xb < len(b) else 0
                    for bit in range(8):
                        x = xb*8 + bit
                        if x < w:
                            if v & (0x80 >> bit): px[y*w+x] |= 1 << pl
                            if m & (0x80 >> bit): msk[y*w+x] |= 1 << pl
        out.append((w, h, px, msk))
    return out

def sheet(fr, pal, cols=16, bg=(255, 0, 255)):
    fr = [f for f in fr if f]
    cw = max(f[0] for f in fr); ch = max(f[1] for f in fr)
    rows = (len(fr)+cols-1)//cols
    im = Image.new('RGB', (cols*cw, rows*ch), bg)
    for i, (w, h, px, msk) in enumerate(fr):
        t = Image.new('RGB', (w, h))
        t.putdata([bg if not m else pal[c] for c, m in zip(px, msk)])
        im.paste(t, ((i % cols)*cw, (i//cols)*ch))
    return im

if __name__ == '__main__':
    p = sys.argv[1]; b = open(p, 'rb').read(); h = parse(b)
    pal = palette(b, h['offs'][0])
    fr = frames(b, h['offs'][6])
    stem = os.path.basename(p).split('.')[0]
    sheet(fr, pal).save('_work/%s_objs.png' % stem)
    print('%s: %d object frames -> _work/%s_objs.png' % (stem, len(fr), stem))
