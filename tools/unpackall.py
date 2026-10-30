#!/usr/bin/env python3
"""Write the resident corpus: every file with every container expanded.

For each input file this writes one output file per resident piece, named
<path>__<offset-chain>.bin, so a file that is a concatenation of streams
becomes several outputs and the gaps between them are kept as their own
pieces.  Nothing is discarded, so the total output size equals the resident
figure printed by tools/band.py.

Usage: python3 tools/unpackall.py <extracted-dir> <out-dir>
"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from speris_imp import Decruncher

MAXDEPTH = 6


def imploder_at(data, off):
    if off + 12 > len(data) or bytes(data[off:off + 4]) not in (b"IMP!", b"ATN!"):
        return None
    orig, packed = struct.unpack_from(">II", data, off + 4)
    if orig == 0 or packed == 0 or orig > 32 << 20 or packed > 32 << 20:
        return None
    end = off + 12 + packed + 38
    if end > len(data):
        return None
    try:
        out = Decruncher(bytes(data[off:end])).run()
    except Exception:
        return None
    if out is None or len(out) != orig:
        return None
    return (end - off, out)


def walk(data, depth, tag, emit):
    if depth > MAXDEPTH:
        emit(tag + "+clip", bytes(data))
        return
    i, last, n, found = 0, 0, len(data), False
    while i < n - 12:
        r = imploder_at(data, i) if bytes(data[i:i + 4]) in (b"IMP!", b"ATN!") else None
        if r:
            length, out = r
            found = True
            if data[last:i]:
                emit(tag + "+gap%d" % last, bytes(data[last:i]))
            walk(out, depth + 1, tag + "+s%d" % i, emit)
            i += length
            last = i
            continue
        i += 1
    if not found:
        emit(tag, bytes(data))
        return
    if data[last:]:
        emit(tag + "+gap%d" % last, bytes(data[last:]))


def main():
    root, out = sys.argv[1], sys.argv[2]
    total = 0
    count = 0
    for dp, dn, fn in os.walk(root):
        for f in sorted(fn):
            p = os.path.join(dp, f)
            rel = p[len(root):].strip(os.sep).replace(os.sep, "_")
            d = open(p, "rb").read()
            pieces = []
            walk(d, 0, rel, lambda t, b: pieces.append((t, b)))
            for t, b in pieces:
                o = os.path.join(out, t.replace("/", "_") + ".bin")
                os.makedirs(os.path.dirname(o), exist_ok=True)
                open(o, "wb").write(b)
                total += len(b)
                count += 1
    print("%d resident pieces, %d bytes" % (count, total))


main()
