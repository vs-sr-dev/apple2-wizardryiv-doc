"""Minimal AmigaDOS hunk-file reader, enough for the disc's four executables."""
import struct, sys

HUNK = {0x3E7:'UNIT',0x3E8:'NAME',0x3E9:'CODE',0x3EA:'DATA',0x3EB:'BSS',
        0x3EC:'RELOC32',0x3ED:'RELOC16',0x3EE:'RELOC8',0x3EF:'EXT',
        0x3F0:'SYMBOL',0x3F1:'DEBUG',0x3F2:'END',0x3F3:'HEADER',
        0x3F7:'DREL32',0x3F8:'DREL16',0x3F9:'DREL8',0x3FA:'LIB',0x3FB:'INDEX'}
MEM = {0:'any',1:'chip',2:'fast'}


def be32(b, o): return struct.unpack_from('>I', b, o)[0]


def parse(data):
    o = 0
    assert be32(data, o) == 0x3F3, 'not a hunk executable'
    o += 4
    # resident library names (always empty in practice)
    libs = []
    while True:
        n = be32(data, o); o += 4
        if n == 0: break
        libs.append(data[o:o+n*4].rstrip(b'\0').decode('latin-1')); o += n*4
    table_size = be32(data, o); first = be32(data, o+4); last = be32(data, o+8); o += 12
    sizes = []
    for _ in range(last - first + 1):
        v = be32(data, o); o += 4
        sizes.append((v & 0x3FFFFFFF, MEM.get(v >> 30, '?')))
    hunks, idx, pending = [], 0, {}
    while o < len(data):
        t = be32(data, o); o += 4
        name = HUNK.get(t & 0x3FFFFFFF, 'UNK%X' % t)
        if name in ('CODE', 'DATA'):
            n = be32(data, o); o += 4
            hunks.append(dict(index=idx, kind=name, size=n*4, off=o,
                              alloc=sizes[idx][0]*4, mem=sizes[idx][1]))
            o += n*4
        elif name == 'BSS':
            n = be32(data, o); o += 4
            hunks.append(dict(index=idx, kind=name, size=0, off=o, alloc=n*4,
                              mem=sizes[idx][1]))
        elif name == 'RELOC32':
            total = 0
            while True:
                cnt = be32(data, o); o += 4
                if cnt == 0: break
                o += 4                      # target hunk
                o += cnt*4
                total += cnt
            hunks[-1].setdefault('reloc32', 0)
            hunks[-1]['reloc32'] += total
        elif name == 'SYMBOL':
            syms = []
            while True:
                n = be32(data, o); o += 4
                if n == 0: break
                syms.append((data[o:o+n*4].rstrip(b'\0').decode('latin-1'),
                             be32(data, o+n*4)))
                o += n*4 + 4
            hunks[-1]['symbols'] = syms
        elif name == 'DEBUG':
            # SAS/C emits this before the first CODE hunk, so there may be
            # nothing to attach it to yet.
            n = be32(data, o); o += 4
            blob = data[o:o+n*4]
            o += n*4
            (hunks[-1] if hunks else pending)['debug'] = blob
        elif name == 'END':
            idx += 1
        else:
            raise ValueError('unhandled hunk %s at 0x%X' % (name, o-4))
    return dict(table_size=table_size, first=first, last=last, sizes=sizes,
                libs=libs, hunks=hunks, prelude=pending)


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    h = parse(d)
    print('%s: %d hunks, %d bytes' % (sys.argv[1], h['table_size'], len(d)))
    if h.get('prelude', {}).get('debug'):
        d0 = h['prelude']['debug']
        print('  before the first hunk: HUNK_DEBUG, %d bytes, tag %r'
              % (len(d0), d0[4:14]))
    for k in h['hunks']:
        print('  hunk %d %-5s %7d bytes  alloc %7d  %-4s  reloc32=%d  file@0x%X'
              % (k['index'], k['kind'], k['size'], k['alloc'], k['mem'],
                 k.get('reloc32', 0), k['off']))
        if 'symbols' in k:
            print('      symbols:', k['symbols'])
