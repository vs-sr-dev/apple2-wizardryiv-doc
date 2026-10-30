#!/usr/bin/env python3
"""Report duplication as per-file byte coverage, not as a sum of runs.

The first version printed "398 maximal runs, 1,383,881 bytes of duplicated
material" on a disc holding 1,261,776 bytes of files -- more duplication than
there are bytes.  That figure is wrong in a specific and instructive way: runs
found from different seed windows overlap, and adding their lengths counts the
same bytes many times over.  The containment filter only dropped runs fully
inside another run of the *same pair*, which is not enough.

The honest measurement is a coverage bitmap: for each file, which of its byte
offsets appear in at least one match somewhere else.  That is reported per file
and as a disc total, and the largest individual runs are still listed because
those are the ones worth naming.
"""
import io

P = 'tools/dupscan.py'
s = io.open(P, encoding='utf-8').read()

old = s[s.index("    # merge: keep only maximal runs"):]
new = '''    # ---- coverage: which bytes of each file appear in some match elsewhere
    cover = {n: bytearray(len(b)) for n, b in files}
    for L, na, oa, nb, ob in runs:
        ca, cb = cover[na], cover[nb]
        for k in range(L):
            ca[oa + k] = 1
            cb[ob + k] = 1

    print("\\n=== duplication coverage, per file ===")
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
    print("\\n  Note: a byte is counted in every file it appears in, so the")
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

    print("\\n=== largest non-overlapping runs (>= %d bytes) ===" % a.minrun)
    for L, na, oa, nb, ob in named[:20]:
        print("  %9d B  %s @0x%06x  ==  %s @0x%06x" % (L, na, oa, nb, ob))
    print("\\n  %d non-overlapping runs, %d bytes"
          % (len(named), sum(r[0] for r in named)))


if __name__ == '__main__':
    main()
'''
assert s.count("    # merge: keep only maximal runs") == 1, "merge anchor not unique"
s = s[:s.index("    # merge: keep only maximal runs")] + new
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print("patched %s" % P)
