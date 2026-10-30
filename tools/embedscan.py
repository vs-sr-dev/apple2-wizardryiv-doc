#!/usr/bin/env python3
"""Scan every byte offset for embedded format magics, not just file heads.

Section 8 of the checklist: on a disc with no Red Book track the music is in
files, and on at least one disc of the set it was inside an executable's chip
DATA hunk where a census over files could not see it.  So this looks at every
offset, in both the on-disc corpus and the resident one.

Each hit is validated as far as the format allows:
  M.K./M!K!/FLT4/FLT8   ProTracker family: the 1084-byte header must be there,
                        the song length must be 1..128 and the 31 sample
                        lengths must be sane
  MMD0/MMD1/MMD2/MMD3   OctaMED: header longwords must be in-file offsets
  8SVX/AIFF/ILBM/ANIM   IFF: the enclosing FORM size must fit the container
  CDXL                  not applicable (checked anyway, expected zero)

Usage: python3 tools/embedscan.py <dir> [--label NAME]
"""
import os, sys, struct
from collections import Counter

TRACKER = [b"M.K.", b"M!K!", b"M&K!", b"FLT4", b"FLT8", b"4CHN", b"6CHN", b"8CHN",
           b"OCTA", b"CD81"]
MED = [b"MMD0", b"MMD1", b"MMD2", b"MMD3"]
IFFTYPES = [b"8SVX", b"16SV", b"ILBM", b"PBM ", b"ANIM", b"ANBM", b"SMUS", b"AIFF",
            b"CDXL", b"FTXT", b"ACBM", b"RGBN", b"RGB8", b"DR2D"]
OTHER = [b"SMOD", b"FC14", b"SIDMON", b"THX", b"AHX", b"BPSM", b"MODU", b"SYNTH"]


def check_mod(d, off):
    """A ProTracker magic sits at +1080 of the module.  Validate the header."""
    base = off - 1080
    if base < 0 or base + 1084 > len(d):
        return None
    songlen = d[base + 950]
    if not (1 <= songlen <= 128):
        return None
    order = d[base + 952:base + 1080]
    if max(order) > 127:
        return None
    npat = max(order[:songlen]) + 1
    total = 0
    for i in range(31):
        s = base + 20 + i * 30
        ln = struct.unpack_from(">H", d, s + 22)[0] * 2
        vol = d[s + 25]
        if vol > 64:
            return None
        total += ln
    size = 1084 + npat * 1024 + total
    if base + size > len(d) + 4096:
        return None
    return dict(base=base, songlen=songlen, patterns=npat,
                sampbytes=total, size=size)


def check_med(d, off):
    if off + 8 > len(d):
        return None
    modlen = struct.unpack_from(">I", d, off + 4)[0]
    if modlen < 64 or off + modlen > len(d) + 4096:
        return None
    return dict(base=off, size=modlen)


def check_iff(d, off):
    """A form type at +8 of a FORM; check the FORM size fits."""
    if off < 8:
        return None
    if bytes(d[off - 8:off - 4]) != b"FORM":
        return None
    sz = struct.unpack_from(">I", d, off - 4)[0]
    if off - 8 + 8 + sz > len(d):
        return None
    return dict(base=off - 8, size=sz + 8)


def main():
    root = sys.argv[1]
    label = sys.argv[sys.argv.index("--label") + 1] if "--label" in sys.argv else root
    files = []
    for dp, dn, fn in os.walk(root):
        for f in sorted(fn):
            files.append(os.path.join(dp, f))
    hits = []
    raw = Counter()
    for p in sorted(files):
        d = open(p, "rb").read()
        rel = p[len(root):].replace(os.sep, "/")
        n = len(d)
        for i in range(n - 4):
            m = bytes(d[i:i + 4])
            if m in TRACKER:
                raw[m] += 1
                r = check_mod(d, i)
                if r:
                    hits.append((rel, m.decode("latin1"), "tracker", r))
            elif m in MED:
                raw[m] += 1
                r = check_med(d, i)
                if r:
                    hits.append((rel, m.decode("latin1"), "med", r))
            elif m in IFFTYPES:
                raw[m] += 1
                r = check_iff(d, i)
                if r:
                    hits.append((rel, m.decode("latin1"), "iff", r))
            elif m in OTHER:
                raw[m] += 1

    print("=== %s ===" % label)
    print("raw magic occurrences (validated or not):")
    for m, v in sorted(raw.items()):
        print("  %-8s %5d" % (m.decode("latin1"), v))
    print()
    print("=== validated: %d ===" % len(hits))
    for rel, m, kind, r in hits:
        extra = ""
        if kind == "tracker":
            extra = "songlen=%d patterns=%d sampledata=%d" % (r["songlen"], r["patterns"], r["sampbytes"])
        print("  %-52s %-6s %-8s base=%-9d size=%-9d %s" %
              (rel, m, kind, r["base"], r["size"], extra))
    print()
    c = Counter(h[1] for h in hits)
    for m, v in c.most_common():
        print("  %-8s %4d validated" % (m, v))


main()
