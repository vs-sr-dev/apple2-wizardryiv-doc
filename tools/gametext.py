#!/usr/bin/env python3
"""Pull the readable game text out of the overlays.

The text is stored uncompressed in the .code overlays as NUL-terminated,
mostly upper-case ASCII.  Runs of >= 8 characters that are at least half
letters are kept.
"""
import os, re, sys
base = '_work/files'
keep = re.compile(rb"[ -~]{8,}")
for f in sorted(os.listdir(base)):
    if not f.endswith('.code'): continue
    d = open(base + '/' + f, 'rb').read()
    out = []
    for m in keep.finditer(d):
        s = m.group().decode()
        letters = sum(c.isalpha() or c == ' ' for c in s)
        if letters >= len(s) * 0.85 and re.search(r'[A-Z]{3}', s):
            out.append((m.start(), s.strip()))
    if out:
        print('===== %s : %d strings =====' % (f, len(out)))
        for o, s in out: print('  %06x  %s' % (o, s))
