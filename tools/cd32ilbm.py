#!/usr/bin/env python3
"""Render IFF ILBM images, and the ILBM frames inside an IFF ANIM, to PNG.

Handles both compression modes (0 = none, 1 = ByteRun1), reads the plane
count, size and page geometry from BMHD, the palette from CMAP, and the
display mode from CAMG where present.  ANIM files are walked as a chain of
FORM ILBM frames; only frames that carry their own BODY are rendered, which
for a delta-compressed ANIM means the key frames.

Usage: python3 tools/ilbm.py <file>... [--out DIR] [--limit N]
"""
import struct, sys, os, argparse


def chunks(d, o, end):
    while o + 8 <= end:
        cid = d[o:o + 4]
        ln = struct.unpack_from('>I', d, o + 4)[0]
        yield cid, o + 8, ln
        o += 8 + ln + (ln & 1)


def byterun1(src, want):
    out = bytearray()
    i = 0
    while len(out) < want and i < len(src):
        n = src[i]
        i += 1
        if n < 128:
            out += src[i:i + n + 1]
            i += n + 1
        elif n > 128:
            out += bytes([src[i]]) * (257 - n)
            i += 1
    return bytes(out[:want]), i


def render(body, w, h, planes, cmap, comp, masking):
    rb = ((w + 15) // 16) * 2
    nsrc = planes + (1 if masking == 1 else 0)
    px = bytearray(w * h)
    pos = 0
    for y in range(h):
        rows = []
        for p in range(nsrc):
            if comp == 1:
                row, used = byterun1(body[pos:pos + rb * 4 + 16], rb)
                pos += used
            else:
                row = body[pos:pos + rb]
                pos += rb
            rows.append(row)
        base = y * w
        for p in range(planes):
            row = rows[p]
            bit = 1 << p
            for x in range(w):
                if len(row) > (x >> 3) and (row[x >> 3] >> (7 - (x & 7))) & 1:
                    px[base + x] |= bit
    from PIL import Image
    im = Image.new('P', (w, h))
    im.putdata(bytes(px))
    pal = []
    for i in range(256):
        if i * 3 + 2 < len(cmap):
            pal += [cmap[i * 3], cmap[i * 3 + 1], cmap[i * 3 + 2]]
        else:
            pal += [0, 0, 0]
    im.putpalette(pal)
    return im


def do_ilbm(d, o, ln, name, out_dir, results):
    bmhd = cmap = body = camg = None
    for cid, co, cl in chunks(d, o + 4, o + ln):
        if cid == b'BMHD':
            bmhd = d[co:co + cl]
        elif cid == b'CMAP':
            cmap = d[co:co + cl]
        elif cid == b'CAMG':
            camg = struct.unpack_from('>I', d, co)[0]
        elif cid == b'BODY':
            body = d[co:co + cl]
    if not bmhd:
        return
    w, h, x, y, planes, masking, comp, pad, tc, xa, ya, pw, ph = \
        struct.unpack_from('>HHhhBBBBHBBhh', bmhd, 0)
    results.append(dict(name=name, w=w, h=h, planes=planes, comp=comp,
                        masking=masking, camg=camg,
                        colours=len(cmap) // 3 if cmap else 0,
                        page=(pw, ph), aspect=(xa, ya),
                        body=len(body) if body else 0))
    if body and out_dir:
        try:
            im = render(body, w, h, planes, cmap or b'', comp, masking)
            im.save(os.path.join(out_dir, name + '.png'))
        except Exception as e:
            print("   render failed for %s: %s" % (name, e))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--out')
    ap.add_argument('--limit', type=int, default=6)
    a = ap.parse_args()
    if a.out:
        os.makedirs(a.out, exist_ok=True)
    results = []
    for p in a.files:
        d = open(p, 'rb').read()
        base = os.path.basename(p)
        if d[:4] != b'FORM':
            continue
        ln = struct.unpack_from('>I', d, 4)[0]
        typ = d[8:12]
        if typ == b'ILBM':
            do_ilbm(d, 8, ln, base, a.out, results)
        elif typ == b'ANIM':
            n = 0
            for cid, co, cl in chunks(d, 12, 8 + ln):
                if cid == b'FORM' and d[co:co + 4] == b'ILBM':
                    n += 1
                    if n <= a.limit:
                        do_ilbm(d, co, cl, "%s.f%02d" % (base, n),
                                a.out, results)
            print("%s: ANIM with %d ILBM frames" % (base, n))
    print()
    print("%-28s %5s %5s %6s %5s %5s %8s %9s" %
          ("image", "w", "h", "planes", "comp", "cols", "CAMG", "BODY"))
    for r in results:
        print("%-28s %5d %5d %6d %5d %5d %8s %9d" %
              (r['name'], r['w'], r['h'], r['planes'], r['comp'], r['colours'],
               ("$%05X" % r['camg']) if r['camg'] is not None else "-", r['body']))


if __name__ == '__main__':
    main()
