#!/usr/bin/env python3
"""Custom-chip register scan with base-register tracking.

Two scans, because a program can do it either way and one scan misses half of
it (platform notes, section 4):

  absolute   move.w #imm,$00DFF0xx      -- the whole address is in the code
  based      movea.l #$dff000,aN / lea $dff000,aN, then d16(aN)

The based scan walks forward from each base load, following the instruction
stream linearly, and attributes every d16(aN) access to a register name until
aN is reloaded with something else or an rts/jmp ends the run.

    python tools/regscan.py <file> [--sites REGNAME]
"""
import sys, struct, collections

REG = {
 0x000:'BLTDDAT',0x002:'DMACONR',0x004:'VPOSR',0x006:'VHPOSR',0x008:'DSKDATR',
 0x00A:'JOY0DAT',0x00C:'JOY1DAT',0x00E:'CLXDAT',0x010:'ADKCONR',0x012:'POT0DAT',
 0x014:'POT1DAT',0x016:'POTGOR',0x018:'SERDATR',0x01A:'DSKBYTR',0x01C:'INTENAR',
 0x01E:'INTREQR',0x020:'DSKPTH',0x024:'DSKLEN',0x02A:'VPOSW',0x02C:'VHPOSW',
 0x02E:'COPCON',0x030:'SERDAT',0x032:'SERPER',0x034:'POTGO',0x036:'JOYTEST',
 0x040:'BLTCON0',0x042:'BLTCON1',0x044:'BLTAFWM',0x046:'BLTALWM',
 0x048:'BLTCPTH',0x04A:'BLTCPTL',0x04C:'BLTBPTH',0x04E:'BLTBPTL',
 0x050:'BLTAPTH',0x052:'BLTAPTL',0x054:'BLTDPTH',0x056:'BLTDPTL',
 0x058:'BLTSIZE',0x05A:'BLTCON0L',0x05C:'BLTSIZV',0x05E:'BLTSIZH',
 0x060:'BLTCMOD',0x062:'BLTBMOD',0x064:'BLTAMOD',0x066:'BLTDMOD',
 0x070:'BLTCDAT',0x072:'BLTBDAT',0x074:'BLTADAT',0x07C:'DENISEID',0x07E:'DSKSYNC',
 0x080:'COP1LCH',0x082:'COP1LCL',0x084:'COP2LCH',0x086:'COP2LCL',
 0x088:'COPJMP1',0x08A:'COPJMP2',0x08E:'DIWSTRT',0x090:'DIWSTOP',
 0x092:'DDFSTRT',0x094:'DDFSTOP',0x096:'DMACON',0x098:'CLXCON',
 0x09A:'INTENA',0x09C:'INTREQ',0x09E:'ADKCON',
 0x0A0:'AUD0LCH',0x0A2:'AUD0LCL',0x0A4:'AUD0LEN',0x0A6:'AUD0PER',0x0A8:'AUD0VOL',0x0AA:'AUD0DAT',
 0x0B0:'AUD1LCH',0x0B2:'AUD1LCL',0x0B4:'AUD1LEN',0x0B6:'AUD1PER',0x0B8:'AUD1VOL',0x0BA:'AUD1DAT',
 0x0C0:'AUD2LCH',0x0C2:'AUD2LCL',0x0C4:'AUD2LEN',0x0C6:'AUD2PER',0x0C8:'AUD2VOL',0x0CA:'AUD2DAT',
 0x0D0:'AUD3LCH',0x0D2:'AUD3LCL',0x0D4:'AUD3LEN',0x0D6:'AUD3PER',0x0D8:'AUD3VOL',0x0DA:'AUD3DAT',
 0x0E0:'BPL1PTH',0x0E4:'BPL2PTH',0x0E8:'BPL3PTH',0x0EC:'BPL4PTH',
 0x0F0:'BPL5PTH',0x0F4:'BPL6PTH',0x0F8:'BPL7PTH',0x0FC:'BPL8PTH',
 0x100:'BPLCON0',0x102:'BPLCON1',0x104:'BPLCON2',0x106:'BPLCON3',
 0x108:'BPL1MOD',0x10A:'BPL2MOD',0x10C:'BPLCON4',
 0x110:'BPL1DAT',0x112:'BPL2DAT',0x114:'BPL3DAT',0x116:'BPL4DAT',
 0x118:'BPL5DAT',0x11A:'BPL6DAT',0x11C:'BPL7DAT',0x11E:'BPL8DAT',
 0x120:'SPR0PTH',0x124:'SPR1PTH',0x128:'SPR2PTH',0x12C:'SPR3PTH',
 0x130:'SPR4PTH',0x134:'SPR5PTH',0x138:'SPR6PTH',0x13C:'SPR7PTH',
 0x1DC:'BEAMCON0',0x1E4:'DIWHIGH',0x1FC:'FMODE',
}
for i in range(32):
    REG[0x180 + 2*i] = 'COLOR%02d' % i

