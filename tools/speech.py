"""Index the speech: the `.LOG` tables and the `.SAM` banks they point into.

A `.SAM` is a run of ordinary IFF `FORM 8SVX` samples with nothing between
them; the `.LOG` beside it is

    '  LG'
    ULONG  file offset of clip 0
    ...
    ULONG  file size          -- a sentinel, so clip i is [off[i], off[i+1])

and an entry of `0xFFFFFFFF` means **this line was never recorded**.  Every
directory holds two banks, Voice1 and Voice2, with the same number of
entries, so the whole script exists twice.

    speech.py <dir-with-Voice1.LOG> ...
"""
import sys, os, struct, collections

MISSING = 0xFFFFFFFF


def index(logpath):
    d = open(logpath, 'rb').read()
    assert d[:4] == b'  LG', 'not a .LOG index'
    n = (len(d) - 4) // 4
    return list(struct.unpack('>%dI' % n, d[4:4 + 4 * n]))


def clips(sampath):
    """-> [(offset, form_len, rate, body_len)] for every FORM 8SVX."""
    d = open(sampath, 'rb').read()
    o, out = 0, []
    while o + 12 <= len(d) and d[o:o + 4] == b'FORM':
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
        out.append((o, n, struct.unpack_from('>H', vh, 12)[0], body))
        o += 8 + n + (n & 1)
    return out, len(d)


if __name__ == '__main__':
    gt, gs, gm = 0, 0.0, 0
    for dirn in sys.argv[1:]:
        for v in ('Voice1', 'Voice2'):
            lg = index(os.path.join(dirn, v + '.LOG'))
            cl, size = clips(os.path.join(dirn, v + '.SAM'))
            lines = len(lg) - 1
            missing = sum(1 for x in lg[:-1] if x == MISSING)
            rates = collections.Counter(c[2] for c in cl)
            secs = sum(c[3] / c[2] for c in cl)
            gt += lines
            gs += secs
            gm += missing
            print('%-28s %-7s %4d lines, %4d recorded, %3d missing, '
                  '%9d bytes, %7.1f s' % (dirn, v, lines, len(cl), missing,
                                          size, secs))
            print('%36s rates %s' % ('', ', '.join(
                '%d Hz x%d' % (r, c) for r, c in rates.most_common(6))))
    print('total %d lines x 2 voices, %d never recorded, %.1f minutes'
          % (gt // 2, gm, gs / 60))
