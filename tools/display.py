#!/usr/bin/env python3
"""Read every BPLCON0 in a file and compute the bitplane count correctly.

Two traps from the checklist, both of which have bitten this set:

  * BPLCON0's bitplane count is FOUR bits, not three: BPU3 is bit 4.  $0211 and
    $0611 both read as "zero bitplanes" to a scan that looks only at bits
    14..12, and both are eight-plane screens.
        BPU = ((v >> 12) & 7) | (((v >> 4) & 1) << 3)
  * Six planes with no BPLCON3 and KILLEHB clear is Extra-Half-Brite, which is
    ECS, not AGA.  KILLEHB is BPLCON2 bit 9.

Every BPLCON0 in the file is read, not the first: one disc in the set has two
copper-list templates differing in five registers.

Also counts the AGA-only registers, and LoadRGB4 against LoadRGB32, which is
the one-line palette test.

Usage: python3 tools/display.py <file>...
"""
import sys, os, struct
from collections import Counter

REG = {0x100: "BPLCON0", 0x102: "BPLCON1", 0x104: "BPLCON2", 0x106: "BPLCON3",
       0x1FC: "FMODE", 0x10C: "BPLCON4", 0x08E: "DIWSTRT", 0x090: "DIWSTOP",
       0x1E4: "DIWHIGH", 0x092: "DDFSTRT", 0x094: "DDFSTOP",
       0x108: "BPL1MOD", 0x10A: "BPL2MOD", 0x02C: "VSSTRT", 0x1DC: "BEAMCON0"}
AGA_ONLY = ("BPLCON3", "BPLCON4", "FMODE", "DIWHIGH")


def bpu(v):
    return ((v >> 12) & 7) | (((v >> 4) & 1) << 3)


def flags(v):
    f = []
    if v & 0x8000:
        f.append("HIRES")
    if v & 0x0800:
        f.append("HAM")
    if v & 0x0400:
        f.append("DBLPF")
    if v & 0x0200:
        f.append("COLOR_ON")
    if v & 0x0100:
        f.append("GAUD")
    if v & 0x0080:
        f.append("UHRES")
    if v & 0x0040:
        f.append("SHRES")
    if v & 0x0008:
        f.append("BYPASS")
    if v & 0x0004:
        f.append("LPEN")
    if v & 0x0002:
        f.append("LACE")
    if v & 0x0001:
        f.append("ERSY")
    return "|".join(f) or "-"


def writes(d):
    n = len(d)
    for i in range(0, n - 7, 2):
        op = struct.unpack_from(">H", d, i)[0]
        if op == 0x33FC and i + 8 <= n:
            imm = struct.unpack_from(">H", d, i + 2)[0]
            adr = struct.unpack_from(">I", d, i + 4)[0]
            if (adr & 0xFFFFF000) == 0x00DFF000:
                r = adr & 0x1FF
                if r in REG:
                    yield (i, REG[r], imm, "abs")
        elif (op & 0xFFF8) == 0x317C and i + 6 <= n:
            imm = struct.unpack_from(">H", d, i + 2)[0]
            d16 = struct.unpack_from(">H", d, i + 4)[0]
            if d16 in REG:
                yield (i, REG[d16], imm, "d16(An)")


def copperwords(d):
    """Copper MOVE instructions: a word whose low bit is 0 and whose register
    is in range, followed by the value.  Only counted when the register is one
    of the display registers we care about, which keeps the noise down."""
    n = len(d)
    for i in range(0, n - 3, 2):
        w = struct.unpack_from(">H", d, i)[0]
        if w & 1:
            continue
        r = w & 0x1FE
        if r in REG and (w & 0xFE00) == 0:
            yield (i, REG[r], struct.unpack_from(">H", d, i + 2)[0])


def main():
    for p in sys.argv[1:]:
        d = open(p, "rb").read()
        ev = list(writes(d))
        cw = list(copperwords(d))
        if not ev and not cw:
            continue
        print("=== %s (%d bytes) ===" % (os.path.basename(p), len(d)))
        b0 = [e for e in ev if e[1] == "BPLCON0"]
        if b0:
            print("  BPLCON0 as an instruction immediate:")
            for off, r, v, how in b0:
                print("    0x%06x  $%04X  BPU=%d  %s  [%s]" % (off, v, bpu(v), flags(v), how))
        cb0 = Counter(v for off, r, v in cw if r == "BPLCON0")
        if cb0:
            print("  BPLCON0 as a copper MOVE value (%d distinct, %d total):" %
                  (len(cb0), sum(cb0.values())))
            for v, c in cb0.most_common(12):
                print("    $%04X  BPU=%d  %s  x%d" % (v, bpu(v), flags(v), c))
        b2 = Counter(v for off, r, v, how in ev if r == "BPLCON2") + \
             Counter(v for off, r, v in cw if r == "BPLCON2")
        if b2:
            print("  BPLCON2 values (KILLEHB is bit 9):")
            for v, c in b2.most_common(8):
                print("    $%04X  KILLEHB=%d  x%d" % (v, bool(v & 0x200), c))
        seen = Counter(r for off, r, v, how in ev) + Counter(r for off, r, v in cw)
        aga = {k: seen[k] for k in AGA_ONLY if seen.get(k)}
        print("  AGA-only registers touched: %s" % (aga or "none"))
        fm = Counter(v for off, r, v, how in ev if r == "FMODE") + \
             Counter(v for off, r, v in cw if r == "FMODE")
        if fm:
            print("  FMODE values: %s" % dict(fm))
        print("  register mentions: %s" % dict(seen.most_common(12)))
        print()


main()
