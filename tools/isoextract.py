#!/usr/bin/env python3
"""Extract every file from the Microcosm data track into _work/files/.

Uses the record list written by tools/isolist.py.  cbmbuild (482 MB) is
extracted too; pass --skip-big to leave it alone.
"""
import sys, os, json, hashlib

SECT = 2048
root = sys.argv[1] if len(sys.argv) > 1 else '.'
skip_big = '--skip-big' in sys.argv
tree = json.load(open(os.path.join(root, '_work', 'tree.json')))
iso = os.path.join(root, tree['pvd']['image'])
out = os.path.join(root, '_work', 'files')
img = open(iso, 'rb')
rows = []
for r in sorted(tree['records'], key=lambda r: r['lba']):
    if r['dir']:
        os.makedirs(out + r['path'], exist_ok=True); continue
    name = r['path'].split(';')[0]
    dst = out + name
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if skip_big and r['size'] > 100 * 1024 * 1024:
        rows.append((name, r['size'], r['lba'], 'skipped')); continue
    img.seek(r['lba'] * SECT)
    h = hashlib.sha1(); left = r['size']
    with open(dst, 'wb') as fh:
        while left:
            n = min(left, 1 << 20)
            b = img.read(n); fh.write(b); h.update(b); left -= n
    rows.append((name, r['size'], r['lba'], h.hexdigest()))
for n, s, l, h in rows:
    print('%-28s %10d %7d %s' % (n, s, l, h))
