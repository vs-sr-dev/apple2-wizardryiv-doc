#!/usr/bin/env python3
"""Read an AmigaDOS hunk file's HUNK_RELOC32 tables and answer the question
that a disassembly of an absolute-addressing program keeps asking:

    "this instruction stores the longword N -- which hunk is N an offset into,
     and what file offset is that?"

Prints the hunk layout with the file offset of each hunk body, then, for each
relocation, the hunk it patches, the offset inside that hunk, the target hunk,
and the stored value.

    python tools/relocs.py <file>                 layout + summary
    python tools/relocs.py <file> --at 0x2586     which reloc covers this file offset
    python tools/relocs.py <file> --list 0        every relocation in hunk 0
"""
import sys, struct

def be32(d,o): return struct.unpack_from('>I',d,o)[0]

MEMF = {0:'any', 1:'chip', 2:'fast'}

def parse(d):
    o = 0
    assert be32(d,0) == 0x3f3, "not a hunk file"
    o = 4
    n = be32(d,o); o += 4                      # resident library names
    while n: o += 4*n + 4; n = be32(d,o-4)
    table = be32(d,o); first = be32(d,o+4); last = be32(d,o+8); o += 12
    sizes = []
    for i in range(table):
        v = be32(d,o); o += 4
        sizes.append((v & 0x3fffffff, MEMF.get(v >> 30, '?')))
    hunks = []      # (index, kind, filestart, length, memflag)
    relocs = []     # (in_hunk, target_hunk, offset_in_hunk, file_offset_of_word)
    idx = first
    while o < len(d) - 3:
        hid = be32(d,o); o += 4
        t = hid & 0x3fffffff
        if t in (0x3e9, 0x3ea, 0x3eb):            # CODE, DATA, BSS
            ln = be32(d,o)*4; o += 4
            kind = {0x3e9:'CODE',0x3ea:'DATA',0x3eb:'BSS'}[t]
            if t == 0x3eb:
                hunks.append((idx, kind, None, ln, sizes[idx][1])); cur = idx
            else:
                hunks.append((idx, kind, o, ln, sizes[idx][1])); cur = idx; o += ln
        elif t == 0x3ec:                          # RELOC32
            while True:
                cnt = be32(d,o); o += 4
                if cnt == 0: break
                tgt = be32(d,o); o += 4
                for _ in range(cnt):
                    off = be32(d,o); o += 4
                    relocs.append((cur, tgt, off))
        elif t == 0x3f2:                          # END
            idx += 1
        elif t in (0x3f0, 0x3f1):                 # SYMBOL, DEBUG
            if t == 0x3f1:
                ln = be32(d,o)*4; o += 4 + ln
            else:
                while True:
                    ln = be32(d,o); o += 4
                    if ln == 0: break
                    o += ln*4 + 4
        else:
            break
    return hunks, relocs

def main():
    d = open(sys.argv[1],'rb').read()
    hunks, relocs = parse(d)
    start = {h[0]: h[2] for h in hunks}
    print("hunk  kind  memory   length      file offset of body")
    for (i,k,fs,ln,mf) in hunks:
        print("  %-3d %-5s %-6s %9d   %s" % (i,k,mf,ln, "0x%06x"%fs if fs is not None else "-- (bss)"))
    print("\n%d relocations" % len(relocs))
    import collections
    c = collections.Counter((a,b) for a,b,_ in relocs)
    for (a,b),n in sorted(c.items()):
        print("  hunk %d -> hunk %d : %d" % (a,b,n))

    if '--at' in sys.argv:
        q = int(sys.argv[sys.argv.index('--at')+1], 0)
        for (a,b,off) in relocs:
            fo = start[a] + off
            if fo <= q < fo+4:
                v = be32(d, fo)
                tgt_fs = start.get(b)
                print("\nfile 0x%06x is a relocation in hunk %d -> hunk %d, stored value 0x%x"
                      % (fo, a, b, v))
                if tgt_fs is not None:
                    print("  = hunk %d offset 0x%x = file offset 0x%06x" % (b, v, tgt_fs+v))
                else:
                    print("  = hunk %d (BSS) offset 0x%x -- no file image" % (b, v))
                return
        print("\nfile 0x%06x is NOT covered by a relocation (the constant is literal)" % q)

    if '--list' in sys.argv:
        h = int(sys.argv[sys.argv.index('--list')+1], 0)
        for (a,b,off) in relocs:
            if a != h: continue
            fo = start[a]+off
            v = be32(d,fo)
            print("  hunk%d+0x%06x (file 0x%06x) -> hunk%d+0x%06x" % (a,off,fo,b,v))

if __name__ == '__main__':
    main()
