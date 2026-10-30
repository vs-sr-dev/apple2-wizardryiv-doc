#!/usr/bin/env python3
"""Walk the disc's packed containers and print the whole tree, gaps included.

Universe stores its data in three shapes and the scan has to see all three:

  * a plain file that is one RNC stream         (`title.np`, `code.prg`, ...)
  * a file that is a *concatenation* of RNC streams with raw gaps between
    them   (`scene*.dat`)
  * a file that is one RNC stream whose *output* is a concatenation of RNC
    streams, some of which are themselves concatenations
    (`part*.dat` -- three levels of RNC)

Nothing on the disc declares any of this: there is no directory, no count and
no length table in front of the streams.  The structure is recovered by
scanning every byte offset for the container magic and accepting a candidate
only when the decompressor consumes exactly the declared packed length and the
CRC-16 matches, which cannot produce a false positive.

Usage: python3 tools/containers.py <dir> [--json FILE]
"""
import sys, os, json, argparse, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rnc

HDR = 18


def streams(blob):
    """Every validated RNC stream in blob, as (offset, packed, data)."""
    out = []
    off = 0
    n = len(blob)
    while off < n - HDR:
        if blob[off:off + 3] == b'RNC' and blob[off + 3] in (1, 2):
            ulen = int.from_bytes(blob[off + 4:off + 8], 'big')
            plen = int.from_bytes(blob[off + 8:off + 12], 'big')
            if 0 < plen and 0 < ulen < (8 << 20) and off + HDR + plen <= n:
                try:
                    data = rnc.unpack(blob[off:off + HDR + plen])
                except Exception:
                    data = None
                if data is not None and len(data) == ulen:
                    out.append((off, HDR + plen, data))
                    off += HDR + plen
                    continue
        off += 1
    return out


def walk(blob, depth, path, acc, gaps):
    ss = streams(blob)
    cur = 0
    for off, packed, data in ss:
        if off > cur:
            gaps.append((path, depth, cur, off - cur,
                         blob[cur:off]))
        acc.append(dict(path=path, depth=depth, off=off, packed=packed,
                        unpacked=len(data),
                        sha1=hashlib.sha1(data).hexdigest()))
        walk(data, depth + 1, '%s/%d' % (path, off), acc, gaps)
        cur = off + packed
    if ss and cur < len(blob):
        gaps.append((path, depth, cur, len(blob) - cur, blob[cur:]))
    return ss


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root')
    ap.add_argument('--json')
    args = ap.parse_args()

    files = []
    for r, _d, fs in os.walk(args.root):
        for f in fs:
            files.append(os.path.join(r, f))
    files.sort(key=lambda p: os.path.basename(p))

    allrec, allgaps = [], []
    print('%-14s %5s %8s %9s %9s  %s' %
          ('file', 'depth', 'offset', 'packed', 'unpacked', 'ratio'))
    for p in files:
        blob = open(p, 'rb').read()
        base = os.path.basename(p)
        acc, gaps = [], []
        top = walk(blob, 0, base, acc, gaps)
        if not acc:
            continue
        for r in acc:
            print('%-14s %5d %8d %9d %9d  %5.2fx' %
                  (base if r['depth'] == 0 else '',
                   r['depth'], r['off'], r['packed'], r['unpacked'],
                   r['unpacked'] / r['packed']))
        cov = sum(s[1] for s in top)
        print('  %-12s %2d streams total, depth 0 covers %d/%d bytes (%.1f%%)'
              % (base, len(acc), cov, len(blob), 100.0 * cov / len(blob)))
        for g in gaps:
            print('  GAP %-10s depth %d  off %7d  %6d bytes  first16 %s' %
                  (g[0][:10], g[1], g[2], g[3], g[4][:16].hex()))
        allrec += acc
        allgaps += [(g[0], g[1], g[2], g[3]) for g in gaps]

    print()
    print('=== TOTALS BY DEPTH ===')
    for d in sorted(set(r['depth'] for r in allrec)):
        rs = [r for r in allrec if r['depth'] == d]
        print('depth %d  %4d streams  %10d packed  %10d unpacked  %5.2fx' %
              (d, len(rs), sum(r['packed'] for r in rs),
               sum(r['unpacked'] for r in rs),
               sum(r['unpacked'] for r in rs) /
               max(1, sum(r['packed'] for r in rs))))
    leaves = []
    for r in allrec:
        kids = [x for x in allrec
                if x['path'].startswith(r['path'] + '/%d' % r['off'])]
        if not kids:
            leaves.append(r)
    print('leaf streams (nothing packed inside them): %d, %d bytes' %
          (len(leaves), sum(r['unpacked'] for r in leaves)))
    print('gaps: %d, %d bytes' % (len(allgaps), sum(g[3] for g in allgaps)))
    if args.json:
        json.dump(dict(streams=allrec, gaps=allgaps),
                  open(args.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