def be16(d,o): return struct.unpack_from('>H',d,o)[0]
def be32(d,o): return struct.unpack_from('>I',d,o)[0]
def s16(v): return v-0x10000 if v & 0x8000 else v

def rname(off):
    if off in REG: return REG[off]
    return '$%03X' % off

def main():
    path = sys.argv[1]
    want = None
    if '--sites' in sys.argv: want = sys.argv[sys.argv.index('--sites')+1]
    d = open(path,'rb').read()

    # ---- absolute references -------------------------------------------------
    absolute = collections.Counter()
    for i in range(len(d)-5):
        if d[i+2:i+5] == b'\x00\xdf\xf0':
            absolute[d[i+5]] += 1

    # ---- base loads ----------------------------------------------------------
    loads = []
    for i in range(len(d)-5):
        op = be16(d,i)
        if d[i+2:i+6] == b'\x00\xdf\xf0\x00':
            if (op & 0xf1ff) == 0x207c:            # movea.l #imm,aN
                loads.append((i, (op>>9)&7, 'movea.l'))
            elif (op & 0xf1ff) == 0x41f9:          # lea imm.l,aN
                loads.append((i, (op>>9)&7, 'lea'))

    based = collections.Counter()
    sites = collections.defaultdict(list)
    for (off, an, kind) in loads:
        # linear walk forward, coarse but sufficient: stop at 512 bytes, at an
        # rts/rte/jmp, or at a reload of the same register
        p = off + 6
        end = min(len(d)-3, off + 4096)
        while p < end:
            w = be16(d,p)
            if w in (0x4e75, 0x4e73, 0x4e77):      # rts rte rtr
                break
            if (w & 0xf1ff) in (0x207c, 0x41f9) and ((w>>9)&7) == an:
                break
            # any d16(aN) effective address in a move/btst/bset/etc:
            # mode 5 (101) reg aN, either as source (bits 5-3,2-0) or dest (11-9,8-6)
            hit = False
            src_mode = (w >> 3) & 7; src_reg = w & 7
            dst_mode = (w >> 6) & 7; dst_reg = (w >> 9) & 7
            if src_mode == 5 and src_reg == an:
                disp = s16(be16(d, p+2)) & 0xffff
                based[disp] += 1; sites[disp].append(p); hit = True
            if dst_mode == 5 and dst_reg == an and (w >> 12) in (1,2,3):
                # move with d16(aN) destination: displacement follows any source ext
                extra = 0
                if src_mode == 7 and src_reg == 4: extra = 4 if (w>>12)==2 else 2
                elif src_mode == 5 or src_mode == 6: extra = 2
                elif src_mode == 7 and src_reg in (0,2,3): extra = 2
                elif src_mode == 7 and src_reg == 1: extra = 4
                disp = s16(be16(d, p+2+extra)) & 0xffff
                based[disp] += 1; sites[disp].append(p); hit = True
            p += 2

    print("=== absolute  move.w #imm,$00DFF0xx  ===")
    for k in sorted(absolute):
        print("  $DFF0%02X %-10s x%d" % (k, rname(k), absolute[k]))
    print("  total %d in %d distinct registers" % (sum(absolute.values()), len(absolute)))

    print("\n=== base loads of $DFF000 ===")
    for (off, an, kind) in loads:
        print("  0x%06x  %s #$dff000,a%d" % (off, kind, an))
    print("  %d base loads" % len(loads))

    print("\n=== registers reached as d16(aN) after a base load ===")
    for k in sorted(based):
        if k > 0x400: continue
        print("  $DFF%03X %-10s x%d" % (k, rname(k), based[k]))
    tot = sum(v for k,v in based.items() if k <= 0x400)
    print("  total %d accesses, %d distinct registers"
          % (tot, len([k for k in based if k <= 0x400])))

    if want:
        for k in sorted(based):
            if rname(k) == want:
                print("\nsites for %s:" % want, ", ".join("0x%x" % s for s in sites[k]))

if __name__ == '__main__':
    main()
