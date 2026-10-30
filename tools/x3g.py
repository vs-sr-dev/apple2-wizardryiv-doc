"""Read the `.x3g` / `.x3d` 3D object files.

    .x3d   FORM VCDO { EXVL, PLST }                     one object
    .x3g   FORM O3DG { OFFS, FORM VCDO x N, [VFTX] }    a group of objects

`EXVL` is the vertex table and decodes cleanly:

    UWORD  vertex count
    repeat:
        WORD  x, WORD y, WORD z        model space, signed
        BYTE  scratch[10]              zero on disc
    BYTE[] optional even-length tail   73 of 367 objects have one

The tail reads as byte-sized indices -- on 42 of the 73 every byte is inside
the object's own vertex range -- but not on all of them, so what it indexes is
an open question.

`PLST` is the polygon list and is only partly understood -- see
docs/12-open-questions.md.  Its first two words are 0 and 0x28/0x2C/0x2E,
which is a header length, and what follows contains the object's bounding
box in the four words before the first polygon.

    x3g.py FILE            chunk tree, vertex counts, bounding boxes
    x3g.py FILE --verts N  print object N's vertices
"""
import sys, struct
from iff import walk


def objects(d):
    """-> [(exvl_off, exvl_len, plst_off, plst_len)] in file order."""
    out, cur = [], {}
    for depth, cid, n, sub, body in walk(d, 0, len(d), 0, [], 8):
        if cid == 'FORM' and sub == 'VCDO':
            cur = {}
        elif cid == 'EXVL':
            cur['e'] = (body, n)
        elif cid == 'PLST':
            cur['p'] = (body, n)
            if 'e' in cur:
                out.append((cur['e'][0], cur['e'][1], body, n))
    return out


def verts(d, off, n):
    count = struct.unpack_from('>H', d, off)[0]
    stored = (n - 2) // 16
    for i in range(min(count, stored)):
        yield struct.unpack_from('>3h', d, off + 2 + i * 16)


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    objs = objects(d)
    if len(sys.argv) > 2 and sys.argv[2] == '--verts':
        i = int(sys.argv[3])
        eo, en, po, pn = objs[i]
        for j, v in enumerate(verts(d, eo, en)):
            print('%4d  %6d %6d %6d' % ((j,) + v))
        sys.exit()
    print('%s  %d bytes, %d objects' % (sys.argv[1], len(d), len(objs)))
    print('%4s %8s %6s %8s %8s  %s'
          % ('obj', 'EXVL', 'count', 'declared', 'PLST', 'bounding box'))
    for i, (eo, en, po, pn) in enumerate(objs):
        c = struct.unpack_from('>H', d, eo)[0]
        vs = list(verts(d, eo, en))
        bb = ''
        if vs:
            bb = 'x %d..%d  y %d..%d  z %d..%d' % (
                min(v[0] for v in vs), max(v[0] for v in vs),
                min(v[1] for v in vs), max(v[1] for v in vs),
                min(v[2] for v in vs), max(v[2] for v in vs))
        slack = en - 2 - c * 16
        print('%4d %8d %6d %8d %8d  %s%s'
              % (i, en, c, 2 + c * 16, pn, bb,
                 '   (+%d-byte index tail)' % slack if slack else ''))
