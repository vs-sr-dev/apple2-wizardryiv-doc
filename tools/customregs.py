#!/usr/bin/env python3
"""Histogram the custom-chip registers a program actually touches.

Section 4 of the platform notes warns not to grep for the base address; this
disc is the opposite failure.  `/QuestII` loads `$DFF000` into an address
register **83 times** and then addresses every register as `d16(An)`, so a scan
for absolute `$00DFF0xx` longwords finds thirteen registers out of the sixty it
really writes.

This walks the code with Capstone, remembers which address registers currently
hold `$DFF000` (from `lea $dff000.l,An` / `movea.l #$dff000,An`), invalidates a
register when anything else is moved into it, and names every `d16(An)` access
made through a live one.  It also reports the same for `$DFF000`-relative
accesses in the copper-list builders.

    python tools/customregs.py <file> [--sites REG]
"""
import sys, collections
from capstone import Cs, CS_ARCH_M68K, CS_MODE_M68K_020, CS_MODE_BIG_ENDIAN
import struct

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scan import REG

BASE = 0xDFF000


def main():
    d = open(sys.argv[1], 'rb').read()
    want = sys.argv[sys.argv.index('--sites') + 1] if '--sites' in sys.argv else None
    md = Cs(CS_ARCH_M68K, CS_MODE_M68K_020 | CS_MODE_BIG_ENDIAN)
    md.detail = False
    live = {}
    hist = collections.Counter()
    sites = collections.defaultdict(list)
    nbase = 0
    pos = 0
    while pos < len(d):
        got = False
        for ins in md.disasm(d[pos:], pos):
            got = True
            pos = ins.address + ins.size
            b = ins.bytes
            # lea $dff000.l,An   -> 4? f9 00 df f0 00
            if len(b) >= 6 and (b[0] & 0xF1) == 0x41 and b[1] == 0xF9:
                if struct.unpack_from('>I', b, 2)[0] == BASE:
                    live[(b[0] >> 1) & 7] = True
                    nbase += 1
                    continue
            # movea.l #$dff000,An  -> 2?7c 00df f000
            if len(b) >= 6 and (b[0] & 0xF1) == 0x21 and b[1] == 0x7C:
                if struct.unpack_from('>I', b, 2)[0] == BASE:
                    live[(b[0] >> 1) & 7] = True
                    nbase += 1
                    continue
            # any other write to An kills it
            if ins.mnemonic.startswith(('movea', 'lea', 'adda', 'suba', 'movem')):
                for r in range(8):
                    if ('a%d' % r) in ins.op_str.split(',')[-1]:
                        live.pop(r, None)
            # d16(An) operand on a live base
            for part in ins.op_str.split(','):
                part = part.strip()
                if part.startswith('$') and part.endswith(')') and '(a' in part:
                    try:
                        disp = part.split('(')[0]
                        an = int(part.split('(a')[1][0])
                    except (ValueError, IndexError):
                        continue
                    if not live.get(an):
                        continue
                    neg = disp.startswith('-')
                    v = int(disp.lstrip('-$'), 16)
                    off = (-v) & 0xFFFF if neg else v
                    if off > 0x1FF:
                        continue
                    hist[off] += 1
                    if want and REG.get(off, '') == want:
                        sites[off].append(ins.address)
        if not got:
            pos += 2
    print("`lea $dff000` / `movea.l #$dff000` sites: %d" % nbase)
    print("distinct registers reached through them: %d, %d accesses" %
          (len(hist), sum(hist.values())))
    for off in sorted(hist):
        print("  $DFF%03X  %-10s x%d" % (off, REG.get(off, '?'), hist[off]))
    for off, ss in sites.items():
        print("sites for $DFF%03X: %s" % (off, ' '.join('0x%x' % a for a in ss)))


if __name__ == '__main__':
    main()
