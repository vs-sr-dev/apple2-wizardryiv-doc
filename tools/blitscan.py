#!/usr/bin/env python3
"""Exact-encoding scan for blitter register writes.

`chipregs.py` is deliberately an upper bound and is useless for the blitter,
because a displacement of $000-$05E collides with every small immediate in the
file.  This scan matches whole `move.w <src>,d16(An)` and
`move.w #imm,$00DFFxxx.l` encodings instead, so every hit is a real write.

    move.w <ea>,d16(An)      opcode word 0x3040 | (An<<9) | (5<<6 is implied)
                             -> 0x3140+An*0x200 pattern, then the displacement
    move.w #imm,d16(An)      0x3?7C imm disp
    move.w #imm,$00DFFxxx.l  0x33FC imm 00DF F0xx

Reports every write to BLTCON0/1, BLTSIZE, BLTAFWM/ALWM, the four modulos and
the four pointers, with the immediate where there is one, and decodes BLTCON0
minterm/USEx and BLTCON1 fill bits.

    python3 tools/blitscan.py FILE [FILE ...]
"""
import sys, struct, collections

BLT = {0x040: "BLTCON0", 0x042: "BLTCON1", 0x044: "BLTAFWM", 0x046: "BLTALWM",
       0x048: "BLTCPTH", 0x04C: "BLTBPTH", 0x050: "BLTAPTH", 0x054: "BLTDPTH",
       0x058: "BLTSIZE", 0x060: "BLTCMOD", 0x062: "BLTBMOD", 0x064: "BLTAMOD",
       0x066: "BLTDMOD", 0x070: "BLTCDAT", 0x072: "BLTBDAT", 0x074: "BLTADAT",
       0x05A: "BLTCON0L", 0x05C: "BLTSIZV", 0x05E: "BLTSIZH"}


def decode_con0(v):
    use = "".join(c for c, b in zip("ABCD", (0x800, 0x400, 0x200, 0x100)) if v & b)
    return "minterm=$%02X ASH=%d USE%s" % (v & 0xFF, (v >> 12) & 0xF, use or "-")


def decode_con1(v):
    f = []
    if v & 0x0008:
        f.append("FILL_CARRYIN")
    if v & 0x0010:
        f.append("FILL_OR")
    if v & 0x0020:
        f.append("FILL_XOR")
    if v & 0x0002:
        f.append("BLITREVERSE")
    if v & 0x0001:
        f.append("LINE")
    return "BSH=%d %s" % ((v >> 12) & 0xF, " ".join(f) or "no fill, area mode")


def scan(path):
    d = open(path, "rb").read()
    hits = []
    n = len(d)
    for o in range(0, n - 8, 2):
        w = struct.unpack_from(">H", d, o)[0]
        # move.w #imm,$00DFFxxx.l  : 33FC imm 00DF F0xx
        if w == 0x33FC and struct.unpack_from(">H", d, o + 4)[0] == 0x00DF:
            a = struct.unpack_from(">H", d, o + 6)[0]
            if (a & 0xFF00) == 0xF000:
                r = a & 0xFF
                if r in BLT:
                    hits.append((o, BLT[r], struct.unpack_from(">H", d, o + 2)[0], "abs"))
            continue
        # move.w <ea>,d16(An) : 0011 rrr 101 mmmrrr  -> (w>>6)&7 == 5
        if (w & 0xF000) == 0x3000 and ((w >> 6) & 7) == 5:
            an = (w >> 9) & 7
            src = w & 0x3F
            imm = None
            disp_off = o + 2
            if src == 0x3C:  # #imm.w -> immediate comes FIRST, then displacement
                imm = struct.unpack_from(">H", d, o + 2)[0]
                disp_off = o + 4
            if disp_off + 2 > n:
                continue
            disp = struct.unpack_from(">H", d, disp_off)[0]
            if disp in BLT:
                hits.append((o, BLT[disp], imm, "a%d" % an))
    return hits


def main():
    for p in sys.argv[1:]:
        hits = scan(p)
        c = collections.Counter(h[1] for h in hits)
        print("=== %s : %d blitter writes ===" % (p, len(hits)))
        for k in sorted(c, key=lambda x: -c[x]):
            print("   %-9s x%d" % (k, c[k]))
        print()
        for o, name, imm, base in hits:
            extra = ""
            if imm is not None:
                if name == "BLTCON0":
                    extra = "  #$%04X  %s" % (imm, decode_con0(imm))
                elif name == "BLTCON1":
                    extra = "  #$%04X  %s" % (imm, decode_con1(imm))
                elif name == "BLTSIZE":
                    extra = "  #$%04X  h=%d w=%d words" % (imm, (imm >> 6) or 1024, (imm & 0x3F) or 64)
                else:
                    extra = "  #$%04X" % imm
            print("   0x%06x  %-9s via %-4s%s" % (o, name, base, extra))
        print()


if __name__ == "__main__":
    main()
