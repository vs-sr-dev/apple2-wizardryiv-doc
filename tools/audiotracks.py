#!/usr/bin/env python3
"""Census of the Red Book tracks beside the data track.

Reads the RIFF header of each `.wav` in the dump, converts its payload to
CD sectors (2,352 bytes each, 75 per second) and reports duration, share of
the disc, and whether any two tracks are byte-identical -- three discs in
this set ship a duplicated track and it is worth one `sha1sum` to know.

    python3 tools/audiotracks.py DIR
"""
import sys, os, glob, hashlib


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else '.'
    rows = []
    h = {}
    for p in sorted(glob.glob(os.path.join(d, '*.wav'))):
        b = open(p, 'rb').read()
        pcm = len(b) - 44
        sec = pcm // 2352
        s = hashlib.sha1(b).hexdigest()
        h.setdefault(s, []).append(os.path.basename(p))
        rows.append((os.path.basename(p), len(b), sec, sec / 75.0, s))
    tot = sum(r[2] for r in rows)
    print("%-8s %12s %9s %9s  %s" % ("track", "bytes", "sectors", "mm:ss", "sha1"))
    for i, (n, b, s, t, sh) in enumerate(rows, start=2):
        print("%-8d %12d %9d %5d:%02d  %s" % (i, b, s, int(t // 60), int(t % 60), sh[:16]))
    print()
    print("tracks              %d" % len(rows))
    print("total sectors       %d" % tot)
    print("total time          %d:%02d" % (tot // 75 // 60, (tot // 75) % 60))
    print("distinct by SHA-1   %d" % len(h))
    for k, v in h.items():
        if len(v) > 1:
            print("  identical: %s" % ", ".join(v))


main()
