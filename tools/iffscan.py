#!/usr/bin/env python3
"""IFF ILBM/PBM chunk walk: BMHD geometry, CAMG mode, palette size, body size.

Answers the section-7 questions for a disc whose pictures are stored as ordinary
IFF rather than raw planar: how many planes, what compression, is the CAMG mode
word claiming HAM/EHB/AGA, and how many colours are actually in the CMAP.

The EHB trap in reverse also lives here: six planes with a 32-entry CMAP is
Extra-Half-Brite, and a CAMG without the EHB bit set but with 6 planes and 32
colours is still EHB in practice.

Usage:  python3 tools/iffscan.py <dir-or-file> [--chunks]
"""
import sys, os, struct, argparse, collections

CAMG_BITS = [(0x0004, "LACE"), (0x0800, "HAM"), (0x0080, "EHB"),
             (0x8000, "HIRES"), (0x0400, "DUALPF"), (0x0200, "COLOR"),
             (0x0100, "GAUD"), (0x0040, "SPRITES"), (0x0020, "VP_HIDE")]
COMP = {0: "none", 1: "ByteRun1"}


def chunks(d, o, end):
    while o + 8 <= end:
        cid = d[o:o + 4]
        sz = struct.unpack_from(">I", d, o + 4)[0]
        yield cid, o + 8, sz
        o += 8 + sz + (sz & 1)


def scan(path):
    d = open(path, "rb").read()
    if d[:4] != b"FORM":
        return None
    total = struct.unpack_from(">I", d, 4)[0]
    kind = d[8:12].decode("latin-1")
    info = dict(file=os.path.basename(path), size=len(d), form=kind,
                declared=total + 8, ncmap=0, body=0, camg=None, bmhd=None,
                chunks=[])
    for cid, o, sz in chunks(d, 12, min(len(d), total + 8)):
        info["chunks"].append((cid.decode("latin-1"), sz))
        if cid == b"BMHD":
            w, h, x, y, planes, mask, comp, pad, tr, xa, ya, pw, ph = \
                struct.unpack_from(">HHhhBBBBHBBhh", d, o)
            info["bmhd"] = dict(w=w, h=h, planes=planes, mask=mask, comp=comp,
                                transparent=tr, aspect=(xa, ya), page=(pw, ph))
        elif cid == b"CMAP":
            info["ncmap"] = sz // 3
        elif cid == b"CAMG":
            info["camg"] = struct.unpack_from(">I", d, o)[0]
        elif cid == b"BODY":
            info["body"] = sz
    return info


def camgstr(v):
    if v is None:
        return "-"
    return "$%08X %s" % (v, ",".join(n for b, n in CAMG_BITS if v & b) or "plain")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--chunks", action="store_true")
    a = ap.parse_args()
    paths = []
    if os.path.isdir(a.src):
        for dp, dn, fn in os.walk(a.src):
            for f in sorted(fn):
                paths.append(os.path.join(dp, f))
    else:
        paths = [a.src]

    rows = []
    for p in paths:
        try:
            i = scan(p)
        except Exception:
            continue
        if i:
            rows.append(i)

    print("%-16s %6s %5s %4s %2s %-9s %6s %8s  %s"
          % ("file", "size", "wxh", "", "bp", "compress", "colours", "body", "CAMG"))
    geom = collections.Counter()
    for i in sorted(rows, key=lambda r: r["file"]):
        b = i["bmhd"] or {}
        g = "%dx%d" % (b.get("w", 0), b.get("h", 0))
        geom[(g, b.get("planes"), i["ncmap"], camgstr(i["camg"]))] += 1
        print("%-16s %6d %9s %2d %-9s %6d %8d  %s"
              % (i["file"], i["size"], g, b.get("planes", 0),
                 COMP.get(b.get("comp"), "?%d" % b.get("comp", -1)),
                 i["ncmap"], i["body"], camgstr(i["camg"])))
        if a.chunks:
            print("      chunks: %s" % ", ".join("%s(%d)" % c for c in i["chunks"]))
        if i["declared"] != i["size"]:
            print("      ! FORM declares %d bytes, file is %d" % (i["declared"], i["size"]))

    print()
    print("%d IFF files.  distinct (geometry, planes, colours, CAMG):" % len(rows))
    for k, n in geom.most_common():
        print("   %-12s %d planes, %3d colours, %-28s x%d" % (k[0], k[1] or 0, k[2], k[3], n))


if __name__ == "__main__":
    main()
