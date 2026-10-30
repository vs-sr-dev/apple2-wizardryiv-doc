#!/usr/bin/env python3
"""Disassemble a copper list out of a hunk file, with AGA register names.

    python tools/copperdump.py <file> <file offset of the list> [--limit N]
    python tools/copperdump.py <file> --find <base> <length>   list terminators

On Guardian the list the game installs is at file offset 0x63674 (chip DATA
hunk 2 + 0x8b8); `move.l #$8b8,$dff080` in the code is a relocation into hunk 2,
which is why the constant alone is meaningless (see docs/00-overview.md).
"""
import sys, struct, collections

NAMES = {0x08e:'DIWSTRT',0x090:'DIWSTOP',0x092:'DDFSTRT',0x094:'DDFSTOP',0x096:'DMACON',
 0x09a:'INTENA',0x09c:'INTREQ',0x100:'BPLCON0',0x102:'BPLCON1',0x104:'BPLCON2',
 0x106:'BPLCON3',0x108:'BPL1MOD',0x10a:'BPL2MOD',0x10c:'BPLCON4',0x1e4:'DIWHIGH',
 0x1fc:'FMODE',0x1fe:'NOOP',0x02e:'COPCON'}
for i in range(32): NAMES[0x180+2*i] = 'COLOR%02d' % i
for i in range(8):
    NAMES[0x0e0+4*i] = 'BPL%dPTH' % (i+1); NAMES[0x0e2+4*i] = 'BPL%dPTL' % (i+1)
    NAMES[0x120+4*i] = 'SPR%dPTH' % i;     NAMES[0x122+4*i] = 'SPR%dPTL' % i
    NAMES[0x140+8*i] = 'SPR%dPOS' % i;     NAMES[0x142+8*i] = 'SPR%dCTL' % i

def bplcon3(v):
    return "bank=%d PF2OF=%d LOCT=%d" % (v >> 13, (v >> 10) & 7, (v >> 9) & 1)

def main():
    d = open(sys.argv[1],'rb').read()
    if '--find' in sys.argv:
        b = int(sys.argv[sys.argv.index('--find')+1],0); ln = int(sys.argv[sys.argv.index('--find')+2],0)
        print([hex(i-b) for i in range(b,b+ln-3,2) if d[i:i+4]==b'\xff\xff\xff\xfe'])
        return
    o = int(sys.argv[2],0); start = o
    limit = int(sys.argv[sys.argv.index('--limit')+1]) if '--limit' in sys.argv else 10**9
    regs = collections.Counter(); waits = []
    n = 0
    while o < len(d)-3 and n < limit:
        w1,w2 = struct.unpack_from('>HH', d, o)
        rel = o - start
        if w1 == 0xffff and w2 == 0xfffe:
            print("+%05x  ffff fffe   END" % rel); n += 1; break
        if w1 & 1:
            waits.append((w1>>8)&0xff)
            print("+%05x  %04x %04x   %s  VP=%3d HP=%02x  mask=%04x"
                  % (rel,w1,w2,"SKIP" if w2&1 else "WAIT",(w1>>8)&0xff,w1&0xfe,w2))
        else:
            r = w1 & 0x1fe; regs[r] += 1
            extra = "   " + bplcon3(w2) if r == 0x106 else ""
            print("+%05x  %04x %04x   MOVE %-8s <- %04x%s"
                  % (rel,w1,w2,NAMES.get(r,'$%03X'%r),w2,extra))
        o += 4; n += 1
    print("\n%d instructions, %d bytes, %d WAITs" % (n, o-start+4, len(waits)))
    for r,c in sorted(regs.items(), key=lambda x:-x[1]):
        print("   %-9s x%d" % (NAMES.get(r,'$%03X'%r), c))

main()
