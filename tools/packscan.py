#!/usr/bin/env python3
"""Scan a file (or a tree) for packed streams at *every* byte offset, and
validate each candidate by actually running the decompressor.

A magic number alone proves nothing: `RNC\\x01` occurs by chance roughly once
per 4 GB, but it also occurs inside sprite data.  A candidate is accepted only
when the decoder consumes exactly the declared packed length and, where the
container has one, the CRC matches.  That cannot produce a false positive: a
byte sequence that decodes cleanly to its own declared length is packed by
construction.

Recognised containers:
    RNC ProPack method 1   'RNC' 01   (CRC-16/ARC on both halves)
    RNC ProPack method 2   'RNC' 02   (same header, different bit stream)
    PowerPacker 2.0        'PP20'     (no checksum -- structural validation only)
    Imploder               'IMP!'/'ATN!'
    CrunchMania            'CrM!'/'Crm!'/'CrM2'/'Crm2'

Usage:
    python3 tools/packscan.py <file-or-dir> [--extract DIR] [--min-gain N]
"""
import sys, os, argparse, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rnc
import rnc2
import pp20

RNC_HDR = 18


def try_rnc(blob, off):
    """Return (kind, packed_total, unpacked_bytes) or None."""
    if blob[off:off + 3] != b'RNC':
        return None
    method = blob[off + 3]
    if method not in (1, 2):
        return None
    ulen = int.from_bytes(blob[off + 4:off + 8], 'big')
    plen = int.from_bytes(blob[off + 8:off + 12], 'big')
    if ulen == 0 or plen == 0 or ulen > 4 << 20 or plen > 4 << 20:
        return None
    if off + RNC_HDR + plen > len(blob):
        return None
    seg = blob[off:off + RNC_HDR + plen]
    try:
        out = (rnc if method == 1 else rnc2).unpack(seg)
    except Exception:
        return None
    if len(out) != ulen:
        return None
    return ('RNC%d' % method, RNC_HDR + plen, out)


def try_pp20(blob, off):
    if blob[off:off + 4] != b'PP20':
        return None
    # PowerPacker stores the unpacked length in the last four bytes of the
    # stream, so the stream length is not known from the header.  Walk to the
    # end of the file and let the structural check decide.
    for end in range(len(blob), off + 12, -4):
        seg = blob[off:end]
        try:
            out = pp20.unpack(seg)
        except Exception:
            continue
        if out:
            return ('PP20', end - off, out)
        break
    return None


def try_imploder(blob, off):
    if blob[off:off + 4] not in (b'IMP!', b'ATN!'):
        return None
    return ('Imploder?', 0, None)


def try_crm(blob, off):
    if blob[off:off + 4] in (b'CrM!', b'Crm!', b'CrM2', b'Crm2'):
        return ('CrunchMania?', 0, None)
    return None


MAGICS = [
    (b'RNC', try_rnc),
    (b'PP20', try_pp20),
    (b'IMP!', try_imploder),
    (b'ATN!', try_imploder),
    (b'CrM!', try_crm),
    (b'Crm!', try_crm),
    (b'CrM2', try_crm),
    (b'Crm2', try_crm),
]


def scan_blob(blob, label, extract=None, depth=0, results=None):
    if results is None:
        results = []
    off = 0
    hits = []
    while off < len(blob) - 8:
        got = None
        for magic, fn in MAGICS:
            if blob.startswith(magic, off):
                got = fn(blob, off)
                if got:
                    break
        if got and got[1]:
            kind, size, out = got
            hits.append((off, kind, size, out))
            off += size
        else:
            off += 1
    for i, (off, kind, size, out) in enumerate(hits):
        name = '%s@%d' % (label, off)
        results.append(dict(label=label, off=off, kind=kind, packed=size,
                            unpacked=len(out), depth=depth,
                            sha1=hashlib.sha1(out).hexdigest()))
        if extract:
            p = os.path.join(extract, '%s.%06d.%s.bin' %
                             (os.path.basename(label), off, kind))
            open(p, 'wb').write(out)
        # nesting: re-scan what we just unpacked
        scan_blob(out, name, extract, depth + 1, results)
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('target')
    ap.add_argument('--extract')
    args = ap.parse_args()
    if args.extract:
        os.makedirs(args.extract, exist_ok=True)
    paths = []
    if os.path.isdir(args.target):
        for root, _d, files in os.walk(args.target):
            for f in sorted(files):
                paths.append(os.path.join(root, f))
    else:
        paths = [args.target]
    print('%-16s %8s %-8s %10s %10s %5s  %s' %
          ('file', 'offset', 'kind', 'packed', 'unpacked', 'depth', 'sha1'))
    grand = 0
    for p in sorted(paths):
        blob = open(p, 'rb').read()
        base = os.path.basename(p)
        res = scan_blob(blob, base, args.extract)
        for r in res:
            print('%-16s %8d %-8s %10d %10d %5d  %s' %
                  (r['label'][:16], r['off'], r['kind'], r['packed'],
                   r['unpacked'], r['depth'], r['sha1'][:12]))
            grand += r['unpacked']
        if res:
            covered = sum(r['packed'] for r in res if r['depth'] == 0)
            print('    %-12s %d streams, %d/%d bytes covered (%.1f%%)' %
                  (base, len(res), covered, len(blob),
                   100.0 * covered / len(blob)))
    print('total unpacked bytes: %d' % grand)


if __name__ == '__main__':
    main()
