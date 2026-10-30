"""List the contents of a `.sty` story archive.

A `.sty` is `FORM HEAD` with one `STRY` chunk: a directory of named `.ASP`
presentation scripts, each of them an `RNC\\2` container elsewhere in the same
file.  Record layout, all big-endian:

    UWORD  count
    repeat:
       UWORD  record length, including this field, padded to even
       ULONG  file offset of the RNC\\2 block
       UBYTE  variant index (0 or 1)
       char   name[], NUL-terminated, padded out to the record length

Usage: sty.py <file.sty>
"""
import sys, struct


def entries(d):
    assert d[:4] == b'FORM' and d[8:12] == b'HEAD', 'not a .sty story archive'
    assert d[12:16] == b'STRY', 'no STRY chunk'
    n = struct.unpack_from('>I', d, 16)[0]
    blob = d[20:20 + n]
    count = struct.unpack_from('>H', blob, 0)[0]
    o = 2
    out = []
    for _ in range(count):
        ln = struct.unpack_from('>H', blob, o)[0]
        off = struct.unpack_from('>I', blob, o + 2)[0]
        var = blob[o + 6]
        name = blob[o + 7:o + ln].split(b'\x00')[0].decode('latin-1')
        out.append((off, var, name, ln))
        o += ln
    return out


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    rows = entries(d)
    print('%s  %d bytes, %d entries' % (sys.argv[1], len(d), len(rows)))
    for i, (off, var, name, ln) in enumerate(rows):
        end = rows[i + 1][0] if i + 1 < len(rows) else len(d)
        magic = d[off:off + 4]
        unp, pk = struct.unpack_from('>II', d, off + 4)
        print('  %2d  @0x%-7X var=%d  %-14s %-5s packed %6d -> %6d'
              % (i, off, var, name, magic.decode('latin-1').strip(), pk, unp))
