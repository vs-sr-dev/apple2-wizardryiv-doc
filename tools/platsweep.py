#!/usr/bin/env python3
"""Checklist step 15: look for traces of the game's other releases.

Microcosm shipped on Mega-CD, 3DO, PC, FM Towns and CD32.  If the CD32 build
inherited anything from another platform's tree, the cheapest place for it to
show is a volume name, an absolute path, or a platform noun left in a string.
"""
import re, os
NEEDLES = [b'3DO', b'MEGA', b'SEGA', b'TOWNS', b'MSDOS', b'IBM', b'A1200',
           b'CD32', b'CDTV', b'DH0:', b'DH1:', b'WORK:', b'RAM:', b'SYS:',
           b'df0:', b'DF0:', b'AMIGA', b'Amiga', b'PSYGNOSIS', b'Psygnosis',
           b'MICROCOSM', b'Microcosm', b'MCOSM']
base = '_work/files'
files = [f for f in sorted(os.listdir(base)) if os.path.isfile(base + '/' + f)]
print('=== platform / volume nouns ===')
for f in files:
    if f == 'cbmbuild': continue
    d = open(base + '/' + f, 'rb').read()
    hits = {w.decode(): d.count(w) for w in NEEDLES if d.count(w)}
    if hits: print('%-18s %s' % (f, hits))
print()
print('=== anything that looks like an AmigaDOS path (excluding cd0:) ===')
print('(only the executable and the .code overlays -- the .data overlays are')
print(' sampled audio and produce nothing but coincidence)')
pat = re.compile(rb'[A-Za-z0-9_.-]{2,20}:[A-Za-z0-9_./-]{0,30}')
for f in files:
    if f != 'cosm' and not f.endswith('.code'): continue
    d = open(base + '/' + f, 'rb').read()
    for m in pat.finditer(d):
        s = m.group().decode()
        if len(s) > 4 and not s.startswith('cd0:'):
            print('%-18s %06x %s' % (f, m.start(), s))
