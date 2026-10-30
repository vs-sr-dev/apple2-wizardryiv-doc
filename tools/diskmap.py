"""Sector map of the data track: what the file system claims, and what it
does not.  Built against the volume size the PVD declares, not the image."""
import sys, struct
sys.path.insert(0, 'tools')
from isofs import Iso
iso = Iso(sys.argv[1])
n = iso.vol_size
used = [None]*n
def mark(a, b, what):
    for s in range(a, min(b, n)):
        used[s] = what
mark(0, 16, 'system area')
mark(16, 19, 'volume descriptors')
mark(19, 21, 'path tables')
mark(struct.unpack_from('<I', iso.root_rec, 2)[0], struct.unpack_from('<I', iso.root_rec, 2)[0]+1, 'root directory')
for e in iso.walk():
    mark(e.lba, e.lba + (e.size + 2047)//2048, e.path)
print('declared volume: %d sectors; image: %d sectors (%d beyond)' % (n, iso.nsec, iso.nsec-n))
runs, s = [], 0
while s < n:
    t = s
    while t < n and (used[t] is None) == (used[s] is None): t += 1
    if used[s] is None: runs.append((s, t-s))
    s = t
tot = sum(r[1] for r in runs)
print('unclaimed inside the declared volume: %d sectors in %d runs' % (tot, len(runs)))
d = iso.data
for a, ln in runs:
    blk = d[a*2048:(a+ln)*2048]
    nz = sum(1 for b in blk if b)
    print('   LBA %5d..%-5d  %4d sectors  %d non-zero bytes%s'
          % (a, a+ln-1, ln, nz, '  <- all zero' if nz == 0 else ''))
print()
tail = d[n*2048:]
print('beyond the declared volume: %d bytes, %d non-zero' % (len(tail), sum(1 for b in tail if b)))
