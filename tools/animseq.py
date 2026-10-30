#!/usr/bin/env python3
"""Segment /cbmbuild into its individual movies.

Longword 16 of each frame header carries the frame index within the current
sequence in its high word; it restarts at zero when a new movie begins.
Longword 15 is (stream id << 16) | chunk count.  Raw blocks between frames --
the ten runs that carry no ANIM header -- are reported too.
"""
import struct, sys, json
f = open('_work/files/cbmbuild', 'rb'); size = f.seek(0, 2)
o = 0; seqs = []; cur = None; raws = []
while o < size:
    f.seek(o); h = f.read(0x44)
    if h[:4] != b'ANIM':
        blob = h + f.read(1 << 22)
        k = blob.find(b'ANIM', 4)
        if k < 0: break
        raws.append((o, k)); o += k; continue
    w = struct.unpack('>17I', h)
    idx = w[16] >> 16; stream = w[15] >> 16
    if cur is None or idx == 0:
        cur = {'start': o, 'frames': 0, 'bytes': 0, 'stream': stream}
        seqs.append(cur)
    p = o + 0x44; chunks = 0
    while True:
        f.seek(p); ch = f.read(20)
        if len(ch) < 20 or ch[:4] == b'ANIM' or not all(65 <= c <= 90 for c in ch[:4]): break
        p += 20 + struct.unpack('>I', ch[4:8])[0]; chunks += 1
    cur['frames'] += 1; cur['bytes'] += p - o
    cur['end'] = p
    o = p
print('%d movies, %d raw blocks' % (len(seqs), len(raws)))
print('%3s %12s %12s %7s %8s %6s' % ('#', 'start', 'bytes', 'frames', 'avg/frm', 'strm'))
for i, s in enumerate(seqs):
    print('%3d 0x%010x %12d %7d %8d %6d' %
          (i, s['start'], s['bytes'], s['frames'], s['bytes'] // s['frames'], s['stream']))
print('--- raw (non-ANIM) blocks ---')
tot = 0
for a, n in raws:
    print('0x%010x  %8d bytes' % (a, n)); tot += n
print('total raw %d bytes (%.3f %% of the file)' % (tot, 100 * tot / size))
print('sum of movie bytes %d (%.3f %%)' % (sum(s['bytes'] for s in seqs),
      100 * sum(s['bytes'] for s in seqs) / size))
json.dump(seqs, open('_work/movies.json', 'w'))
