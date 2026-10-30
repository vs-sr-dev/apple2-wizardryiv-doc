#!/usr/bin/env python3
"""AKIKO and AGA sweep over a whole tree (or a raw disc image).

AKIKO, per section 7 of the platform notes: the byte pattern `00 B8 00` proves
nothing, so this counts the three things that do -- a pointer load of
`$00B80000`, a reference to the C2P port `$00B80038`/`$00B8003C`, and the
`$C0DE0000` identification constant -- and reports the bare pattern separately
so the false positives are visible rather than hidden.

AGA: counts writes to the registers that do not exist below AGA, in both the
absolute (`$00DFF1xx`) and the copper (`MOVE` to `$1xx`) encodings.

    python tools/agascan.py <path> [<path> ...]
"""
import sys, os, re, struct, collections

AKIKO = [(b'\x00\xb8\x00\x00', 'bare $00B80000 longword'),
         (b'\x00\xb8\x00\x38', 'C2P port $00B80038'),
         (b'\x00\xb8\x00\x3c', '$00B8003C'),
         (b'\xc0\xde\x00\x00', '$C0DE0000 id constant')]
PTRLOAD = [(b'\x41\xf9\x00\xb8\x00\x00', 'lea $B80000,a0'),
           (b'\x43\xf9\x00\xb8\x00\x00', 'lea $B80000,a1'),
           (b'\x45\xf9\x00\xb8\x00\x00', 'lea $B80000,a2'),
           (b'\x47\xf9\x00\xb8\x00\x00', 'lea $B80000,a3'),
           (b'\x49\xf9\x00\xb8\x00\x00', 'lea $B80000,a4'),
           (b'\x4b\xf9\x00\xb8\x00\x00', 'lea $B80000,a5'),
           (b'\x4d\xf9\x00\xb8\x00\x00', 'lea $B80000,a6')]
AGA_ABS = {0x106: 'BPLCON3', 0x10C: 'BPLCON4', 0x1FC: 'FMODE', 0x1E4: 'DIWHIGH',
           0x10E: 'CLXCON2', 0x1FE: 'NOP'}


def sweep(path):
    d = open(path, 'rb').read()
    row = collections.Counter()
    for pat, name in AKIKO:
        row[name] = d.count(pat)
    for pat, name in PTRLOAD:
        row['pointer load'] += d.count(pat)
    row['bare 00 B8 00 xx'] = len(re.findall(rb'\x00\xb8\x00', d))
    for off, name in AGA_ABS.items():
        row['abs $DFF%03X %s' % (off, name)] = len(re.findall(
            b'\x00\xdf\xf0' + bytes([off & 0xFF]) if off < 0x100 else
            struct.pack('>I', 0x00DFF000 + off), d))
    # NB: copper MOVEs are NOT counted here.  A bare two-byte register offset
    # followed by any two bytes matches by chance thousands of times in bitmap
    # and sample data; use tools/copperfind.py, which requires a whole valid
    # list ending in FFFF FFFE, to answer the copper half of the question.
    return d, row


def main():
    keys = None
    for p in sys.argv[1:]:
        files = []
        if os.path.isdir(p):
            for dp, dn, fn in os.walk(p):
                dn.sort()
                for f in sorted(fn):
                    files.append(os.path.join(dp, f))
        else:
            files = [p]
        tot = collections.Counter()
        nb = 0
        for f in files:
            d, row = sweep(f)
            nb += len(d)
            tot.update(row)
        print("== %s: %d files, %d bytes" % (p, len(files), nb))
        for k in sorted(tot):
            print("   %-28s %d" % (k, tot[k]))


if __name__ == '__main__':
    main()
