"""Walk an IFF file and print its chunk tree.

Everything Byte Engineers stored as data on this disc is an IFF FORM with
in-house chunk ids -- the 3D geometry (`.x3g`), the speech (`.SAM`) and the
animation streams (`.sty`).  Only the container is standard; the chunks are
not, and naming them is what the rest of the documentation does.

Usage: iff.py <file> [maxdepth]
"""
import sys, struct

CONTAINERS = (b'FORM', b'LIST', b'CAT ', b'PROP')


def walk(d, off, end, depth, out, maxdepth):
    while off + 8 <= end:
        cid = d[off:off + 4]
        n = struct.unpack_from('>I', d, off + 4)[0]
        body = off + 8
        if cid in CONTAINERS:
            sub = d[body:body + 4]
            out.append((depth, cid.decode('latin-1'), n,
                        sub.decode('latin-1'), body))
            if depth < maxdepth:
                walk(d, body + 4, min(end, body + n), depth + 1, out, maxdepth)
        else:
            out.append((depth, cid.decode('latin-1'), n, '', body))
        off = body + n + (n & 1)
    return out


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    md = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    rows = walk(d, 0, len(d), 0, [], md)
    for depth, cid, n, sub, body in rows:
        print('%s%-4s %9d %-4s  @0x%X' % ('  ' * depth, cid, n, sub, body))
