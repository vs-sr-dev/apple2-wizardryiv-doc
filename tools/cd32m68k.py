#!/usr/bin/env python3
"""Capstone M68K disassembly with the immediates re-read from the raw bytes.

Capstone's M68K backend prints plausible but wrong constants on this code, so
every line is annotated with the raw hex; treat the hex as authoritative.
"""
import sys
from capstone import Cs, CS_ARCH_M68K, CS_MODE_M68K_000
path, off, n = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0)
base = int(sys.argv[4], 0) if len(sys.argv) > 4 else off
d = open(path, 'rb').read()[off:off + n]
md = Cs(CS_ARCH_M68K, CS_MODE_M68K_000)
for i in md.disasm(d, base):
    print('%06x  %-24s %-10s %s' % (i.address, i.bytes.hex(' '), i.mnemonic, i.op_str))
