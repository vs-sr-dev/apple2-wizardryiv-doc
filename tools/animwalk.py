#!/usr/bin/env python3
"""Walk the chunk stream of /cbmbuild.

Header:  'ANIM' then two zero longwords, eleven longwords of per-stream
maximum chunk sizes, a longword, a longword, a zero, then the chunk stream.
Each chunk is a four-character id, a big-endian ULONG payload length, twelve
bytes of chunk sub-header, and length bytes of payload: 20 + length in total.
"""
import sys, struct, collections

path = sys.argv[1] if len(sys.argv) > 1 else '_work/files/cbmbuild'
start = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x44
limit = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0
f = open(path, 'rb')
f.seek(0); hdr = f.read(0x44)
print('magic %r' % hdr[:4])
print('header longwords:', ' '.join('%08x' % v for v in struct.unpack('>16I', hdr[4:0x44])))
o = start
n = 0
kinds = collections.Counter(); sizes = collections.Counter()
order = []
while True:
    f.seek(o); h = f.read(8)
    if len(h) < 8: break
    cid, ln = h[:4], struct.unpack('>I', h[4:])[0]
    sub = f.read(12)
    if not all(32 <= c < 127 for c in cid):
        print('!! non-ascii id at 0x%x: %s' % (o, h.hex(' '))); break
    kinds[cid] += 1; sizes[cid] += ln
    if n < 40 or (limit and n < limit):
        order.append((o, cid.decode(), ln, sub.hex(' ')))
    n += 1
    o += 20 + ln
    if limit and n >= limit: break
for oo, c, l, sb in order:
    print('0x%09x  %s  %8d  %s' % (oo, c, l, sb))
print('--- %d chunks ---' % n)
for k, v in kinds.most_common():
    print('%s  x%-8d %14d bytes  avg %d' % (k.decode(), v, sizes[k], sizes[k] // v))
