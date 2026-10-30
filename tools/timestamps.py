#!/usr/bin/env python3
"""Sort the directory by timestamp and print it as a build log (checklist 3)."""
import json, sys, os
t = json.load(open('_work/tree.json'))
p = t['pvd']
print('PVD created   %s' % p['created'][:14])
print('root record   %s' % p['root_date'])
print()
rows = sorted(t['records'], key=lambda r: (r['date'], r['path']))
print('%-22s %10s  %s' % ('date/time', 'size', 'file'))
prev = None
for r in rows:
    gap = ''
    if prev and r['date'][:10] == prev[:10]:
        a = [int(x) for x in prev[11:19].split(':')]
        b = [int(x) for x in r['date'][11:19].split(':')]
        d = (b[0]*3600+b[1]*60+b[2]) - (a[0]*3600+a[1]*60+a[2])
        if d: gap = '  +%ds' % d
    print('%-22s %10d  %s%s%s' % (r['date'][:19], r['size'], r['path'],
                                  '/' if r['dir'] else '', gap))
    prev = r['date']
