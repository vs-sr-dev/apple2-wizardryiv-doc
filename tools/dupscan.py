#!/usr/bin/env python3
"""dupscan.py -- find byte-identical material shared between files, and inside a
single file, and report how many bytes it accounts for.

The checklist asks for duplication to be compared **by content, not by name**,
and warns that one direction of comparison is not enough.  Whole-file hashing
finds nothing on this disc: no two files are identical.  The duplication here is
*interior* -- a 94 KB run shared between two executables, and a whole packed
file that also sits inside one of them -- and only a substring search finds it.

Method: hash every WINDOW-byte window at STRIDE-byte steps of every file, group
equal hashes, then extend each candidate match in both directions to its maximal
run and merge overlapping runs.  Runs shorter than MINRUN are dropped.  A run is
only reported once per (file A, file B) pair of regions.

Usage: dupscan.py DIR [--window 256] [--stride 64] [--minrun 1024]
"""
import os, sys, argparse, hashlib
from collections import defaultdict


def load(root):
    out = []
    for dp, dn, fn in os.walk(root):
        for f in sorted(fn):
            p = os.path.join(dp, f)
            rel = '/' + os.path.relpath(p, root).replace('\\', '/')
            out.append((rel, open(p, 'rb').read()))
    return sorted(out, key=lambda x: -len(x[1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root')
    ap.add_argument('--window', type=int, default=256)
    ap.add_argument('--stride', type=int, default=64)
    ap.add_argument('--minrun', type=int, default=1024)
    a = ap.parse_args()

    files = load(a.root)
    print("%d files, %d bytes total" % (len(files), sum(len(b) for _, b in files)))

    # ---- whole-file duplicates first, the cheap direction
    byhash = defaultdict(list)
    for n, b in files:
        byhash[hashlib.sha1(b).hexdigest()].append(n)
    whole = [v for v in byhash.values() if len(v) > 1]
    print("\n=== whole-file duplicates ===")
    if whole:
        for g in whole:
            print("  %s" % " == ".join(g))
    else:
        print("  none -- no two files on this disc are byte-identical")

    # ---- interior duplication
    index = defaultdict(list)
    for fi, (n, b) in enumerate(files):
        for off in range(0, max(0, len(b) - a.window + 1), a.stride):
            h = hash(b[off:off + a.window])
            index[h].append((fi, off))

    seen = set()
    runs = []
    for h, lst in index.items():
        if len(lst) < 2:
            continue
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                fa, oa = lst[i]
                fb, ob = lst[j]
                if fa == fb and oa == ob:
                    continue
                A, B = files[fa][1], files[fb][1]
                if A[oa:oa + a.window] != B[ob:ob + a.window]:
                    continue
                # extend
                s = 0
                while oa - s > 0 and ob - s > 0 and A[oa - s - 1] == B[ob - s - 1]:
                    if fa == fb and oa - s - 1 == ob - s - 1:
                        break
                    s += 1
                e = a.window
                while oa + e < len(A) and ob + e < len(B) and A[oa + e] == B[ob + e]:
                    e += 1
                length = s + e
                if length < a.minrun:
                    continue
                key = (fa, fb, oa - s, ob - s, length)
                if key in seen:
                    continue
                seen.add(key)
                runs.append((length, files[fa][0], oa - s, files[fb][0], ob - s))

    # ---- coverage: which bytes of each file appear in some match elsewhere
    cover = {n: bytearray(len(b)) for n, b in files}
    for L, na, oa, nb, ob in runs:
        ca, cb = cover[na], cover[nb]
        for k in range(L):
            ca[oa + k] = 1
            cb[ob + k] = 1

    print("\n=== duplication coverage, per file ===")
    print("%-34s %10s %10s %7s" % ("file", "bytes", "duplicated", "share"))
    tot_b = tot_d = 0
    for n, b in files:
        d = sum(cover[n])
        tot_b += len(b)
        tot_d += d
        if d:
            print("%-34s %10d %10d %6.2f%%" % (n, len(b), d, 100.0 * d / len(b)))
    print("%-34s %10d %10d %6.2f%%" % ("TOTAL", tot_b, tot_d,
                                       100.0 * tot_d / tot_b if tot_b else 0))
    print("\n  Note: a byte is counted in every file it appears in, so the")
    print("  total is the number of bytes involved in duplication, not the")
    print("  number that could be saved by removing the copies.")

    # ---- the individual runs worth naming: longest, non-overlapping per pair
    runs.sort(key=lambda r: -r[0])
    named, used = [], {}
    for L, na, oa, nb, ob in runs:
        ka, kb = used.setdefault(na, []), used.setdefault(nb, [])
        if any(oa < e and oa + L > s2 for s2, e in ka):
            continue
        if any(ob < e and ob + L > s2 for s2, e in kb):
            continue
        ka.append((oa, oa + L))
        kb.append((ob, ob + L))
        named.append((L, na, oa, nb, ob))

    print("\n=== largest non-overlapping runs (>= %d bytes) ===" % a.minrun)
    for L, na, oa, nb, ob in named[:20]:
        print("  %9d B  %s @0x%06x  ==  %s @0x%06x" % (L, na, oa, nb, ob))
    print("\n  %d non-overlapping runs, %d bytes"
          % (len(named), sum(r[0] for r in named)))


if __name__ == '__main__':
    main()
