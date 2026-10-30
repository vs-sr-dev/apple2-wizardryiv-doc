#!/usr/bin/env python3
"""Read the header of the 'PaCK' container found in /SuperStardust/CRM.

Layout deduced from the disc, not from any format description:

    +0  char[4]  'PaCK'
    +4  UWORD    0            (always zero on this disc)
    +6  ULONG    unpacked size
    +10 ULONG    packed size
    +14 ...      packed bytes, exactly `packed` of them

The test is that 14 + packed == the file size on every file, and that the
declared unpacked size equals the size of the same-named file in the sibling
RAW/ or AGARAW/ directory where one exists.

Usage: python3 tools/packheader.py <dir>...
"""
import os, sys, struct


def main():
    rows = []
    for d in sys.argv[1:]:
        for dp, dn, fn in os.walk(d):
            for f in sorted(fn):
                p = os.path.join(dp, f)
                b = open(p, "rb").read()
                if b[:4] != b"PaCK":
                    continue
                w = struct.unpack_from(">H", b, 4)[0]
                unp = struct.unpack_from(">I", b, 6)[0]
                pk = struct.unpack_from(">I", b, 10)[0]
                rows.append((p, len(b), w, unp, pk))
    print("%-52s %8s %5s %9s %9s %8s %7s" %
          ("file", "size", "w@4", "unpacked", "packed", "14+pk", "ratio"))
    exact = 0
    for p, n, w, unp, pk in rows:
        fits = (14 + pk == n)
        exact += fits
        print("%-52s %8d %5d %9d %9d %8s %6.1f%%" %
              (p.replace(os.sep, "/"), n, w, unp, pk,
               "OK" if fits else "%d" % (14 + pk), 100.0 * n / unp if unp else 0))
    print()
    print("%d files, %d with 14+packed == filesize" % (len(rows), exact))
    print()
    print("=== declared unpacked size vs the same name in RAW/AGARAW ===")
    for p, n, w, unp, pk in rows:
        base = os.path.basename(p)
        for sib in ("RAW", "AGARAW"):
            cand = os.path.join(os.path.dirname(os.path.dirname(p)), sib, base)
            if os.path.exists(cand):
                sz = os.path.getsize(cand)
                print("  %-40s declared %8d   %s/%s is %8d   %s" %
                      (base, unp, sib, base, sz, "MATCH" if sz == unp else "differ"))


main()
