#!/usr/bin/env python3
"""Verify the frame-header checksum that CDCODE/CDXLINT.S enforces.

The interrupt does  d0 = 'COSM'; 17 x  sub.l (a0)+,d0;  and rejects the block
unless d0 comes back zero -- i.e. the seventeen longwords of a frame header
must sum to 0x434F534D modulo 2**32.  Longword 14 is the value the packer
chose to make that true; longword 15 is the chunk count; longword 16 is the
frame index in its high word.
"""
import struct, sys
f = open(sys.argv[1] if len(sys.argv) > 1 else '_work/files/cbmbuild', 'rb')
size = f.seek(0, 2)
o = 0; n = 0; bad = 0; idxbad = 0; cnt = {}
prev = None
while o < size:
    f.seek(o); h = f.read(0x44)
    if h[:4] != b'ANIM':
        blob = h + f.read(1 << 22)
        k = blob.find(b'ANIM', 4)
        if k < 0: break
        o += k; continue
    w = struct.unpack('>17I', h)
    s = sum(w) & 0xFFFFFFFF
    if s != 0x434F534D: bad += 1
    cnt[w[15]] = cnt.get(w[15], 0) + 1
    if w[16] >> 16 != n & 0xFFFF: idxbad += 1
    p = o + 0x44
    while True:
        f.seek(p); ch = f.read(20)
        cid = ch[:4]
        if len(ch) < 20 or cid == b'ANIM' or not all(65 <= c <= 90 for c in cid): break
        p += 20 + struct.unpack('>I', ch[4:8])[0]
    n += 1; o = p
print('%d frames checked' % n)
print('headers whose 17 longwords do NOT sum to \'COSM\': %d' % bad)
print('headers whose longword 16 high word != sequential frame index: %d' % idxbad)
print('longword 15 (chunk count) distribution: %s' % cnt)
