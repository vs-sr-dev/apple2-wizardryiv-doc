#!/usr/bin/env python3
"""Where does the frame end up? Count C2P magics as IMMEDIATES, not as data.

The six constants a chunky-to-planar converter needs are also six perfectly
ordinary bit patterns, so counting their appearances anywhere in a file
measures nothing.  What matters is whether they appear as the immediate
operand of `andi.l`, `eori.l` or `ori.l` on a data register, which is the
only place a C2P merge step can put them.

  andi.l #imm,Dn   0000 10nn   -> 0x0280 | n
  ori.l  #imm,Dn   0000 00nn   -> 0x0080 | n
  eori.l #imm,Dn   0000 10nn   -> 0x0A80 | n

The two counts are printed side by side.  The difference between them is the
result: on the Gunship disc the magics appeared 320 times as data and zero
times as immediates, and that is what "no C2P" looks like when it is measured.

Also reports $B80038/$B8003C (the Akiko C2P port) as pointer loads, since a
hardware C2P leaves no immediates at all.

Usage: python3 tools/c2pscan.py <dir-or-file>...
"""
import os, sys, struct
from collections import Counter

MAGICS = {
    0xF0F0F0F0: "F0F0F0F0", 0x0F0F0F0F: "0F0F0F0F",
    0xCCCCCCCC: "CCCCCCCC", 0x33333333: "33333333",
    0xAAAAAAAA: "AAAAAAAA", 0x55555555: "55555555",
}
OPS = {}
for n in range(8):
    OPS[0x0280 | n] = ("andi.l", "d%d" % n)
    OPS[0x0080 | n] = ("ori.l", "d%d" % n)
    OPS[0x0A80 | n] = ("eori.l", "d%d" % n)

LEA = {0x41f9: "a0", 0x43f9: "a1", 0x45f9: "a2", 0x47f9: "a3",
       0x49f9: "a4", 0x4bf9: "a5", 0x4df9: "a6", 0x4ff9: "a7"}
MOVEA = {0x207c: "a0", 0x227c: "a1", 0x247c: "a2", 0x267c: "a3",
         0x287c: "a4", 0x2a7c: "a5", 0x2c7c: "a6", 0x2e7c: "a7"}


def main():
    files = []
    for root in sys.argv[1:]:
        if os.path.isdir(root):
            for dp, dn, fn in os.walk(root):
                for f in sorted(fn):
                    files.append((root, os.path.join(dp, f)))
        else:
            files.append((os.path.dirname(root), root))

    as_data = Counter()
    as_imm = Counter()
    imm_sites = []
    port_sites = []
    for root, p in files:
        d = open(p, "rb").read()
        rel = p[len(root):].replace(os.sep, "/")
        n = len(d)
        # as data: every aligned and unaligned occurrence of the longword
        for i in range(n - 3):
            v = struct.unpack_from(">I", d, i)[0]
            if v in MAGICS:
                as_data[MAGICS[v]] += 1
        # as immediate: opword at even offset followed by the longword
        for i in range(0, n - 5, 2):
            op = struct.unpack_from(">H", d, i)[0]
            if op in OPS:
                v = struct.unpack_from(">I", d, i + 2)[0]
                if v in MAGICS:
                    as_imm[MAGICS[v]] += 1
                    mn, reg = OPS[op]
                    # An even-aligned `02 80` / `0A 80` inside a table of
                    # alternating $55/$AA mask bytes reads as an instruction and
                    # is not one.  Classify by the neighbourhood: if most of the
                    # 32 bytes either side are $55 or $AA, call it data.
                    ctx = d[max(0, i - 32):i] + d[i + 6:i + 38]
                    frac = sum(1 for c in ctx if c in (0x55, 0xAA)) / max(1, len(ctx))
                    imm_sites.append((rel, i, mn, reg, MAGICS[v], frac))
        # the Akiko C2P port as a pointer load
        for i in range(0, n - 5, 2):
            op = struct.unpack_from(">H", d, i)[0]
            if op in LEA or op in MOVEA:
                v = struct.unpack_from(">I", d, i + 2)[0]
                if v in (0x00B80038, 0x00B8003C, 0x00B80030, 0x00B80000):
                    reg = LEA.get(op) or MOVEA.get(op)
                    port_sites.append((rel, i, "%08X" % v, reg))

    print("=== C2P magic constants ===")
    print("%-12s %10s %12s" % ("constant", "as data", "as immediate"))
    for k in ("F0F0F0F0", "0F0F0F0F", "CCCCCCCC", "33333333", "AAAAAAAA", "55555555"):
        print("%-12s %10d %12d" % (k, as_data[k], as_imm[k]))
    print("%-12s %10d %12d" % ("TOTAL", sum(as_data.values()), sum(as_imm.values())))
    print()
    if imm_sites:
        print("=== immediate sites ===")
        for rel, i, mn, reg, k, frac in imm_sites[:200]:
            print("  %-52s 0x%06x  %s #$%s,%s   neighbourhood $55/$AA %3.0f%% %s" %
                  (rel, i, mn, k, reg, 100 * frac,
                   "<- mask DATA, not an instruction" if frac > 0.5 else ""))
        nd = sum(1 for r in imm_sites if r[5] > 0.5)
        print()
        print("  %d of %d immediate sites sit inside $55/$AA mask tables and are"
              % (nd, len(imm_sites)))
        print("  byte coincidences, leaving %d that are really instructions."
              % (len(imm_sites) - nd))
    else:
        print("=== immediate sites: none ===")
    print()
    print("=== Akiko ports as pointer loads: %d ===" % len(port_sites))
    for rel, i, v, reg in port_sites:
        print("  %-52s 0x%06x  -> %s, %s" % (rel, i, v, reg))


main()
