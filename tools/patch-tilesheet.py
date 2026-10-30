#!/usr/bin/env python3
"""Add a --layout option to tools/tilesheet.py.

The first render assumed the four bitplanes of a tile were stored one after the
other (plane-contiguous).  It produced coherent shapes cut by horizontal banding
at a 16-pixel pitch, which is the signature of reading an interleaved bitmap as
a contiguous one.  Amiga tile banks are commonly stored *row-interleaved*: for
each of the 16 rows, the four planes' two bytes each, so one row costs 8 bytes
and one tile 128 -- the same 128 the length evidence gives, so the byte count
cannot distinguish the two layouts.  Only the rendering can, which is exactly
why the checklist asks for planes to be looked at before geometry is asserted.

This patch keeps both readings available and makes neither the silent default:
`--layout contig` and `--layout inter`, printed in the output either way.
"""
import io

P = 'tools/tilesheet.py'
s = io.open(P, encoding='utf-8').read()

old = '''def decode_tile(blob, ti):
    """Return a 16x16 array of 0..15 colour indices for tile `ti`.

    Tiles are stored plane-contiguous within the tile: plane 0's 32 bytes,
    then plane 1's, and so on.  That is the layout that makes each tile a
    self-contained 128-byte unit, which is what the length evidence implies.
    """
    base = ti * TILE
    px = [[0] * TW for _ in range(TH)]
    for p in range(PLANES):
        for y in range(TH):
            o = base + p * (TH * TW // 8) + y * (TW // 8)
            if o + 1 >= len(blob):
                continue
            word = (blob[o] << 8) | blob[o + 1]
            for x in range(TW):
                if word & (0x8000 >> x):
                    px[y][x] |= (1 << p)
    return px'''

new = '''def plane_row_offset(base, p, y, layout):
    """Byte offset of plane `p`, row `y` of the tile starting at `base`.

    contig  plane 0's 32 bytes, then plane 1's, ...  (plane-contiguous)
    inter   row 0 planes 0..3, row 1 planes 0..3, ... (row-interleaved)

    Both cost exactly 128 bytes per tile, so the length evidence cannot choose
    between them; the render can.
    """
    if layout == 'contig':
        return base + p * (TH * TW // 8) + y * (TW // 8)
    return base + y * (TW // 8) * PLANES + p * (TW // 8)


def decode_tile(blob, ti, layout='inter'):
    """Return a 16x16 array of 0..15 colour indices for tile `ti`."""
    base = ti * TILE
    px = [[0] * TW for _ in range(TH)]
    for p in range(PLANES):
        for y in range(TH):
            o = plane_row_offset(base, p, y, layout)
            if o + 1 >= len(blob):
                continue
            word = (blob[o] << 8) | blob[o + 1]
            for x in range(TW):
                if word & (0x8000 >> x):
                    px[y][x] |= (1 << p)
    return px'''

assert s.count(old) == 1, "decode_tile anchor not unique"
s = s.replace(old, new, 1)

old2 = "    ap.add_argument('--planes', action='store_true')"
new2 = ("    ap.add_argument('--planes', action='store_true')\n"
        "    ap.add_argument('--layout', choices=('inter', 'contig'), default='inter',\n"
        "                    help='tile-internal bitplane layout; printed either way')")
assert s.count(old2) == 1, "argparse anchor not unique"
s = s.replace(old2, new2, 1)

old3 = """                base = ti * TILE + p * (TH * TW // 8)
                for y in range(TH):
                    o = base + y * 2"""
new3 = """                base = ti * TILE
                for y in range(TH):
                    o = plane_row_offset(base, p, y, a.layout)"""
assert s.count(old3) == 1, "plane render anchor not unique"
s = s.replace(old3, new3, 1)

old4 = "        px = decode_tile(blob, ti)"
new4 = "        px = decode_tile(blob, ti, a.layout)"
assert s.count(old4) == 1, "decode call anchor not unique"
s = s.replace(old4, new4, 1)

old5 = '''    print("%s: %d bytes = %d tiles of 16x16x4" % (a.file, len(blob), n))'''
new5 = '''    print("%s: %d bytes = %d tiles of 16x16x4, layout=%s"
          % (a.file, len(blob), n, a.layout))'''
assert s.count(old5) == 1, "print anchor not unique"
s = s.replace(old5, new5, 1)

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print("patched %s" % P)
