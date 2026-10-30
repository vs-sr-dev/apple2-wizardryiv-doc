"""Read an unpacked LevelN/<language>.Pak: the game's in-level text.

The file is a magic word and then a run of records.  A record is 7-bit ASCII
with 0x0A between lines and 0xFF 0xFE at the end; there is no count, no index
and no offset table, so the reader is the record separator and nothing else.
"""
import sys

MAGIC = b'RDT!'
END   = bytes([0xFF, 0xFE])

def records(d):
    assert d[:4] == MAGIC, 'not an RDT! file: %r' % d[:4]
    body, out, cur, i = d[4:], [], [], 0
    while i < len(body):
        if body[i:i+2] == END:
            out.append(cur); cur = []; i += 2; continue
        nl  = body.find(b'\n', i)
        end = body.find(END, i)
        stop = min(x for x in (nl, end, len(body)) if x >= 0)
        cur.append(body[i:stop].decode('latin-1'))
        i = stop + 1 if stop == nl else stop
        if stop == len(body):
            break
    if cur:
        out.append(cur)
    return out

if __name__ == '__main__':
    for p in sys.argv[1:]:
        r = records(open(p, 'rb').read())
        print('=== %s: %d records, %d lines' % (p, len(r), sum(len(x) for x in r)))
        for i, rec in enumerate(r):
            print('  [%3d] %s' % (i, ' | '.join(s.rstrip() for s in rec)))
