#!/usr/bin/env python3
"""Second, independent geometry measure: mean |d[i] - d[i+k]| against lag k.

`geomguess.py` scores a candidate row stride by vertical correlation, which
finds the smallest repeating unit.  That is not enough on its own: on
[Superfrog] the stride minimum landed at 2 bytes, the signature of tile data,
and it took a second measure -- this one -- to separate "one tile bank" from
"five bitplanes stored as five separate sheets".  A structural minimum at lag
L says the data repeats every L bytes; a *maximum* at lag L says the data at
distance L is maximally unlike itself, which is what separated planes look
like.

Usage: python3 tools/autocorr.py <file> [--max N] [--step N] [--top N]
"""
import sys, argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file')
    ap.add_argument('--max', type=int, default=4096)
    ap.add_argument('--step', type=int, default=1)
    ap.add_argument('--top', type=int, default=12)
    ap.add_argument('--sample', type=int, default=65536)
    a = ap.parse_args()
    d = open(a.file, 'rb').read()
    n = min(len(d), a.sample)
    scores = []
    for k in range(1, min(a.max, n - 1) + 1, a.step):
        s = 0
        m = n - k
        stride = max(1, m // 4000)
        cnt = 0
        for i in range(0, m, stride):
            s += abs(d[i] - d[i + k])
            cnt += 1
        scores.append((s / cnt, k))
    mean = sum(v for v, k in scores) / len(scores)
    print("%s  %d bytes, %d lags scored, mean %.2f" %
          (a.file, len(d), len(scores), mean))
    print("  lowest (data repeats at this distance):")
    for v, k in sorted(scores)[:a.top]:
        print("    lag %6d   %7.2f   %5.1f%% of mean" % (k, v, 100 * v / mean))
    print("  highest (data is maximally unlike itself at this distance):")
    for v, k in sorted(scores)[-a.top:][::-1]:
        print("    lag %6d   %7.2f   %5.1f%% of mean" % (k, v, 100 * v / mean))


if __name__ == '__main__':
    main()
