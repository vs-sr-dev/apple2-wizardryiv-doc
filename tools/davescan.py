#!/usr/bin/env python3
"""Scan every byte offset for `DAVE` containers and bare Bytekiller streams,
validating each hit by running the decompressor and checking its checksum.

Two hit kinds are looked for, and both are *validated*, so neither can be a
false positive:

  DAVE   a `DAVE` magic at any offset whose declared length matches the
         stream trailer's and whose XOR checksum comes out zero.

  bare   a Bytekiller stream with no container header at all -- the form
         MYTH.A chunk 1 uses.  These have no magic, so the only way to find
         one is to try every offset as a stream *end*: read the trailer,
         decode, and keep the hit only if the checksum residue is zero and
         the decoded length matches.  That is expensive, so bare scanning is
         opt-in with --bare and is bounded by --bare-step.

Recursion: whatever a stream decodes to is scanned again, up to --depth.

Usage: python3 tools/davescan.py <dir-or-file>... [--depth N] [--out DIR]
                                 [--bare] [--bare-step N]
"""
import os, sys, struct, hashlib, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dave import unpack_stream

MAGIC = b'DAVE'
MAXOUT = 8 << 20


def try_dave(d, off):
    """Validate a DAVE container at off. Returns (out, packed_len) or None."""
    if off + 16 > len(d):
        return None
    n = struct.unpack_from('>I', d, off + 4)[0]
    if n == 0 or n > MAXOUT:
        return None
    # the stream runs to some end; the declared length must reappear in the
    # trailer, so search forward for the first end where it does.
    body = d[off + 8:]
    # trailer u32 at end-4 must equal n; try the whole remainder first, then
    # every 2-byte-aligned shorter end (streams are longword aligned in
    # practice, so step 2 is generous).
    ends = []
    lim = len(body)
    for e in range(12, lim + 1, 2):
        if struct.unpack_from('>I', body, e - 4)[0] == n:
            ends.append(e)
    for e in ends:
        try:
            out, residue, tl = unpack_stream(body[:e], n)
        except Exception:
            continue
        if residue == 0 and tl == n and len(out) == n:
            return out, 8 + e
    return None


def try_bare(d, end):
    """Validate a bare Bytekiller stream ending at `end`."""
    if end < 16:
        return None
    n = struct.unpack_from('>I', d, end - 4)[0]
    if n == 0 or n > MAXOUT or n < 16:
        return None
    try:
        out, residue, tl = unpack_stream(d[:end], n)
    except Exception:
        return None
    if residue == 0 and len(out) == n:
        return out, end
    return None


def scan(name, d, depth, maxdepth, out_dir, results, bare, bare_step):
    off = 0
    while True:
        i = d.find(MAGIC, off)
        if i < 0:
            break
        r = try_dave(d, i)
        if r:
            out, plen = r
            rec = dict(origin=name, off=i, kind='DAVE', depth=depth,
                       packed=plen, unpacked=len(out),
                       sha1=hashlib.sha1(out).hexdigest())
            results.append(rec)
            piece = "%s+s%x" % (name, i)
            if out_dir:
                open(os.path.join(out_dir, piece.replace('/', '_')), 'wb').write(out)
            if depth < maxdepth:
                scan(piece, out, depth + 1, maxdepth, out_dir, results,
                     bare, bare_step)
            off = i + plen
        else:
            results.append(dict(origin=name, off=i, kind='DAVE-nodecode',
                                depth=depth, packed=0, unpacked=0, sha1=''))
            off = i + 4
    if bare and depth == 0:
        for e in range(len(d), 15, -bare_step):
            r = try_bare(d, e)
            if r:
                out, plen = r
                rec = dict(origin=name, off=0, kind='bare', depth=depth,
                           packed=plen, unpacked=len(out),
                           sha1=hashlib.sha1(out).hexdigest())
                results.append(rec)
                piece = "%s+bare" % name
                if out_dir:
                    open(os.path.join(out_dir, piece.replace('/', '_')), 'wb').write(out)
                if depth < maxdepth:
                    scan(piece, out, depth + 1, maxdepth, out_dir, results,
                         bare, bare_step)
                break


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('targets', nargs='+')
    ap.add_argument('--depth', type=int, default=4)
    ap.add_argument('--out')
    ap.add_argument('--bare', action='store_true')
    ap.add_argument('--bare-step', type=int, default=2)
    a = ap.parse_args()
    if a.out:
        os.makedirs(a.out, exist_ok=True)
    files = []
    for t in a.targets:
        if os.path.isdir(t):
            for dp, dn, fn in os.walk(t):
                for f in sorted(fn):
                    files.append(os.path.join(dp, f))
        else:
            files.append(t)
    results = []
    for p in sorted(files):
        d = open(p, 'rb').read()
        scan(os.path.basename(p), d, 0, a.depth, a.out, results,
             a.bare, a.bare_step)
    ok = [r for r in results if r['kind'] != 'DAVE-nodecode']
    bad = [r for r in results if r['kind'] == 'DAVE-nodecode']
    print("=== validated streams: %d ===" % len(ok))
    print("%-38s %8s %-6s %5s %9s %9s %6s" %
          ("origin", "offset", "kind", "depth", "packed", "unpacked", "ratio"))
    for r in ok:
        print("%-38s %8d %-6s %5d %9d %9d %5.1f%%" %
              (r['origin'], r['off'], r['kind'], r['depth'], r['packed'],
               r['unpacked'], 100.0 * r['packed'] / r['unpacked']))
    from collections import Counter
    print()
    print("=== by depth ===")
    for dd in sorted(set(r['depth'] for r in ok)):
        sub = [r for r in ok if r['depth'] == dd]
        p = sum(r['packed'] for r in sub)
        u = sum(r['unpacked'] for r in sub)
        print("  depth %d: %4d streams  %9d packed -> %9d unpacked  %.2fx" %
              (dd, len(sub), p, u, u / max(1, p)))
    print()
    print("=== magic-shaped hits that did NOT decode: %d ===" % len(bad))
    for r in bad[:40]:
        print("  %-38s %8d" % (r['origin'], r['off']))


if __name__ == '__main__':
    main()
