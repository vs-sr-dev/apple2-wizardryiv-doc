#!/usr/bin/env python3
"""Byte autocorrelation, to find the row pitch of a headerless bitmap.

For each candidate stride s, the score is the fraction of sampled positions
where `d[i] == d[i+s]`.  A real bitmap gives a sharp peak at its pitch and a
harmonic series above it; section 7 of the platform notes says to scan wide and
read the harmonics rather than taking the first peak.

    python tools/stride.py <file> [--max 1400] [--top 20] [--off N]
"""
import sys
import numpy as np


def main():
    path = sys.argv[1]
    mx = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else 1400
    top = int(sys.argv[sys.argv.index('--top') + 1]) if '--top' in sys.argv else 20
    off = int(sys.argv[sys.argv.index('--off') + 1]) if '--off' in sys.argv else 0
    d = np.frombuffer(open(path, 'rb').read()[off:], dtype=np.uint8)
    n = min(len(d), 200000)
    d = d[:n]
    scores = []
    for s in range(1, min(mx, n // 2)):
        a = d[:n - s]
        b = d[s:]
        scores.append((float((a == b).mean()), s))
    scores.sort(reverse=True)
    print("%s: %d bytes" % (path, len(d)))
    for sc, s in scores[:top]:
        print("   stride %5d  %.4f" % (s, sc))


if __name__ == '__main__':
    main()
