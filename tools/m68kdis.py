#!/usr/bin/env python3
"""Disassemble a byte range of a 68k binary with Capstone, printing the raw
bytes beside every instruction and resynchronising on undecodable words.

The Capstone M68K backend prints wrong-but-plausible immediates and
displacements on this code, so the byte column is the authority: every constant
quoted in this repository's documentation was re-read from it.

    python tools/m68kdis.py <file> <start> <length> [--hunk 0x20]
"""
import sys
from capstone import Cs, CS_ARCH_M68K, CS_MODE_M68K_020, CS_MODE_BIG_ENDIAN


def main():
    path = sys.argv[1]
    start = int(sys.argv[2], 0)
    length = int(sys.argv[3], 0)
    base = 0
    if '--hunk' in sys.argv:
        base = int(sys.argv[sys.argv.index('--hunk') + 1], 0)
    d = open(path, 'rb').read()
    md = Cs(CS_ARCH_M68K, CS_MODE_M68K_020 | CS_MODE_BIG_ENDIAN)
    pos = start
    end = start + length
    while pos < end:
        got = False
        for ins in md.disasm(d[pos:end], pos):
            raw = ' '.join('%02x' % b for b in ins.bytes)
            tag = "%06x" % (ins.address - base)
            print("%s  %-26s %-10s %s" % (tag, raw, ins.mnemonic, ins.op_str))
            pos = ins.address + ins.size
            got = True
        if not got:
            print("%06x  %-26s %s" % (pos - base, d[pos:pos + 2].hex(' '), ".dc.w"))
            pos += 2


if __name__ == '__main__':
    main()
