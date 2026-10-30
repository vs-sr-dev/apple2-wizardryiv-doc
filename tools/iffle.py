#!/usr/bin/env python3
"""The little-endian IFF variant used by the .SCN / .WRL / .SHP family.

IFF is defined big-endian.  The front-end's screen, world and shape files start
with a correct `FORM` tag and a correct form type, but every chunk size in them
is stored little-endian, which is why a standard IFF reader sees a 3.4 GB FORM
in a 3 KB file.  This tool reads them the way the game must and checks that the
chunk walk lands exactly on the end of the file, which is the proof that the
byte order is the only difference.

Usage:  python3 tools/iffle.py <dir-or-file> [--areas]
"""
import sys, os, struct, argparse, collections


def walk(d, little):
    """Walk chunks from offset 12; return (chunks, end_offset) or (None, None)."""
    u = "<I" if little else ">I"
    total = struct.unpack_from(u, d, 4)[0]
    out = []
    o = 12
    end = min(len(d), total + 8)
    while o + 8 <= end:
        cid = d[o:o + 4]
        sz = struct.unpack_from(u, d, o + 4)[0]
        if sz > len(d):
            return None, None, total
        out.append((cid.decode("latin-1", "replace"), sz, o + 8))
        o += 8 + sz + (sz & 1)
    return out, o, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--areas", action="store_true")
    a = ap.parse_args()
    paths = []
    if os.path.isdir(a.src):
        for dp, dn, fn in os.walk(a.src):
            for f in sorted(fn):
                paths.append(os.path.join(dp, f))
    else:
        paths = [a.src]

    be = le = neither = notiff = 0
    forms = collections.Counter()
    chunkcount = collections.Counter()
    print("%-16s %7s %-6s %-9s %8s %8s  %s"
          % ("file", "size", "form", "byteorder", "FORM sz", "walk end", "chunks"))
    for p in paths:
        d = open(p, "rb").read()
        if len(d) < 12 or d[:4] != b"FORM":
            notiff += 1
            continue
        form = d[8:12].decode("latin-1", "replace")
        forms[form] += 1
        cb, endb, totb = walk(d, False)
        cl, endl, totl = walk(d, True)
        # accept when the walk ends within one pad/terminator byte of the file end
        okb = cb is not None and endb is not None and 0 <= len(d) - endb <= 1
        okl = cl is not None and endl is not None and 0 <= len(d) - endl <= 1
        order = "big" if okb else ("little" if okl else "neither")
        if okb:
            be += 1; ch = cb
        elif okl:
            le += 1; ch = cl
        else:
            neither += 1; ch = cb or cl or []
        for c in ch:
            chunkcount[(form, c[0])] += 1
        print("%-16s %7d %-6s %-9s %8d %8s  %s"
              % (os.path.basename(p), len(d), form, order,
                 totb if okb else totl,
                 endb if okb else (endl if okl else "-"),
                 ",".join(c[0] for c in ch[:8]) + ("..." if len(ch) > 8 else "")))
        if a.areas and okl:
            for cid, sz, off in ch:
                if cid == "AREA":
                    vals = struct.unpack_from(">%dH" % (sz // 2), d, off)
                    print("      AREA(%d) %s" % (sz, " ".join("%d" % v for v in vals)))

    print()
    print("IFF files %d : big-endian %d, little-endian %d, neither %d (non-IFF %d)"
          % (be + le + neither, be, le, neither, notiff))
    print("form types: %s" % ", ".join("%s x%d" % kv for kv in forms.most_common()))
    print("chunks by form:")
    for (f, c), n in chunkcount.most_common(24):
        print("   %-6s %-6s x%d" % (f, c, n))


if __name__ == "__main__":
    main()
