"""Read an Amiga shared library's resident tag, autoinit block and function
table -- for the three in-house libraries in `libs/`.

The three Wyvern libraries are single-code-hunk files whose resident struct
sits at hunk offset 4.  What matters is the export count and where each entry
point is, because the game calls them by LVO and there is no symbol table.

Usage: libinfo.py <library> [--sine OFFSET]
"""
import sys, struct, math
from hunk import parse


def info(path):
    d = open(path, 'rb').read()
    h = parse(d)
    k = h['hunks'][0]
    b = d[k['off']:k['off'] + k['size']]
    i = b.find(b'\x4a\xfc')
    match, endskip = struct.unpack_from('>II', b, i + 2)
    flags, ver, typ, pri = struct.unpack_from('>BBBb', b, i + 10)
    nameptr, idptr, initptr = struct.unpack_from('>III', b, i + 14)
    dsize, ftab, istruct, ifunc = struct.unpack_from('>4I', b, initptr)
    fns, o = [], ftab
    while True:
        v = struct.unpack_from('>I', b, o)[0]
        if v == 0xFFFFFFFF or len(fns) > 200:
            break
        fns.append(v)
        o += 4
    name = b[nameptr:b.index(b'\x00', nameptr)].decode('latin-1')
    ident = b[idptr:b.index(b'\x00', idptr)].decode('latin-1')
    return b, dict(code=len(b), resident=i, endskip=endskip, ver=ver,
                   pri=pri, name=name, id=ident, dsize=dsize, ftab=ftab,
                   fns=fns)


if __name__ == '__main__':
    b, v = info(sys.argv[1])
    print('%s  code hunk %d bytes' % (sys.argv[1], v['code']))
    print('  resident tag at 0x%X, endskip 0x%X, version %d, priority %d'
          % (v['resident'], v['endskip'], v['ver'], v['pri']))
    print('  name %r  id %r' % (v['name'], v['id']))
    print('  autoinit: data size %d, function table at 0x%X'
          % (v['dsize'], v['ftab']))
    print('  %d table entries = 4 standard + %d exports'
          % (len(v['fns']), len(v['fns']) - 4))
    for n, a in enumerate(v['fns']):
        print('     LVO %5d -> 0x%06X%s'
              % (-6 * (n + 1), a, '   (Open/Close/Expunge/reserved)'
                 if n < 4 else ''))
    if len(sys.argv) > 3 and sys.argv[2] == '--sine':
        off = int(sys.argv[3], 0)
        t = struct.unpack_from('>512h', b, off)
        print('  sine table at 0x%X: %d entries, peak %d'
              % (off, len(t), max(t)))
        print('  first 16: %s' % ', '.join(str(x) for x in t[:16]))
        bad = sum(1 for n, x in enumerate(t)
                  if x != round(16384 * math.sin(2 * math.pi * n / 512)))
        print('  entries differing from round(16384*sin(2*pi*n/512)): %d of 512'
              % bad)
