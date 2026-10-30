#!/usr/bin/env python3
"""Capstone M68K disassembly with branch targets recomputed from the raw bytes.

The Capstone M68K backend prints wrong-but-plausible branch displacements,
immediates and absolute addresses on this code.  This wrapper keeps the byte
column (which is the authority) and re-derives the one thing a reader needs
most -- where each Bcc/BRA/BSR/DBcc actually goes -- straight from the
encoding.  Everything else printed by Capstone must still be checked against
the bytes before it is quoted.

    python tools/dis68k.py <file> <start> <length> [--base 0x2c] [--labels]
"""
import sys, argparse
from capstone import Cs, CS_ARCH_M68K, CS_MODE_M68K_020, CS_MODE_BIG_ENDIAN


def s8(v):
    return v - 256 if v > 127 else v


def s16(v):
    return v - 65536 if v > 32767 else v


def branch_target(addr, b):
    """Return the real target of a Bcc/BRA/BSR/DBcc at addr, or None."""
    op = int.from_bytes(b[0:2], 'big')
    hi = op >> 12
    if hi == 6:                                   # Bcc.b/.w/.l, BRA, BSR
        disp = op & 0xff
        if disp == 0:
            return addr + 2 + s16(int.from_bytes(b[2:4], 'big'))
        if disp == 0xff:
            return addr + 2 + int.from_bytes(b[2:6], 'big')
        return addr + 2 + s8(disp)
    if (op & 0xf0f8) == 0x50c8:                   # DBcc
        return addr + 2 + s16(int.from_bytes(b[2:4], 'big'))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("start")
    ap.add_argument("length")
    ap.add_argument("--base", default="0")
    a = ap.parse_args()
    start = int(a.start, 0)
    length = int(a.length, 0)
    base = int(a.base, 0)
    d = open(a.file, 'rb').read()
    md = Cs(CS_ARCH_M68K, CS_MODE_M68K_020 | CS_MODE_BIG_ENDIAN)
    rows = []
    pos, end = start, start + length
    while pos < end:
        got = False
        for ins in md.disasm(d[pos:end], pos):
            rows.append((ins.address, bytes(ins.bytes), ins.mnemonic, ins.op_str))
            pos = ins.address + ins.size
            got = True
        if not got:
            rows.append((pos, d[pos:pos + 2], ".dc.w", "$%04x" % int.from_bytes(d[pos:pos + 2], 'big')))
            pos += 2
    targets = {}
    for addr, raw, mn, ops in rows:
        t = branch_target(addr, raw)
        if t is not None:
            targets[t] = True
    labels = {}
    for i, t in enumerate(sorted(targets)):
        labels[t] = "L%02d" % i
    for addr, raw, mn, ops in rows:
        t = branch_target(addr, raw)
        if t is not None:
            ops = "%s (%06x)" % (labels.get(t, "?"), t - base)
        lab = labels.get(addr, "")
        print("%-5s %06x  %-20s %-10s %s" %
              (lab + ":" if lab else "", addr - base,
               ' '.join('%02x' % b for b in raw), mn, ops))


main()
