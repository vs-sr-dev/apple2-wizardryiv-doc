#!/usr/bin/env python3
"""Cruncher magic scan, validated by running the decompressor.

Scans every byte offset of every file (and optionally the raw image) for the
magics of the nine crunchers seen across this disc set, then *validates* each
hit by actually decoding the stream.  A hit that decodes is a stream; a hit
that does not is reported separately so a magic-shaped coincidence never gets
counted as compression.

Usage: python3 tools/packscan2.py <dir-or-file> [--depth N] [--out DIR]
"""
import os, sys, struct, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

MAGICS = [
    (b"IMP!", "Imploder"),
    (b"ATN!", "Imploder"),
    (b"RNC\x01", "RNC1"),
    (b"RNC\x02", "RNC2"),
    (b"PP20", "PP20"),
    (b"PP11", "PP11"),
    (b"CrM!", "CrunchMania"),
    (b"CrM2", "CrunchMania"),
    (b"Crm!", "CrunchMania"),
    (b"Crm2", "CrunchMania"),
    (b"PaCK", "PaCK"),
]


def try_imploder(data, off):
    """Structural + length validation, then full decode."""
    try:
        from speris_imp import Decruncher
    except Exception:
        return None
    if off + 12 > len(data):
        return None
    orig, packed = struct.unpack_from(">II", data, off + 4)
    if orig == 0 or packed == 0 or orig > 16 << 20 or packed > 16 << 20:
        return None
    # 12-byte header ('IMP!' + unpacked + packed) then packed bytes then a
    # 38-byte constant tail, so the stream is exactly packed + 50 bytes long.
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


def try_rnc(data, off, method):
    try:
        import rnc, rnc2
    except Exception:
        return None
    if off + 18 > len(data):
        return None
    unp, pk = struct.unpack_from(">II", data, off + 4)
    if unp == 0 or pk == 0 or unp > 32 << 20 or pk > 32 << 20:
        return None
    if off + 18 + pk > len(data):
        return None
    blob = bytes(data[off:off + 18 + pk])
    try:
        if method == 1:
            out = rnc.unpack(blob)
        else:
            out = rnc2.unpack(blob)
    except Exception:
        return None
    if out is None or len(out) != unp:
        return None
    return (18 + pk, out)


def try_pp20(data, off):
    try:
        import pp20
    except Exception:
        return None
    # PP20 has no declared length; the stream runs to the end of its container
    for end in (len(data),):
        try:
            out = pp20.unpack(bytes(data[off:end]))
        except Exception:
            return None
        if out:
            return (end - off, out)
    return None


def scan_file(path, data, depth, maxdepth, out_dir, results, origin):
    n = len(data)
    i = 0
    while i < n - 16:
        b4 = bytes(data[i:i + 4])
        for magic, name in MAGICS:
            if b4 != magic:
                continue
            res = None
            if name == "Imploder":
                res = try_imploder(data, i)
            elif name == "RNC1":
                res = try_rnc(data, i, 1)
            elif name == "RNC2":
                res = try_rnc(data, i, 2)
            elif name == "PP20":
                res = try_pp20(data, i)
            if res:
                length, out = res
                results.append(dict(origin=origin, off=i, magic=name, depth=depth,
                                    packed=length, unpacked=len(out), ok=True))
                if depth < maxdepth:
                    scan_file(path, out, depth + 1, maxdepth, out_dir,
                              results, origin + "!%d" % i)
                if out_dir:
                    o = os.path.join(out_dir, origin.strip("/").replace("/", "_") + "_%d.bin" % i)
                    open(o, "wb").write(out)
                i += length - 1
                break
            else:
                results.append(dict(origin=origin, off=i, magic=name, depth=depth,
                                    packed=0, unpacked=0, ok=False))
        i += 1


def main():
    target = sys.argv[1]
    maxdepth = 3
    if "--depth" in sys.argv:
        maxdepth = int(sys.argv[sys.argv.index("--depth") + 1])
    out_dir = None
    if "--out" in sys.argv:
        out_dir = sys.argv[sys.argv.index("--out") + 1]
        os.makedirs(out_dir, exist_ok=True)

    files = []
    if os.path.isdir(target):
        for dp, dn, fn in os.walk(target):
            for f in sorted(fn):
                files.append(os.path.join(dp, f))
    else:
        files = [target]

    results = []
    for p in sorted(files):
        d = open(p, "rb").read()
        rel = p[len(target):].replace(os.sep, "/") if os.path.isdir(target) else os.path.basename(p)
        scan_file(p, d, 0, maxdepth, out_dir, results, rel)

    ok = [r for r in results if r["ok"]]
    bad = [r for r in results if not r["ok"]]
    print("=== validated streams: %d ===" % len(ok))
    print("%-52s %8s %-12s %5s %10s %10s %6s" %
          ("origin", "offset", "magic", "depth", "packed", "unpacked", "ratio"))
    for r in sorted(ok, key=lambda r: (r["origin"], r["off"])):
        print("%-52s %8d %-12s %5d %10d %10d %5.1f%%" %
              (r["origin"], r["off"], r["magic"], r["depth"], r["packed"],
               r["unpacked"], 100.0 * r["packed"] / r["unpacked"]))
    print()
    from collections import Counter
    print("=== by depth ===")
    c = Counter(r["depth"] for r in ok)
    for d in sorted(c):
        sub = [r for r in ok if r["depth"] == d]
        print("  depth %d: %4d streams  %10d packed -> %10d unpacked  %.2fx" %
              (d, len(sub), sum(r["packed"] for r in sub), sum(r["unpacked"] for r in sub),
               sum(r["unpacked"] for r in sub) / max(1, sum(r["packed"] for r in sub))))
    print()
    print("=== by magic ===")
    c = Counter(r["magic"] for r in ok)
    for m, v in c.most_common():
        print("  %-12s %4d" % (m, v))
    print()
    print("=== magic-shaped hits that did NOT decode: %d ===" % len(bad))
    c = Counter(r["magic"] for r in bad)
    for m, v in c.most_common():
        print("  %-12s %4d" % (m, v))
    for r in bad[:40]:
        print("  %-52s %8d %s" % (r["origin"], r["off"], r["magic"]))


main()
