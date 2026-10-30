#!/usr/bin/env python3
"""Census of an extracted ISO tree: size, first 16 bytes, SHA-1, and a guess
at the container form from the leading magic.

Usage:  python3 tools/magiccensus.py <extracted-dir>
"""
import os, sys, hashlib

MAGIC = [
    (b"\x00\x00\x03\xf3", "AmigaHunk executable"),
    (b"\x00\x00\x03\xe7", "AmigaHunk unit"),
    (b"FORM", "IFF"),
    (b"RNC\x01", "RNC ProPack method 1"),
    (b"RNC\x02", "RNC ProPack method 2"),
    (b"PP20", "PowerPacker 2.0"),
    (b"IMP!", "Imploder"),
    (b"ATN!", "Imploder (ATN!)"),
    (b"CrM!", "CrunchMania"),
    (b"Crm!", "CrunchMania (Crm!)"),
    (b"CD32", "CD32 tag"),
    (b"\x89PNG", "PNG"),
    (b"RIFF", "RIFF"),
]


def guess(h):
    for m, n in MAGIC:
        if h.startswith(m):
            return n
    if h[:4] == b"CDXL":
        return "CDXL"
    return ""


def main():
    root = sys.argv[1]
    rows = []
    for dp, dn, fn in os.walk(root):
        for f in fn:
            p = os.path.join(dp, f)
            sz = os.path.getsize(p)
            with open(p, "rb") as fh:
                head = fh.read(64)
            sha = hashlib.sha1()
            with open(p, "rb") as fh:
                for c in iter(lambda: fh.read(1 << 20), b""):
                    sha.update(c)
            rel = os.path.relpath(p, root)
            rel = rel.replace(os.sep, "/")
            rows.append((rel, sz, head, sha.hexdigest()))
    rows.sort(key=lambda r: -r[1])
    tot = sum(r[1] for r in rows)
    print("%d files, %d bytes total" % (len(rows), tot))
    print()
    print("%-32s %10s  %-32s %-22s %s" % ("file", "size", "first 16 bytes (hex)", "ascii", "guess"))
    for rel, sz, head, sha in rows:
        h = head[:16]
        asc = "".join(chr(c) if 32 <= c < 127 else "." for c in h)
        print("%-32s %10d  %-32s %-22s %s" % (rel, sz, h.hex(), asc, guess(head)))
    print()
    print("=== SHA-1 ===")
    for rel, sz, head, sha in sorted(rows):
        print("%s  %s" % (sha, rel))


if __name__ == "__main__":
    main()
