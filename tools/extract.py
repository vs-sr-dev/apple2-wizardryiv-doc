"""Extract every file in the ISO 9660 volume to a directory tree.

Names keep the ISO ';1' version suffix off; directories are created as
needed.  Nothing here is committed -- the default target is _work/, which
.gitignore excludes.
"""
import os, sys
from isofs import Iso

iso = Iso(sys.argv[1])
out = sys.argv[2] if len(sys.argv) > 2 else '_work/iso'
n = 0
for e in iso.walk():
    p = os.path.join(out, e.path.lstrip('/').split(';')[0])
    if e.is_dir:
        os.makedirs(p, exist_ok=True)
        continue
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f:
        f.write(iso.read(e))
    n += 1
print('%d files -> %s' % (n, out))
