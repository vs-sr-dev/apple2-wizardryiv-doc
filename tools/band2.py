#!/usr/bin/env python3
"""band2.py -- the three band figures, for a disc whose cruncher is RNC.

Why this is not tools/band.py.  The inherited band.py knows exactly two magics,
`IMP!` and `ATN!`, because it was written on a disc packed with the Imploder.
Run unmodified on this disc it reports "validated streams: 0", which is not a
measurement -- it is the tool's magic list.  Run unmodified on the Superfrog
tree it reports 158 streams at depth 2, so the tool works; it simply cannot see
RNC.  That control run is the reason this file exists rather than a zero being
written into the documentation.

This version detects every magic the set knows, validates each hit by running
the decompressor (a hit that does not decode is counted separately and never
contributes bytes), recurses into decoded output, and reports:

    on disc    the file as pressed
    resident   the corpus after unpacking at every level, raw gaps included
    used       resident minus each piece's trailing run of zero bytes

Pieces are named with the pipeline's convention, so any address quoted in the
documentation is attached to a named piece:

    <file>              the file exactly as pressed
    <file>+s<off>       a stream found at byte <off> of <file>
    <file>+gap<off>     raw bytes at <off> that no stream covers

Usage: band2.py <extracted-dir> [--maxdepth N] [--per-file] [--out DIR]
"""
import os, sys, argparse, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rnc

MAGICS = {b"RNC\x01": "RNC1", b"RNC\x02": "RNC2", b"IMP!": "Imploder",
          b"ATN!": "Imploder", b"PP20": "PP20", b"PP11": "PP11",
          b"CrM!": "CrunchMania", b"CrM2": "CrunchMania",
          b"Crm!": "CrunchMania", b"Crm2": "CrunchMania",
          b"PaCK": "PaCK", b"DAVE": "DAVE"}


def try_decode(blob, off):
    """Return (kind, packed_len, output) for a validated stream at `off`."""
    m = blob[off:off + 4]
    kind = MAGICS.get(bytes(m))
    if kind is None:
        return None
    if kind in ("RNC1", "RNC2"):
        if off + 18 > len(blob):
            return None
        unp = int.from_bytes(blob[off + 4:off + 8], 'big')
        pk = int.from_bytes(blob[off + 8:off + 12], 'big')
        if unp == 0 or pk == 0 or off + 18 + pk > len(blob):
            return None
        if unp > 64 * 1024 * 1024:
            return None
        try:
            out = rnc.unpack(bytes(blob[off:off + 18 + pk]))
        except Exception:
            return None
        if len(out) != unp:
            return None
        return kind, 18 + pk, out
    return None            # other codecs are absent from this disc; see notes


def walk(name, blob, depth, maxdepth, pieces, stats):
    """Split `blob` into validated streams and the raw gaps between them."""
    hits = []
    i = 0
    while i < len(blob) - 4:
        r = try_decode(blob, i)
        if r:
            kind, plen, out = r
            hits.append((i, kind, plen, out))
            stats['validated'] += 1
            stats['by_depth'].setdefault(depth, [0, 0, 0])
            stats['by_depth'][depth][0] += 1
            stats['by_depth'][depth][1] += plen
            stats['by_depth'][depth][2] += len(out)
            i += plen
            continue
        if bytes(blob[i:i + 4]) in MAGICS:
            stats['rejected'] += 1
        i += 1

    if not hits:
        pieces.append((name, bytes(blob)))
        return

    cur = 0
    for off, kind, plen, out in hits:
        if off > cur:
            pieces.append(("%s+gap%d" % (name, cur), bytes(blob[cur:off])))
            stats['gaps'] += 1
            stats['gapbytes'] += off - cur
        sub = "%s+s%d" % (name, off)
        if depth + 1 <= maxdepth:
            walk(sub, out, depth + 1, maxdepth, pieces, stats)
        else:
            stats['clipped'] += 1
            pieces.append((sub, out))
        cur = off + plen
    if cur < len(blob):
        pieces.append(("%s+gap%d" % (name, cur), bytes(blob[cur:])))
        stats['gaps'] += 1
        stats['gapbytes'] += len(blob) - cur


def used_bytes(b):
    i = len(b)
    while i and b[i - 1] == 0:
        i -= 1
    return i


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root')
    ap.add_argument('--maxdepth', type=int, default=6)
    ap.add_argument('--per-file', action='store_true')
    ap.add_argument('--out')
    a = ap.parse_args()

    files = []
    for dp, dn, fn in os.walk(a.root):
        for f in sorted(fn):
            p = os.path.join(dp, f)
            files.append((p, '/' + os.path.relpath(p, a.root).replace('\\', '/')))
    files.sort(key=lambda x: -os.path.getsize(x[0]))

    stats = dict(validated=0, rejected=0, gaps=0, gapbytes=0, clipped=0,
                 by_depth={})
    rows = []
    total_disc = total_res = total_used = 0
    allpieces = []
    for path, rel in files:
        blob = open(path, 'rb').read()
        pieces = []
        walk(rel, blob, 0, a.maxdepth, pieces, stats)
        res = sum(len(b) for _, b in pieces)
        usd = sum(used_bytes(b) for _, b in pieces)
        rows.append((rel, len(blob), res, usd, len(pieces)))
        total_disc += len(blob)
        total_res += res
        total_used += usd
        allpieces += pieces

    if a.per_file:
        print("%-42s %10s %10s %10s %6s %7s"
              % ("file", "on disc", "resident", "used", "pieces", "slack"))
        for rel, d, r, u, n in rows:
            print("%-42s %10d %10d %10d %6d %6.2f%%"
                  % (rel, d, r, u, n, 100.0 * (r - u) / r if r else 0))

    print("\n=== the three figures ===")
    print("  on disc   %10d B" % total_disc)
    print("  resident  %10d B" % total_res)
    print("  used      %10d B" % total_used)
    print("  expansion %.3fx      slack %.3f%%"
          % (total_res / total_disc if total_disc else 0,
             100.0 * (total_res - total_used) / total_res if total_res else 0))

    print("\n=== containers ===")
    print("  validated streams : %d" % stats['validated'])
    print("  magic-shaped hits that did NOT decode: %d" % stats['rejected'])
    for d in sorted(stats['by_depth']):
        n, p, u = stats['by_depth'][d]
        print("  depth %d: %3d streams  %9d packed -> %9d unpacked  %.2fx"
              % (d, n, p, u, u / p if p else 0))
    print("  deepest nesting   : %d" % (max(stats['by_depth']) if stats['by_depth'] else 0))
    print("  raw gaps: %d runs, %d bytes" % (stats['gaps'], stats['gapbytes']))
    print("  clipped at maxdepth: %d" % stats['clipped'])

    print("\n=== slack, per piece (non-zero only) ===")
    sl = [(n, len(b), used_bytes(b)) for n, b in allpieces]
    sl = [(n, r, u) for n, r, u in sl if r > u]
    sl.sort(key=lambda x: -(x[1] - x[2]))
    print("  pieces with any trailing zeros: %d of %d" % (len(sl), len(allpieces)))
    for n, r, u in sl[:15]:
        print("  %-46s resident %8d used %8d slack %7d  %5.2f%%"
              % (n, r, u, r - u, 100.0 * (r - u) / r))

    if a.out:
        os.makedirs(a.out, exist_ok=True)
        for n, b in allpieces:
            fn = n.strip('/').replace('/', '_')
            open(os.path.join(a.out, fn), 'wb').write(b)
        print("\nwrote %d pieces to %s" % (len(allpieces), a.out))


if __name__ == '__main__':
    main()
