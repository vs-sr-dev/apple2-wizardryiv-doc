#!/usr/bin/env python3
"""Find and classify every stored copper list in a file.

A copper list is a run of longwords that are either MOVEs (bit 0 of the
first word clear, register offset in 0x000..0x1FE) or WAIT/SKIP (bit 0 set).
The scanner walks the file two words at a time and keeps every run that is
at least `--min` instructions long and contains at least one BPLCON0 or
bitplane-pointer write, so palette tables and coordinate arrays do not
qualify.

For every BPLCON0 value it reports the bitplane count **computed** as

    BPU = ((v >> 12) & 7) | (((v >> 4) & 1) << 3)

because BPLCON0's fourth bitplane-count bit is BPU3 at bit 4 (platform
notes, section 7): a scan that reads only bits 14-12 calls $0211 a
zero-bitplane screen when it is an eight-plane one.  Six planes are only
Extra-Half-Brite -- i.e. ECS -- if BPLCON2 bit 9 (KILLEHB) is clear, so the
BPLCON2 seen in the same list is reported next to it.

    python3 tools/copperfind.py FILE [--min 8] [--dump N]
"""
import sys, argparse


def regname(r):
    R = {0x100: 'BPLCON0', 0x102: 'BPLCON1', 0x104: 'BPLCON2', 0x106: 'BPLCON3',
         0x108: 'BPL1MOD', 0x10A: 'BPL2MOD', 0x10C: 'BPLCON4',
         0x08E: 'DIWSTRT', 0x090: 'DIWSTOP', 0x092: 'DDFSTRT', 0x094: 'DDFSTOP',
         0x096: 'DMACON', 0x1FC: 'FMODE', 0x1E4: 'DIWHIGH', 0x1DC: 'BEAMCON0',
         0x02A: 'VPOSW', 0x02C: 'VHPOSW', 0x088: 'COPJMP1', 0x08A: 'COPJMP2',
         0x084: 'COP2LCH', 0x086: 'COP2LCL', 0x080: 'COP1LCH', 0x082: 'COP1LCL'}
    for i in range(8):
        R[0x0E0 + 4 * i] = 'BPL%dPTH' % (i + 1)
        R[0x0E2 + 4 * i] = 'BPL%dPTL' % (i + 1)
        R[0x120 + 4 * i] = 'SPR%dPTH' % i
        R[0x122 + 4 * i] = 'SPR%dPTL' % i
    for i in range(32):
        R[0x180 + 2 * i] = 'COLOR%02d' % i
    return R.get(r, '$%03X' % r)


def bpu(v):
    return ((v >> 12) & 7) | (((v >> 4) & 1) << 3)


def decode_bplcon0(v):
    f = []
    if v & 0x8000: f.append('HIRES')
    if v & 0x0800: f.append('HAM')
    if v & 0x0400: f.append('DBLPF')
    if v & 0x0200: f.append('COLOR')
    if v & 0x0100: f.append('GAUD')
    if v & 0x0080: f.append('UHRES')
    if v & 0x0040: f.append('SHRES')
    if v & 0x0020: f.append('BYPASS')
    if v & 0x0008: f.append('LPEN')
    if v & 0x0004: f.append('LACE')
    if v & 0x0002: f.append('ERSY')
    if v & 0x0001: f.append('ECSENA')
    return f


def w(d, o):
    return int.from_bytes(d[o:o + 2], 'big')


def runs(d, minlen):
    out = []
    o, start, n = 0, None, 0
    while o + 4 <= len(d):
        a, b = w(d, o), w(d, o + 2)
        ok = False
        if (a & 1) == 0 and (a & 0x1FE) == (a & 0x1FF) and (a & 0xFE00) == 0 and a <= 0x1FE:
            ok = True                    # MOVE
        elif (a & 1) == 1 and (b & 1) in (0, 1):
            ok = True                    # WAIT / SKIP
        if ok:
            if start is None:
                start, n = o, 0
            n += 1
            o += 4
            if a == 0xFFFF and b == 0xFFFE:
                if n >= minlen:
                    out.append((start, o))
                start = None
        else:
            if start is not None and n >= minlen:
                out.append((start, o))
            start = None
            o += 2
    if start is not None and n >= minlen:
        out.append((start, o))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--min", type=int, default=10)
    ap.add_argument("--dump", type=lambda s: int(s, 0))
    ap.add_argument("--base", type=lambda s: int(s, 0), default=0,
                    help="file offset of the hunk body, for hunk-relative reporting")
    a = ap.parse_args()
    d = open(a.file, 'rb').read()

    if a.dump is not None:
        o = a.dump
        while o + 4 <= len(d):
            x, y = w(d, o), w(d, o + 2)
            if x & 1:
                print("%06x  %-6s vp=%02x hp=%02x  (%04x %04x)"
                      % (o, 'SKIP' if (y & 1) else 'WAIT', (x >> 8) & 0xff, x & 0xfe, x, y))
                if x == 0xFFFF and y == 0xFFFE:
                    break
            else:
                extra = ''
                if x == 0x100:
                    extra = "  BPU=%d %s" % (bpu(y), ','.join(decode_bplcon0(y)))
                print("%06x  MOVE  %-9s $%04x%s" % (o, regname(x), y, extra))
            o += 4
        return

    found = runs(d, a.min)
    print("### %s  --  %d candidate copper lists (>= %d instructions)"
          % (a.file, len(found), a.min))
    tot0 = 0
    for s, e in found:
        regs = {}
        bplcon0 = []
        bplcon2 = None
        bplcon3 = None
        fmode = None
        ptrs = set()
        for o in range(s, e, 4):
            x, y = w(d, o), w(d, o + 2)
            if x & 1:
                continue
            regs[x] = regs.get(x, 0) + 1
            if x == 0x100:
                bplcon0.append((o, y))
            elif x == 0x104:
                bplcon2 = y
            elif x == 0x106:
                bplcon3 = y
            elif x == 0x1FC:
                fmode = y
            elif 0x0E0 <= x < 0x100:
                ptrs.add((x - 0x0E0) // 4 + 1)
        if not bplcon0 and not ptrs:
            continue
        tot0 += len(bplcon0)
        print("  list at file 0x%06x (hunk +0x%06x), %d instructions, %d bytes"
              % (s, s - a.base, (e - s) // 4, e - s))
        print("    bitplane pointers written: %s" % (sorted(ptrs) or 'none'))
        if bplcon2 is not None:
            print("    BPLCON2 $%04x   KILLEHB(bit9)=%d" % (bplcon2, (bplcon2 >> 9) & 1))
        if bplcon3 is not None:
            print("    BPLCON3 $%04x" % bplcon3)
        if fmode is not None:
            print("    FMODE   $%04x" % fmode)
        for o, v in bplcon0:
            print("    BPLCON0 $%04x at 0x%06x  ->  BPU=%d  %s"
                  % (v, o, bpu(v), ','.join(decode_bplcon0(v))))
    print("  total BPLCON0 writes in qualifying lists: %d" % tot0)


main()
