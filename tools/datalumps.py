#!/usr/bin/env python3
"""Read the lump directory at the head of every .data overlay.

    UWORD  count       number of lumps the loader expects
    UWORD  0
    ULONG  0
    ULONG  offset[n]   offsets of the lumps, relative to byte 8; the first
                       offset is also the length of the table, so n is
                       self-describing:  n = offset[0] / 4

The high bit of an offset marks a lump the loader treats differently (all such
values are small and are not file offsets).  Lumps whose first bytes look like
a 31-sample ProTracker module are reported with their title and sample names.
"""
import os, struct, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
base = '_work/files'
def san(b):
    return ''.join(chr(c) if 32 <= c < 127 else '' for c in b)
def modnames(b):
    """If b looks like a 31-sample MOD, return (title, [sample names])."""
    if len(b) < 1084: return None
    title = b[:20].rstrip(b'\0').decode('latin-1', 'replace')
    names, ok = [], 0
    for i in range(31):
        e = b[20 + i * 30: 50 + i * 30]
        nm = e[:22].rstrip(b'\0').decode('latin-1', 'replace')
        ln = struct.unpack('>H', e[22:24])[0]
        ft, vol = e[24], e[25]
        if ft <= 15 and vol <= 64: ok += 1
        names.append((nm, ln * 2, ft, vol))
    if ok < 28: return None
    return title, names

for f in sorted(os.listdir(base)):
    if not f.endswith('.data'): continue
    d = open(base + '/' + f, 'rb').read()
    count = struct.unpack('>H', d[0:2])[0]
    first = struct.unpack('>I', d[8:12])[0]
    n = first // 4
    offs = [struct.unpack('>I', d[8 + 4 * i:12 + 4 * i])[0] for i in range(n)]
    print('=== %-16s %9d bytes   header count=%d, table entries=%d ===' %
          (f, len(d), count, n))
    for i, o in enumerate(offs):
        flag = o >> 31; a = (o & 0x7fffffff) + 8
        nxt = [(x & 0x7fffffff) + 8 for x in offs if (x & 0x7fffffff) + 8 > a]
        end = min(nxt) if nxt else len(d)
        tag = 'FLAG' if flag else '    '
        m = modnames(d[a:a + 1084 + 4]) if not flag and a < len(d) else None
        print('  %2d %s off=0x%08x len=%8d %s' %
              (i, tag, a, max(0, end - a), ('MOD "%s"' % m[0]) if m else ''))
        if m:
            for nm, ln, ft, vol in m[1]:
                if nm or ln: print('        sample %-24s %6d bytes  ft=%2d vol=%2d' % (nm, ln, ft, vol))
