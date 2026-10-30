#!/usr/bin/env python3
"""Directory timestamps in write order, with the gaps between them.

Section 8 of the platform notes: sort the directory by timestamp before reading
a single file.  The relative order is a real write log even when the absolute
clock is wrong, so the gaps are printed next to the entries.

Counts the two MS-DOS zero epochs (1980 = FAT day zero, 1978) separately,
because open item 24 asks whether a DOS-first publisher shows more of them.

Usage:  python3 tools/timeline.py <iso.json from isodump.py>
"""
import sys, json, collections, datetime


def parse(s):
    if not s:
        return None
    return datetime.datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")


def main():
    j = json.load(open(sys.argv[1]))
    ents = []
    for f in j.get("files", []):
        t = parse(f.get("date"))
        if t:
            ents.append((t, f["size"], f["path"], "file"))
    for d in j.get("dirrecs", []):
        t = parse(d.get("date"))
        if t:
            ents.append((t, 0, d["path"], "dir"))
    ents.sort()

    print("%-21s %5s %10s  %s" % ("timestamp", "gap", "size", "path"))
    prev = None
    for t, sz, p, k in ents:
        gap = "" if prev is None else str(t - prev)
        print("%-21s %5s %10d  %s%s" % (t.isoformat(sep=" "), gap, sz, p, "/" if k == "dir" else ""))
        prev = t

    print()
    years = collections.Counter(t.year for t, _s, _p, _k in ents)
    print("by year: %s" % ", ".join("%d x%d" % kv for kv in sorted(years.items())))
    for epoch in (1978, 1980):
        g = [e for e in ents if e[0].year == epoch]
        if g:
            print("epoch %d: %d entries, %s .. %s (span %s)"
                  % (epoch, len(g), g[0][0], g[-1][0], g[-1][0] - g[0][0]))
        else:
            print("epoch %d: none" % epoch)
    days = collections.Counter(t.date() for t, _s, _p, _k in ents)
    print()
    print("distinct calendar days: %d" % len(days))
    for d in sorted(days):
        print("   %s  x%d" % (d, days[d]))
    pvd = j.get("pvd", {}).get("creation")
    if pvd:
        print()
        print("PVD creation      %s" % pvd)
        print("newest file       %s  (PVD is %s later)"
              % (ents[-1][0], parse(pvd[:19].replace("-", "-")) - ents[-1][0]
                 if parse(pvd[:19]) else "?"))


if __name__ == "__main__":
    main()
