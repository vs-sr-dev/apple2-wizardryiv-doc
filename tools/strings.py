#!/usr/bin/env python3
"""Printable-ASCII string extractor with file offsets (no external `strings`)."""
import sys, re
def run(path, minlen=4, offsets=True):
    d = open(path, 'rb').read()
    for m in re.finditer(rb'[\x20-\x7e]{%d,}' % minlen, d):
        s = m.group().decode('ascii')
        print(("%06x  " % m.start() if offsets else "") + s)
if __name__ == '__main__':
    a = sys.argv[1:]
    n = 4
    if '-n' in a:
        i = a.index('-n'); n = int(a[i+1]); del a[i:i+2]
    run(a[0], n)
