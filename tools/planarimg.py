#!/usr/bin/env python3
"""Render an Amiga planar image out of a file, given the 12-byte header this
disc uses:

    UWORD width, height, planes, x, y, size      size == width/8 * height * planes

Layout is INTERLEAVED (plane 0 row 0, plane 1 row 0, ... plane n-1 row 0,
plane 0 row 1, ...), which is what this title's copper modulos say.

    python tools/planarimg.py <file> <header offset> <out.png> [--pal OFF] [--sep]
    python tools/planarimg.py <file> --scan            list headers

--pal OFF reads the palette as big-endian $0RGB words at OFF; --pal24 OFF reads
it as this disc's LOCT pairs (two words per entry, high nibbles then low).
Without a palette a grey ramp is used.
"""
import sys, struct

def be16(d,o): return struct.unpack_from('>H',d,o)[0]

def render(d, hdr, palette=None, sep=False):
    w,h,p,x,y,sz = struct.unpack_from('>6H', d, hdr)
    bpr = w//8
    body = d[hdr+12:hdr+12+sz]
    px = [[0]*w for _ in range(h)]
    for row in range(h):
        for pl in range(p):
            if sep: base = pl*bpr*h + row*bpr
            else:   base = (row*p + pl)*bpr
            for bx in range(bpr):
                if base+bx >= len(body): continue
                b = body[base+bx]
                for bit in range(8):
                    if b & (0x80 >> bit):
                        px[row][bx*8+bit] |= (1 << pl)
    return w,h,p,px

def writepng(path, w, h, px, pal):
    import zlib
    raw = bytearray()
    for row in px:
        raw.append(0)
        for v in row:
            raw += bytes(pal[v] if v < len(pal) else (255,0,255))
    def chunk(t, data):
        c = t + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += chunk(b'IEND', b'')
    open(path,'wb').write(png)

def main():
    d = open(sys.argv[1],'rb').read()
    if '--scan' in sys.argv:
        for i in range(0, len(d)-14, 2):
            w,h,p,x,y,sz = struct.unpack_from('>6H', d, i)
            if 8<=w<=640 and 2<=h<=512 and 1<=p<=8 and w%8==0 and sz==(w//8)*h*p and sz>=64:
                print("0x%06x  %dx%d planes=%d size=%d" % (i,w,h,p,sz))
        return
    hdr = int(sys.argv[2],0); out = sys.argv[3]
    n = 1 << struct.unpack_from('>6H',d,hdr)[2]
    pal = [(i*255//max(1,n-1),)*3 for i in range(n)]
    if '--pal' in sys.argv:
        o = int(sys.argv[sys.argv.index('--pal')+1],0)
        pal = []
        for i in range(n):
            v = be16(d,o+2*i)
            pal.append((((v>>8)&15)*17, ((v>>4)&15)*17, (v&15)*17))
    if '--pal24' in sys.argv:
        o = int(sys.argv[sys.argv.index('--pal24')+1],0)
        pal = []
        for i in range(n):
            a = be16(d,o+4*i); b = be16(d,o+4*i+2)
            pal.append(((((a>>8)&15)<<4)|((b>>8)&15), (((a>>4)&15)<<4)|((b>>4)&15),
                        ((a&15)<<4)|(b&15)))
    w,h,p,px = render(d, hdr, sep='--sep' in sys.argv)
    writepng(out, w, h, px, pal)
    print("wrote %s  %dx%d %d planes" % (out,w,h,p))

main()
