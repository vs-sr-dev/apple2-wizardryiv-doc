#!/usr/bin/env python3
"""Walk an Amiga ADF (880 KB floppy image), OFS or FFS.

Prints the boot-block type, the root directory name and dates, and the file
tree with size, date and SHA-1. `-x DIR` extracts.

    python tools/adfread.py <image.adf> [-x outdir]
"""
import sys, struct, os, hashlib, datetime

BS = 512
def be32(d,o): return struct.unpack_from('>I',d,o)[0]

def amidate(days, mins, ticks):
    base = datetime.datetime(1978,1,1)
    return (base + datetime.timedelta(days=days, minutes=mins, seconds=ticks/50.0)).strftime('%Y-%m-%d %H:%M:%S')

def blk(d,n): return d[n*BS:(n+1)*BS]

def name_of(b):
    n = b[BS-80]
    return b[BS-79:BS-79+n].decode('latin1')

def main():
    path = sys.argv[1]
    d = open(path,'rb').read()
    boot = d[:BS]
    print("boot block id %r  flags 0x%02x  rootblock %d  checksum %08x"
          % (boot[:3], boot[3], be32(boot,8), be32(boot,4)))
    ffs = bool(boot[3] & 1)
    print("filesystem:", "FFS" if ffs else "OFS", "  (DOS%d)" % boot[3])
    if boot[:3] != b'DOS':
        print("NOT an AmigaDOS filesystem -- custom bootblock / trackloader")
        print("boot block first 64 bytes:", boot[:64].hex())
        return
    root = 880
    rb = blk(d,root)
    print("root name %r" % name_of(rb))
    print("root  modified %s   disk created %s" %
          (amidate(be32(rb,BS-92),be32(rb,BS-88),be32(rb,BS-84)),
           amidate(be32(rb,BS-40),be32(rb,BS-36),be32(rb,BS-32))))
    out = None
    if '-x' in sys.argv:
        out = sys.argv[sys.argv.index('-x')+1]

    total = [0,0]
    def walk(hdr, prefix):
        b = blk(d,hdr)
        ht = b[BS-208:BS-208+72]           # hash table, 72 longwords
        entries = []
        for i in range(72):
            n = be32(b, 24 + 4*i)
            while n:
                entries.append(n)
                nb = blk(d,n)
                n = be32(nb, BS-16)        # hash chain
        for e in sorted(entries):
            eb = blk(d,e)
            sec = struct.unpack('>i', eb[BS-4:])[0]
            nm = name_of(eb)
            dt = amidate(be32(eb,BS-92),be32(eb,BS-88),be32(eb,BS-84))
            if sec == 2:                                  # directory
                print("%-9s %8s  %s  %s/" % (e,'',dt,prefix+nm)); total[1]+=1
                walk(e, prefix+nm+'/')
            elif sec == -3:                               # file
                size = be32(eb,BS-188)
                data = read_file(eb, size)
                print("%-9s %8d  %s  %s  %s" % (e,size,dt,hashlib.sha1(data).hexdigest(),prefix+nm))
                total[0]+=1
                if out:
                    p = os.path.join(out, (prefix+nm).lstrip('/'))
                    os.makedirs(os.path.dirname(p), exist_ok=True)
                    open(p,'wb').write(data)

    def read_file(eb, size):
        buf = bytearray()
        cur = eb
        while True:
            hi = be32(cur, 8)                # high_seq
            for i in range(hi):
                blkno = be32(cur, 24 + 4*(71-i))
                if ffs: buf += blk(d, blkno)
                else:   buf += blk(d, blkno)[24:]
            ext = be32(cur, BS-8)
            if not ext: break
            cur = blk(d, ext)
        return bytes(buf[:size])

    walk(root, '/')
    print("\n%d files, %d directories" % (total[0], total[1]))

if __name__ == '__main__':
    main()
