"""Reader for the game's own 'LEV2' level container.

Header: 'LEV2', a start offset, the total length, then seven section offsets
and the total again as the eighth bound; two words; a 40-byte space-padded
name.  Every level on the disc has the same seven sections, so the count is
fixed in the code rather than stored in the file.
"""
import struct, sys, os

def parse(b):
    assert b[:4] == b'LEV2', b[:4]
    start, total = struct.unpack_from('>II', b, 4)
    offs = list(struct.unpack_from('>7I', b, 12))
    a, c = struct.unpack_from('>HH', b, 0x28)
    name = b[0x2C:0x54].decode('latin-1')
    return dict(start=start, total=total, offs=offs + [total], w=a, h=c, name=name)

if __name__ == '__main__':
    print('%-26s %8s %4s %4s  %s' % ('file', 'total', 'a', 'b', 'name'))
    rows = []
    for d in ('Levels/Outside', 'Levels/Inside'):
        for f in sorted(os.listdir('_work/unpacked/' + d)):
            h = parse(open('_work/unpacked/%s/%s' % (d, f), 'rb').read())
            rows.append((f, h))
            print('%-26s %8d %4d %4d  %r' % (f, h['total'], h['w'], h['h'], h['name']))
    print()
    print('%-26s %s' % ('file', ' '.join('%7s' % ('sec%d' % i) for i in range(7))))
    for f, h in rows:
        o = h['offs']
        print('%-26s %s' % (f, ' '.join('%7d' % (o[i+1]-o[i]) for i in range(7))))
