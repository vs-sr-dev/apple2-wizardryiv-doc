#!/usr/bin/env python3
"""Full structural scan of /cbmbuild.

The file is a flat sequence of frames.  Each frame is

    'ANIM'  ULONG 0  ULONG 0
    ULONG[11]   sizes of the next eleven frames (look-ahead for the CD reader)
    ULONG ?  ULONG ?  ULONG 0          -- 0x44 bytes in total
    then chunks:  id(4)  ULONG len  12 bytes of chunk parameters  len bytes

Reports the frame count, the chunk vocabulary, and the size distribution.
"""
import sys, struct, collections, json

path = sys.argv[1] if len(sys.argv) > 1 else '_work/files/cbmbuild'
f = open(path, 'rb'); size = f.seek(0, 2)
o = 0
frames = 0
resync = []
kinds = collections.Counter(); bytes_by = collections.Counter()
percombo = collections.Counter()
framesizes = []
segstarts = []
first = []
while o < size:
    f.seek(o); h = f.read(0x44)
    if h[:4] != b'ANIM':
        # resynchronise: scan forward for the next frame header
        f.seek(o); blob = f.read(1 << 22)
        k = blob.find(b'ANIM', 4)
        if k < 0:
            print('!! lost sync at 0x%x, no further ANIM within 4 MB' % o); break
        resync.append((o, o + k)); o += k; continue
    look = struct.unpack('>11I', h[12:56])
    tail = struct.unpack('>3I', h[56:68])
    p = o + 0x44
    combo = []
    while True:
        f.seek(p); ch = f.read(20)
        if len(ch) < 20: break
        cid = ch[:4]
        if cid == b'ANIM' or not all(65 <= c <= 90 for c in cid): break
        ln = struct.unpack('>I', ch[4:8])[0]
        kinds[cid] += 1; bytes_by[cid] += ln
        combo.append(cid.decode())
        if frames < 3: first.append((p, cid.decode(), ln, ch[8:20].hex(' ')))
        p += 20 + ln
    percombo['+'.join(combo)] += 1
    framesizes.append(p - o)
    if frames < 3: segstarts.append((o, look, tail))
    frames += 1
    o = p
print('file %d bytes, %d frames, ended at 0x%x' % (size, frames, o))
print('resyncs: %d %s' % (len(resync), [(hex(a),hex(b)) for a,b in resync[:8]]))
print('--- first frames ---')
for s, look, tail in segstarts:
    print('0x%x look=%s tail=%s' % (s, [hex(x) for x in look], [hex(x) for x in tail]))
for r in first: print('   0x%09x %s %8d  %s' % r)
print('--- chunk vocabulary ---')
for k, v in kinds.most_common():
    print('%s  x%-8d %13d bytes  avg %7d' % (k.decode(), v, bytes_by[k], bytes_by[k] // v))
print('--- frame layouts ---')
for k, v in percombo.most_common(15):
    print('x%-8d %s' % (v, k))
fs = sorted(framesizes)
print('frame size: min %d  med %d  max %d  total %d' %
      (fs[0], fs[len(fs)//2], fs[-1], sum(fs)))
json.dump({'frames': frames, 'framesizes': framesizes}, open('_work/animframes.json','w'))
