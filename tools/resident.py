#!/usr/bin/env python3
"""Materialise Myth's resident corpus and report the three band figures.

Pieces are named with the convention this pipeline uses for a disc that has
nesting, so that every address quoted anywhere in the documentation is
attached to a named piece:

    <file>              the file exactly as pressed
    <file>+s<off>       a stream found at byte <off> of <file>
    <file>+gap<off>     raw bytes at <off> that no stream covers

Three figures come out, and every claim in the documentation says which one
it is testing against:

    on disc    the file as pressed
    resident   the corpus after unpacking at every level, gaps included
    used       resident minus each piece's trailing zero run

Usage: python3 tools/resident.py <isofiles-dir> <chunkdir> [--out DIR]
"""
import os, sys, struct, hashlib, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dave import unpack_stream
from mythdir import parse as parse_dir

MAGIC = b'DAVE'


def decode_chunk(d):
    """Return (kind, output) for one chunk of a floppy image."""
    if d[:4] == MAGIC:
        n = struct.unpack_from('>I', d, 4)[0]
        out, residue, tl = unpack_stream(d[8:], n)
        assert residue == 0 and tl == n and len(out) == n
        return 'DAVE', out
    # a bare Bytekiller stream declares its length in its own trailer
    if len(d) >= 16:
        n = struct.unpack_from('>I', d, len(d) - 4)[0]
        if 16 <= n <= (8 << 20):
            try:
                out, residue, tl = unpack_stream(d, n)
                if residue == 0 and len(out) == n:
                    return 'bare', out
            except Exception:
                pass
    return 'raw', d


def used(b):
    i = len(b)
    while i > 0 and b[i - 1] == 0:
        i -= 1
    return i


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('isodir')
    ap.add_argument('--out')
    a = ap.parse_args()
    if a.out:
        os.makedirs(a.out, exist_ok=True)

    pieces = []          # (name, kind, ondisc, resident, used)
    for fn in sorted(os.listdir(a.isodir)):
        p = os.path.join(a.isodir, fn)
        d = open(p, 'rb').read()
        if fn.startswith('MYTH.') and len(d) == 901120:
            ents = parse_dir(d)
            claimed = bytearray(len(d))
            for tbl, o, n in ents:
                for k in range(o, min(o + n, len(d))):
                    claimed[k] = 1
            for i, (tbl, o, n) in enumerate(ents):
                kind, out = decode_chunk(d[o:o + n])
                name = "%s+s%x" % (fn, o) if kind != 'raw' else "%s+gap%x" % (fn, o)
                pieces.append((name, kind, n, len(out), used(out)))
                if a.out:
                    open(os.path.join(a.out, name.replace('/', '_')), 'wb').write(out)
            # gaps
            i = 0
            while i < len(d):
                if not claimed[i]:
                    j = i
                    while j < len(d) and not claimed[j]:
                        j += 1
                    seg = d[i:j]
                    name = "%s+gap%x" % (fn, i)
                    pieces.append((name, 'gap', j - i, j - i, used(seg)))
                    if a.out:
                        open(os.path.join(a.out, name.replace('/', '_')), 'wb').write(seg)
                    i = j
                else:
                    i += 1
        else:
            pieces.append((fn, 'raw', len(d), len(d), used(d)))
            if a.out:
                open(os.path.join(a.out, fn), 'wb').write(d)

    print("%-22s %-6s %10s %10s %10s %7s" %
          ("piece", "kind", "on disc", "resident", "used", "slack"))
    for name, kind, od, res, us in pieces:
        print("%-22s %-6s %10d %10d %10d %6.2f%%" %
              (name, kind, od, res, us, 100.0 * (res - us) / max(1, res)))
    tod = sum(p[2] for p in pieces)
    tres = sum(p[3] for p in pieces)
    tus = sum(p[4] for p in pieces)
    print("-" * 72)
    print("%-22s %-6s %10d %10d %10d %6.2f%%" %
          ("TOTAL", "", tod, tres, tus, 100.0 * (tres - tus) / tres))
    print()
    print("on disc (five pressed files)      %10d B  %8.3f MB" % (2722021, 2722021 / 1e6))
    print("resident (all levels, gaps in)    %10d B  %8.3f MB" % (tres, tres / 1e6))
    print("used (last non-zero per piece)    %10d B  %8.3f MB" % (tus, tus / 1e6))
    print("expansion resident / on disc      %10.3fx" % (tres / 2722021.0))
    print("slack resident vs used            %10.3f%%" % (100.0 * (tres - tus) / tres))
    print()
    from collections import Counter
    c = Counter(p[3] for p in pieces)
    print("=== histogram of resident sizes (values seen more than once) ===")
    for v, n in sorted(c.items(), key=lambda kv: -kv[1]):
        if n > 1:
            print("  %10d B  x%d" % (v, n))


if __name__ == '__main__':
    main()
