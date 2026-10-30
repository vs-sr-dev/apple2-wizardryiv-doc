#!/usr/bin/env python3
"""Akiko scan: the CD32 chunky-to-planar port and its identification constant.

Reports, for every file given (and for a raw image), the counts that matter:

  $00B80038  the C2P data port          -- the only unambiguous reference
  $00B80000  as a pointer load          lea $B80000,An / movea.l #$B80000,An
  $C0DE0000  the Akiko identification constant
  00 B8 00 xx  the bare byte pattern    -- reported for context only; see the
               platform notes, it is ProTracker's period table most of the time

    python tools/akiko.py <file> [<file> ...]
"""
import sys, os

def scan(name, d):
    out = {}
    out['B80038'] = d.count(b'\x00\xb8\x00\x38')
    out['B8003C'] = d.count(b'\x00\xb8\x00\x3c')
    out['C0DE0000'] = d.count(b'\xc0\xde\x00\x00')
    # pointer loads: lea $B80000,An = 4?f9 00B80000 ; movea.l #$B80000,An = 2?7c 00B80000
    ptr = 0
    sites = []
    for i in range(len(d) - 6):
        if d[i+2:i+6] == b'\x00\xb8\x00\x00':
            op = int.from_bytes(d[i:i+2], 'big')
            if (op & 0xf1ff) == 0x41f9 or (op & 0xf1ff) == 0x207c:
                ptr += 1
                sites.append((i, hex(op)))
    out['ptrload'] = ptr
    bare = 0
    for i in range(len(d) - 3):
        if d[i:i+3] == b'\x00\xb8\x00':
            bare += 1
    out['bare_00B800'] = bare
    print("%-40s  B80038=%d  B8003C=%d  C0DE0000=%d  ptrload=%d  bare 00B800=%d"
          % (name, out['B80038'], out['B8003C'], out['C0DE0000'], out['ptrload'], out['bare_00B800']))
    for s in sites:
        print("       pointer load at 0x%x opcode %s" % s)
    return out

if __name__ == '__main__':
    tot = {'B80038':0,'B8003C':0,'C0DE0000':0,'ptrload':0,'bare_00B800':0}
    for p in sys.argv[1:]:
        r = scan(p, open(p,'rb').read())
        for k in tot: tot[k] += r[k]
    print("-" * 100)
    print("TOTAL  B80038=%d  B8003C=%d  C0DE0000=%d  ptrload=%d  bare 00B800=%d"
          % (tot['B80038'], tot['B8003C'], tot['C0DE0000'], tot['ptrload'], tot['bare_00B800']))
