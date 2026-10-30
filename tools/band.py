#!/usr/bin/env python3
"""The three figures: bytes on disc, bytes resident, bytes used.

on disc   the file's size in the ISO 9660 volume
resident  the size after unpacking every container at every depth.  A file
          that is one stream contributes its unpacked size; a file that is a
          concatenation of streams and raw gaps contributes the sum of the
          unpacked outputs plus the gaps; a stream whose *output* is itself a
          concatenation recurses.  Depth is reported.
used      resident bytes up to and including the last non-zero byte of each
          resident object.  The gap between resident and used is the slack.

Files are attributed to a title from their top-level directory so the game
can be measured apart from the two demos and the system files.

Usage: python3 tools/band.py <extracted-dir> [--maxdepth N] [--per-file]
"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from speris_imp import Decruncher

MAXDEPTH = 6


def imploder_at(data, off):
    if off + 12 > len(data):
        return None
    if bytes(data[off:off + 4]) not in (b"IMP!", b"ATN!"):
        return None
    orig, packed = struct.unpack_from(">II", data, off + 4)
    if orig == 0 or packed == 0 or orig > 32 << 20 or packed > 32 << 20:
        return None
    end = off + 12 + packed + 38
    if end > len(data):
        return None
    try:
        d = Decruncher(bytes(data[off:end]))
        out = d.run()
    except Exception:
        return None
    if out is None or len(out) != orig:
        return None
    return (end - off, out)


def expand(data, depth, stats):
    """Return the resident byte count of `data` once every container in it is
    unpacked.  Records the deepest level reached and the gap bytes."""
    if depth > MAXDEPTH:
        stats["clipped"] += 1
        return len(data), [data]
    total = 0
    pieces = []
    i = 0
    n = len(data)
    last = 0
    found = False
    while i < n - 12:
        if bytes(data[i:i + 4]) in (b"IMP!", b"ATN!"):
            r = imploder_at(data, i)
            if r:
                length, out = r
                found = True
                stats["depth"] = max(stats["depth"], depth + 1)
                stats["streams"] += 1
                stats["by_depth"][depth + 1] = stats["by_depth"].get(depth + 1, 0) + 1
                gap = data[last:i]
                if gap:
                    stats["gap_bytes"] += len(gap)
                    stats["gaps"] += 1
                    total += len(gap)
                    pieces.append(bytes(gap))
                sub, subp = expand(out, depth + 1, stats)
                total += sub
                pieces.extend(subp)
                i += length
                last = i
                continue
        i += 1
    if not found:
        return len(data), [bytes(data)]
    tailgap = data[last:]
    if tailgap:
        stats["gap_bytes"] += len(tailgap)
        stats["gaps"] += 1
        total += len(tailgap)
        pieces.append(bytes(tailgap))
    return total, pieces


def used_bytes(b):
    i = len(b)
    while i > 0 and b[i - 1] == 0:
        i -= 1
    return i


def title_of(rel):
    top = rel.strip("/").split("/")[0]
    if top in ("SuperFrog", "SuperFrog.info"):
        return "Superfrog"
    if top in ("SuperStardust", "SuperStardust.info"):
        return "Super Stardust (demo)"
    if top in ("Pool", "Pool.info"):
        return "Arcade Pool (demo)"
    if top in ("c", "s", "libs", "devs", "fonts", "Disk.info"):
        return "system / shell"
    return "system / shell"


def main():
    global MAXDEPTH
    root = sys.argv[1]
    if "--maxdepth" in sys.argv:
        MAXDEPTH = int(sys.argv[sys.argv.index("--maxdepth") + 1])
    perfile = "--per-file" in sys.argv

    stats = dict(depth=0, streams=0, gaps=0, gap_bytes=0, clipped=0, by_depth={})
    tot = {}
    rows = []
    for dp, dn, fn in os.walk(root):
        for f in sorted(fn):
            p = os.path.join(dp, f)
            d = open(p, "rb").read()
            rel = p[len(root):].replace(os.sep, "/")
            st = dict(depth=0, streams=0, gaps=0, gap_bytes=0, clipped=0, by_depth={})
            res, pieces = expand(d, 0, st)
            use = sum(used_bytes(x) for x in pieces)
            t = title_of(rel)
            tot.setdefault(t, [0, 0, 0, 0])
            tot[t][0] += len(d)
            tot[t][1] += res
            tot[t][2] += use
            tot[t][3] += 1
            rows.append((rel, len(d), res, use, st["streams"], st["depth"]))
            for k in ("streams", "gaps", "gap_bytes", "clipped"):
                stats[k] += st[k]
            stats["depth"] = max(stats["depth"], st["depth"])
            for k, v in st["by_depth"].items():
                stats["by_depth"][k] = stats["by_depth"].get(k, 0) + v

    if perfile:
        print("%-56s %9s %10s %10s %5s %5s %7s" %
              ("file", "on disc", "resident", "used", "strm", "dpth", "slack"))
        for rel, n, res, use, s, dep in sorted(rows, key=lambda r: -r[2]):
            sl = 100.0 * (res - use) / res if res else 0
            print("%-56s %9d %10d %10d %5d %5d %6.2f%%" % (rel, n, res, use, s, dep, sl))
        print()

    print("=== by title ===")
    print("%-24s %5s %10s %11s %11s %7s %7s" %
          ("title", "files", "on disc", "resident", "used", "expand", "slack"))
    gd = gr = gu = 0
    for t in sorted(tot):
        n, res, use, cnt = tot[t]
        gd += n; gr += res; gu += use
        print("%-24s %5d %10d %11d %11d %6.2fx %6.3f%%" %
              (t, cnt, n, res, use, res / n if n else 0,
               100.0 * (res - use) / res if res else 0))
    print("%-24s %5s %10d %11d %11d %6.2fx %6.3f%%" %
          ("TOTAL", "", gd, gr, gu, gr / gd, 100.0 * (gr - gu) / gr))
    print()
    print("resident MB (10^6): %.2f    MiB: %.2f" % (gr / 1e6, gr / 1048576.0))
    print()
    print("=== containers ===")
    print("  validated streams : %d" % stats["streams"])
    print("  deepest nesting   : %d" % stats["depth"])
    for k in sorted(stats["by_depth"]):
        print("    depth %d: %d streams" % (k, stats["by_depth"][k]))
    print("  raw gaps between/around streams: %d runs, %d bytes" %
          (stats["gaps"], stats["gap_bytes"]))
    print("  clipped at maxdepth: %d" % stats["clipped"])
    print()
    print("=== largest slack, per file ===")
    for rel, n, res, use, s, dep in sorted(rows, key=lambda r: -(r[2] - r[3]))[:15]:
        if res == use:
            break
        print("  %-56s resident %9d used %9d  slack %8d  %6.2f%%" %
              (rel, res, use, res - use, 100.0 * (res - use) / res))


main()
