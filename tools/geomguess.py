#!/usr/bin/env python3
"""Recover the row stride of a planar bitmap by minimising row-to-row change.

None of the graphics resources on this disc stores its geometry; the copper
list gives the display 40 bytes per row and four interleaved planes per
playfield, but a resource bank need not match the display.  This tool scores
every candidate stride from 2 to 256 bytes by the mean absolute difference
between vertically adjacent bytes: a bitmap read at its true stride has
strongly correlated neighbouring rows, and any other stride shears the image
and destroys that correlation.

The score is reported for the best candidates so the reader can see how
sharp the minimum is rather than taking a single number on trust.

    python3 tools/geomguess.py FILE [--off 0] [--len N] [--top 8]
"""
import sys, argparse


def score(d, stride):
    n = (len(d) // stride) * stride
    if n < stride * 8:
        return None
    tot = 0
    cnt = 0
    for i in range(stride, min(n, stride * 400)):
        tot += abs(d[i] - d[i - stride])
        cnt += 1
    return tot / float(cnt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--off", type=lambda s: int(s, 0), default=0)
    ap.add_argument("--len", type=lambda s: int(s, 0))
    ap.add_argument("--top", type=int, default=8)
    a = ap.parse_args()
    d = open(a.file, 'rb').read()[a.off:]
    if a.len:
        d = d[:a.len]
    res = []
    for s in range(2, 257, 2):
        v = score(d, s)
        if v is not None:
            res.append((v, s))
    res.sort()
    base = sum(v for v, _ in res) / len(res)
    print("### %s  off=0x%x len=%d   mean score over all strides %.2f"
          % (a.file, a.off, len(d), base))
    for v, s in res[:a.top]:
        print("    stride %3d bytes  (%4d px 1bpp)  score %6.2f   %.0f%% of mean"
              % (s, s * 8, v, 100.0 * v / base))


main()
