#!/usr/bin/env python3
"""Decode this disc's in-executable image container and render it.

Header, 12 bytes, big endian:

    UWORD width, height, planes, x, y, size

`size` is the UNPACKED length and equals width/8 * height * planes; the body is
ByteRun1 (the IFF `cmpByteRun1` code): a signed count n, n>=0 copies n+1
literal bytes, n<0 repeats the next byte 1-n times, n==-128 is skipped. The
decode is complete when `size` bytes have been produced, which is the check
that the geometry is right.

    python tools/rleimg.py <file> <header offset> [out.png] [--pal OFF] [--sep]
    python tools/rleimg.py <file> --scan
"""
import sys, struct, zlib

def unrle(d, o, want):
    out = bytearray()
    while len(out) < want and o < len(d):
        n = d[o]; o += 1
        if n < 128:
            out += d[o:o+n+1]; o += n+1
        elif n > 128:
            out += bytes([d[o]]) * (257-n); o += 1
    return bytes(out[:want]), o, len(out)

def deplane(body, w, h, p, sep=False):
    bpr = w//8
    px = [[0]*w for _ in range(h)]
    for row in range(h):
        for pl in range(p):
            base = pl*bpr*h + row*bpr if sep else (row*p+pl)*bpr
            for bx in range(bpr):
                if base+bx >= len(body): continue
                b = body[base+bx]
                for bit in range(8):
                    if b & (0x80>>bit): px[row][bx*8+bit] |= (1<<pl)
    return px

def png(path, w, h, px, pal):
    raw = bytearray()
    for row in px:
        raw.append(0)
        for v in row: raw += bytes(pal[v] if v < len(pal) else (255,0,255))
    def ch(t,dd):
        c=t+dd; return struct.pack('>I',len(dd))+c+struct.pack('>I',zlib.crc32(c)&0xffffffff)
    open(path,'wb').write(b'\x89PNG\r\n\x1a\n'
        + ch(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))
        + ch(b'IDAT',zlib.compress(bytes(raw),9)) + ch(b'IEND',b''))

def main():
    d = open(sys.argv[1],'rb').read()
    if '--scan' in sys.argv:
        for i in range(0,len(d)-14,2):
            w,h,p,x,y,sz = struct.unpack_from('>6H',d,i)
            if 8<=w<=640 and 2<=h<=512 and 1<=p<=8 and w%8==0 and sz==(w//8)*h*p and sz>=64:
                body,end,got = unrle(d,i+12,sz)
                print("0x%06x  %3dx%-3d planes=%d  unpacked=%6d  packed=%6d (%.1f%%)  %s"
                      % (i,w,h,p,sz,end-(i+12),100*(end-i-12)/sz,
                         "OK" if got>=sz else "SHORT %d"%got))
        return
    hdr = int(sys.argv[2],0)
    w,h,p,x,y,sz = struct.unpack_from('>6H',d,hdr)
    body,end,got = unrle(d,hdr+12,sz)
    print("%dx%d planes=%d  unpacked %d  packed %d bytes (%.1f%%)" % (w,h,p,sz,end-hdr-12,100*(end-hdr-12)/sz))
    if len(sys.argv) > 3 and not sys.argv[3].startswith('--'):
        n = 1<<p
        pal = [(i*255//max(1,n-1),)*3 for i in range(n)]
        if '--pal' in sys.argv:
            o = int(sys.argv[sys.argv.index('--pal')+1],0)
            pal = [((( struct.unpack_from('>H',d,o+2*i)[0]>>8)&15)*17,
                    ((struct.unpack_from('>H',d,o+2*i)[0]>>4)&15)*17,
                    (struct.unpack_from('>H',d,o+2*i)[0]&15)*17) for i in range(n)]
        png(sys.argv[3], w,h, deplane(body,w,h,p,'--sep' in sys.argv), pal)
        print("wrote", sys.argv[3])

main()
