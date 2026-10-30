#!/usr/bin/env python3
"""Report every ProTracker module in a tree: title, sample names, lengths,
pattern count and the size the header implies, checked against the file.

    python tools/mods.py _work/unpacked
"""
import sys, os, struct, hashlib


def report(d, name):
    if len(d) < 1084 or d[1080:1084] not in (b'M.K.', b'M!K!', b'FLT4'):
        return None
    title = d[0:20].rstrip(b'\0').decode('latin1', 'replace')
    samples = []
    for i in range(31):
        o = 20 + 30 * i
        nm = d[o:o + 22].rstrip(b'\0 ').decode('latin1', 'replace')
        ln = struct.unpack_from('>H', d, o + 22)[0] * 2
        ft = d[o + 24] & 0x0F
        vol = d[o + 25]
        rep = struct.unpack_from('>H', d, o + 26)[0] * 2
        rl = struct.unpack_from('>H', d, o + 28)[0] * 2
        samples.append((i + 1, nm, ln, ft, vol, rep, rl))
    songlen = d[950]
    order = list(d[952:1080])
    npat = max(order[:max(1, songlen)]) + 1
    body = 1084 + 1024 * npat
    smp = sum(s[2] for s in samples)
    print("== %s  (%d bytes, SHA-1 %s)" % (name, len(d), hashlib.sha1(d).hexdigest()))
    print("   title %r  song length %d  patterns %d  sample bytes %d" %
          (title, songlen, npat, smp))
    print("   header implies %d bytes, file is %d (%+d)" % (body + smp, len(d), len(d) - (body + smp)))
    for i, nm, ln, ft, vol, rep, rl in samples:
        if ln or nm:
            print("     %2d %-24s len %6d  vol %3d  finetune %d  loop %d+%d" %
                  (i, repr(nm)[1:-1], ln, vol, ft, rep, rl))
    return title, samples


def main():
    root = sys.argv[1]
    for dp, dn, fn in os.walk(root):
        dn.sort()
        for f in sorted(fn):
            p = os.path.join(dp, f)
            d = open(p, 'rb').read()
            report(d, os.path.relpath(p, root).replace(os.sep, '/'))


if __name__ == '__main__':
    main()
