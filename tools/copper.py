#!/usr/bin/env python3
"""Decode a copper list out of /cosm's chip DATA hunk.

Hunk 1 begins at file offset 0x20c84 and the module map addresses it as
0x19ef8 + offset-within-hunk, so file = 0x20c84 + (addr - 0x19ef8).
"""
import sys
REG = {0x080:'COP1LC',0x084:'COP2LC',0x088:'COPJMP1',0x08a:'COPJMP2',
       0x08e:'DIWSTRT',0x090:'DIWSTOP',0x092:'DDFSTRT',0x094:'DDFSTOP',
       0x096:'DMACON',0x100:'BPLCON0',0x102:'BPLCON1',0x104:'BPLCON2',
       0x106:'BPLCON3',0x108:'BPL1MOD',0x10a:'BPL2MOD',0x10c:'BPLCON4',
       0x1fc:'FMODE',0x1dc:'BEAMCON0',0x1e4:'DIWHIGH',0x02e:'COPCON'}
for i in range(8): REG[0x0e0+i*4]='BPL%dPTH'%(i+1); REG[0x0e2+i*4]='BPL%dPTL'%(i+1)
for i in range(32): REG[0x180+i*2]='COLOR%02d'%i
d=open(sys.argv[1],'rb').read()
addr=int(sys.argv[2],0); n=int(sys.argv[3],0)
off=0x20c84+addr
b=d[off:off+n]
for i in range(0,len(b)-3,4):
    w1=int.from_bytes(b[i:i+2],'big'); w2=int.from_bytes(b[i+2:i+4],'big')
    if w1&1:
        kind='WAIT ' if not (w2&1) else 'SKIP '
        print('%05x  %04x %04x  %s vp=%02x hp=%02x  mask=%04x' %
              (addr+i,w1,w2,kind,(w1>>8)&0xff,w1&0xfe,w2))
        if w1==0xffff and w2==0xfffe: print('%05x  ---- end ----'%(addr+i)); break
    else:
        r=w1&0x1fe
        print('%05x  %04x %04x  MOVE %-8s <- %04x' % (addr+i,w1,w2,REG.get(r,'$%03x'%r),w2))
