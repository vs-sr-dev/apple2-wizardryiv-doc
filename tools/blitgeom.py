#!/usr/bin/env python3
"""Section 4's three questions, answered with numbers instead of intuition.

1. Is there a BLTCON1 write, and does it carry the FILL bits?
2. What is the height in BLTSIZE and what are the modulos?  Pairing a BLTSIZE
   with the BLTDMOD written just before it gives the destination row stride --
   (words * 2) + modulo bytes -- and therefore the real pixel width of the
   bitmap being drawn into.  On a scrolling game that width is larger than the
   screen, and the difference is how far the playfield scrolls.
3. For minterm $CA, is USEA set?  $CA with USEA on is an ordinary masked bob;
   $CA with USEA off and BLTADAT loaded outside the loop is a cookie-cut.

Custom-register writes are matched as whole instruction encodings against the
two addressing forms that actually occur -- `move.w #imm,$dff0xx.l` and
`move.w #imm,d16(An)` -- rather than by searching for the displacement, which
collides with immediates.

Usage: python3 tools/blitgeom.py <file>...
"""
import sys, os, struct
from collections import Counter

REG = {0x040: "BLTCON0", 0x042: "BLTCON1", 0x044: "BLTAFWM", 0x046: "BLTALWM",
       0x048: "BLTCPTH", 0x04C: "BLTBPTH", 0x050: "BLTAPTH", 0x054: "BLTDPTH",
       0x058: "BLTSIZE", 0x05A: "BLTCON0L", 0x05C: "BLTSIZV", 0x05E: "BLTSIZH",
       0x060: "BLTCMOD", 0x062: "BLTBMOD", 0x064: "BLTAMOD", 0x066: "BLTDMOD",
       0x070: "BLTCDAT", 0x072: "BLTBDAT", 0x074: "BLTADAT"}

USEA, USEB, USEC, USED = 0x800, 0x400, 0x200, 0x100


def decode(d):
    """Yield (offset, regname, immediate-or-None) for custom-register writes."""
    n = len(d)
    for i in range(0, n - 7, 2):
        op = struct.unpack_from(">H", d, i)[0]
        # move.w #imm,$00dffXXX.l   = 33FC imm 00df fXXX
        if op == 0x33FC and i + 8 <= n:
            imm = struct.unpack_from(">H", d, i + 2)[0]
            adr = struct.unpack_from(">I", d, i + 4)[0]
            if (adr & 0xFFFFF000) == 0x00DFF000:
                r = adr & 0x1FF
                if r in REG:
                    yield (i, REG[r], imm)
        # move.w #imm,d16(An)       = 3?7C imm d16     (An = a0..a7)
        elif (op & 0xFFF8) == 0x317C and i + 6 <= n:
            imm = struct.unpack_from(">H", d, i + 2)[0]
            d16 = struct.unpack_from(">H", d, i + 4)[0]
            if d16 in REG:
                yield (i, REG[d16], imm)
        # move.w Dn,d16(An)         = 3?8? -- register source, no immediate
        elif (op & 0xF1C0) == 0x3140 and i + 4 <= n:
            d16 = struct.unpack_from(">H", d, i + 2)[0]
            if d16 in REG:
                yield (i, REG[d16], None)


def main():
    widths = Counter()
    con0 = Counter()
    con1 = Counter()
    fills = []
    ca_sites = []
    allsizes = Counter()
    for p in sys.argv[1:]:
        d = open(p, "rb").read()
        rel = os.path.basename(p)
        ev = list(decode(d))
        lastmod = {}
        lastcon0 = None
        for off, r, imm in ev:
            if r in ("BLTDMOD", "BLTAMOD", "BLTCMOD", "BLTBMOD"):
                lastmod[r] = (off, imm)
            elif r == "BLTCON0" and imm is not None:
                con0[imm] += 1
                lastcon0 = (off, imm)
                mt = imm & 0xFF
                if mt == 0xCA:
                    ca_sites.append((rel, off, imm, bool(imm & USEA), bool(imm & USEB),
                                     bool(imm & USEC), bool(imm & USED)))
            elif r == "BLTCON1" and imm is not None:
                con1[imm] += 1
                if imm & 0x0018:  # FILL_OR | FILL_XOR
                    fills.append((rel, off, imm))
            elif r == "BLTSIZE" and imm is not None:
                h = (imm >> 6) & 0x3FF
                w = imm & 0x3F
                h = h or 1024
                w = w or 64
                allsizes[(h, w)] += 1
                for mr in ("BLTDMOD", "BLTAMOD"):
                    if mr in lastmod and 0 < off - lastmod[mr][0] < 64 and lastmod[mr][1] is not None:
                        mod = lastmod[mr][1]
                        if mod > 32767:
                            continue
                        stride = w * 2 + mod
                        widths[(mr, stride * 8, stride)] += 1

    print("=== BLTCON0 immediates (minterm = low byte) ===")
    for v, c in con0.most_common():
        print("  $%04X  minterm $%02X  USEA=%d USEB=%d USEC=%d USED=%d  ashift=%d  x%d" %
              (v, v & 0xFF, bool(v & USEA), bool(v & USEB), bool(v & USEC),
               bool(v & USED), v >> 12, c))
    print()
    print("=== BLTCON1 immediates ===")
    for v, c in con1.most_common():
        print("  $%04X  FILL_OR=%d FILL_XOR=%d FCI=%d DESC=%d LINE=%d  x%d" %
              (v, bool(v & 0x0008), bool(v & 0x0010), bool(v & 0x0004),
               bool(v & 0x0002), bool(v & 0x0001), c))
    print("  writes with a FILL bit set: %d" % len(fills))
    for r in fills:
        print("    %s 0x%06x $%04X" % r)
    print()
    print("=== minterm $CA sites (masked bob vs cookie-cut) ===")
    if not ca_sites:
        print("  none")
    for rel, off, v, a, b, c, dd in ca_sites:
        print("  %-40s 0x%06x $%04X USEA=%d -> %s" %
              (rel, off, v, a, "ordinary masked bob" if a else "COOKIE-CUT (BLTADAT set outside the loop)"))
    print()
    print("=== implied destination width from (BLTSIZE words, modulo) ===")
    print("  %-10s %8s %8s %6s" % ("modreg", "px wide", "bytes", "count"))
    for (mr, px, by), c in sorted(widths.items(), key=lambda kv: -kv[1]):
        print("  %-10s %8d %8d %6d" % (mr, px, by, c))
    print()
    print("=== BLTSIZE height x width, most common ===")
    for (h, w), c in allsizes.most_common(20):
        print("  h=%-5d w=%-3d words (%4d px)  x%d" % (h, w, w * 16, c))


main()
