"""Walk `Samples*.BIN` and the `FORM 8SVX` runs inside a `.sty` archive.

    UWORD  sample count
    FORM 8SVX x count

with nothing between the samples and no padding: the walk lands on the file
size exactly on all three banks.  Each sample carries its own rate in its own
`VHDR`, so the rate is per clip, not per bank.

Usage: samples.py <Samples*.BIN | *.sty> ...
"""
import sys, struct, collections


def forms(d, o):
    """Yield (offset, form length, rate, body length) for a run of 8SVX."""
    while o + 12 <= len(d) and d[o:o + 4] == b'FORM' and d[o + 8:o + 12] == b'8SVX':
        n = struct.unpack_from('>I', d, o + 4)[0]
        p, vh, body = o + 12, None, 0
        while p < o + 8 + n:
            cid = d[p:p + 4]
            ln = struct.unpack_from('>I', d, p + 4)[0]
            if cid == b'VHDR':
                vh = d[p + 8:p + 8 + ln]
            elif cid == b'BODY':
                body = ln
            p += 8 + ln + (ln & 1)
        yield o, n, struct.unpack_from('>H', vh, 12)[0], body, vh[15]
        o += 8 + n + (n & 1)


if __name__ == '__main__':
    for path in sys.argv[1:]:
        d = open(path, 'rb').read()
        if d[:4] == b'FORM':
            print('%s: scanning for uncompressed 8SVX runs' % path)
            o, found = 0, 0
            while True:
                o = d.find(b'FORM', o + 1)
                if o < 0:
                    break
                if d[o + 8:o + 12] != b'8SVX':
                    continue
                for off, n, rate, body, comp in forms(d, o):
                    print('   @0x%-8X %8d bytes  %6d samples @ %5d Hz'
                          '  %5.2f s  compression %d'
                          % (off, n, body, rate, body / rate, comp))
                    found += 1
                    o = off
            print('   %d samples' % found)
            continue
        n = struct.unpack_from('>H', d, 0)[0]
        rows = list(forms(d, 2))
        rates = collections.Counter(r[2] for r in rows)
        end = rows[-1][0] + 8 + rows[-1][1] + (rows[-1][1] & 1) if rows else 2
        print('%-16s %7d bytes  %2d declared, %2d found, %.2f s'
              % (path, len(d), n, len(rows), sum(r[3] / r[2] for r in rows)))
        print('%18s walk ends at %d, file is %d' % ('', end, len(d)))
        print('%18s rates: %s'
              % ('', ', '.join('%d Hz x%d' % (k, v)
                               for k, v in rates.most_common())))
