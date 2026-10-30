#!/usr/bin/env python3
"""pdframes.py -- the seven `*dat.bin` / `*pal.bin` pairs of Power Drive
(CD32, 1994): headerless planar frames that close by arithmetic, and the
geometry that was read out of the bytes rather than guessed.

WHAT THE BYTES GAVE (this repository's docs/05)
------------------------------------------------
Each pair is a frame file and a palette file.  The palette file is 96 bytes
per frame -- 32 colours x 3 bytes of 8-bit RGB (the first triple of every
car's frame 0 is 00 00 00) -- so the frame count is `len(pal) / 96`, and the
frame size is `len(dat) / count`, which is a whole number on all seven pairs:

    six cars    22,528 B per frame  = 11 CD sectors   (139+82+83+80+82+117 = 583 frames)
    usg         11,264 B per frame  = 5.5 CD sectors  (820 frames)

The geometry inside a frame has no header.  It was found by two measurements
that this tool repeats (`--probe`):

  * the byte-equality rate at lag L over the first frames peaks at the row
    stride: 30 bytes (240 px) on the six cars, 28 bytes (224 px) on usg;
  * the row-pair equality with that stride dips to ~0 at the plane
    boundaries: on astdat.bin the dip after row 300 with 150-row planes;
    32 colours = 5 planes;  30 x 150 x 5 = 22,500 (+28 bytes of sector
    padding), 28 x 80 x 5 = 11,200 (+64).

So: cars 240 x 150 x 5 contiguous planes, usg 224 x 80 x 5 contiguous
planes, one 32-entry RGB888 palette per frame.  The owner recognised the
rendered frame 0 of astdat.bin as a car seen head-on; frame 800 of usg reads
`PRODUCTION`.  Nothing here is chunky: the byte values above 31 (62-73 % of
the car bytes) rule out an 8-bit index into a 32-colour palette before any
render is made.

    python tools/pdframes.py census DIR                      the seven pairs by arithmetic
    python tools/pdframes.py probe DIR/astdat.bin 22528      stride and plane dips
    python tools/pdframes.py render DIR/astdat.bin DIR/astpal.bin N out.png [--scale 2]
    python tools/pdframes.py sheet DIR/astdat.bin DIR/astpal.bin out.png [--cols 12] [--every 1]
    python tools/pdframes.py --selftest

Renders stay in _work/: the repository publishes no image of the object.
"""
import argparse, os, sys, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dirguard, nameguard

PAL_ENTRY = 96          # 32 x RGB888
PAIRS = ('ast', 'cel', 'cli', 'cos', 'fia', 'min', 'usg')
GEOM = {22528: (240, 150, 5, 28), 11264: (224, 80, 5, 64)}   # w, h, planes, padding


def u8(b):
    return b


def frame_geometry(frame_size):
    """(w, h, planes, pad) for a known frame size, or None."""
    return GEOM.get(frame_size)


def census(root):
    rows = []
    for stem in PAIRS:
        dp = os.path.join(root, stem + 'dat.bin')
        pp = os.path.join(root, stem + 'pal.bin')
        if not (os.path.isfile(dp) and os.path.isfile(pp)):
            rows.append((stem, None))
            continue
        ds, ps = os.path.getsize(dp), os.path.getsize(pp)
        n, rem = divmod(ps, PAL_ENTRY)
        fs, frem = divmod(ds, n) if n else (0, ds)
        g = frame_geometry(fs)
        rows.append((stem, (ds, ps, n, rem, fs, frem, g)))
    return rows


def print_census(root):
    rows = census(root)
    print('pair     dat bytes   pal bytes  frames  pal rem  frame bytes  rem  geometry (w x h x planes + pad)')
    tf = tb = 0
    found = 0
    for stem, r in rows:
        if r is None:
            print('%-6s   (pair missing)' % stem)
            continue
        found += 1
        ds, ps, n, rem, fs, frem, g = r
        gs = ('%d x %d x %d + %d' % g) if g else 'unknown'
        print('%-6s %11d %11d  %6d  %7d  %11d  %3d  %s' % (stem, ds, ps, n, rem, fs, frem, gs))
        tf += n
        tb += ds
    print('%d of %d pairs present; %d frames; %d frame bytes' % (found, len(PAIRS), tf, tb))
    if found == 0:
        sys.exit('pdframes: no *dat.bin/*pal.bin pair under %s -- a census of nothing is refused' % root)
    return rows


def equality_rate(buf, lag):
    n = len(buf) - lag
    if n <= 0:
        return 0.0
    try:
        import numpy as np
        a = np.frombuffer(buf, dtype=np.uint8)
        return 100.0 * float(np.mean(a[:-lag] == a[lag:]))
    except ImportError:
        return 100.0 * sum(1 for i in range(n) if buf[i] == buf[i + lag]) / n


def probe(path, frame_size, nframes=3, maxlag=200):
    d = open(path, 'rb').read()[:frame_size * nframes]
    rates = {lag: equality_rate(d, lag) for lag in range(1, maxlag + 1)}
    peaks = [l for l in range(2, maxlag) if rates[l] > rates[l - 1] and rates[l] >= rates[l + 1]]
    peaks.sort(key=lambda l: -rates[l])
    stride = peaks[0] if peaks else None
    out = {'stride': stride, 'peaks': [(l, rates[l]) for l in peaks[:6]]}
    if stride:
        rows = frame_size // stride
        f = d[:rows * stride]
        pairs = []
        for r in range(rows - 1):
            a = f[r * stride:(r + 1) * stride]
            b = f[(r + 1) * stride:(r + 2) * stride]
            pairs.append(100.0 * sum(1 for i in range(stride) if a[i] == b[i]) / stride)
        dips = sorted(range(len(pairs)), key=lambda i: pairs[i])[:5]
        out['rows'] = rows
        out['dips'] = sorted((i + 1, pairs[i]) for i in dips)
        for planes in (4, 5, 6, 8):
            per = (frame_size // planes) // stride
            out['planes %d' % planes] = [round(pairs[k * per - 1], 1) for k in range(1, planes) if k * per - 1 < len(pairs)]
    return out


def print_probe(path, frame_size):
    r = probe(path, frame_size)
    print('%s  frame %d bytes' % (os.path.basename(path), frame_size))
    print('  equality-rate peaks (lag: %%): %s' % ', '.join('%d: %.1f' % p for p in r['peaks']))
    print('  row stride = %s bytes = %s px' % (r['stride'], r['stride'] * 8 if r['stride'] else '?'))
    if r.get('rows'):
        print('  rows of that stride in a frame: %d; deepest row-pair dips after row: %s'
              % (r['rows'], ', '.join('%d (%.1f %%)' % x for x in r['dips'])))
        for planes in (4, 5, 6, 8):
            print('  %d planes -> equality at the plane boundaries: %s' % (planes, r['planes %d' % planes]))


def read_frame(dat, pal, index, geom):
    w, h, planes, pad = geom
    fs = w // 8 * h * planes + pad
    f = dat[index * fs:(index + 1) * fs]
    p = pal[index * PAL_ENTRY:(index + 1) * PAL_ENTRY]
    if len(f) < fs - pad or len(p) < PAL_ENTRY:
        raise IndexError('frame %d out of range' % index)
    bpr = w // 8
    px = [[0] * w for _ in range(h)]
    for m in range(planes):
        for y in range(h):
            base = m * bpr * h + y * bpr
            row = px[y]
            for xb in range(bpr):
                b = f[base + xb]
                if not b:
                    continue
                for k in range(8):
                    if b & (0x80 >> k):
                        row[xb * 8 + k] |= 1 << m
    cols = [tuple(p[i:i + 3]) for i in range(0, PAL_ENTRY, 3)]
    return px, cols


def to_image(px, cols, scale=1):
    from PIL import Image
    h, w = len(px), len(px[0])
    im = Image.new('RGB', (w, h))
    put = im.load()
    for y in range(h):
        r = px[y]
        for x in range(w):
            put[x, y] = cols[r[x]]
    if scale > 1:
        im = im.resize((w * scale, h * scale), Image.NEAREST)
    return im


def cmd_render(a):
    dat = open(dirguard.want_file(a.dat, 'pdframes'), 'rb').read()
    pal = open(dirguard.want_file(a.pal, 'pdframes'), 'rb').read()
    n = len(pal) // PAL_ENTRY
    fs = len(dat) // n
    g = frame_geometry(fs)
    if g is None:
        sys.exit('pdframes: frame size %d has no known geometry (run probe)' % fs)
    px, cols = read_frame(dat, pal, a.index, g)
    to_image(px, cols, a.scale).save(a.out)
    print('%s frame %d of %d: %d x %d x %d planes -> %s' % (os.path.basename(a.dat), a.index, n, g[0], g[1], g[2], a.out))


def cmd_sheet(a):
    from PIL import Image
    dat = open(dirguard.want_file(a.dat, 'pdframes'), 'rb').read()
    pal = open(dirguard.want_file(a.pal, 'pdframes'), 'rb').read()
    n = len(pal) // PAL_ENTRY
    fs = len(dat) // n
    g = frame_geometry(fs)
    if g is None:
        sys.exit('pdframes: frame size %d has no known geometry (run probe)' % fs)
    idx = list(range(0, n, a.every))
    w, h = g[0], g[1]
    rows = (len(idx) + a.cols - 1) // a.cols
    sheet = Image.new('RGB', (w * a.cols, h * rows))
    for k, i in enumerate(idx):
        px, cols = read_frame(dat, pal, i, g)
        sheet.paste(to_image(px, cols), ((k % a.cols) * w, (k // a.cols) * h))
    sheet.save(a.out)
    print('%s: %d of %d frames on a %d x %d sheet -> %s' % (os.path.basename(a.dat), len(idx), n, a.cols, rows, a.out))


def selftest():
    import tempfile, struct
    fails = 0

    def check(name, ok):
        nonlocal fails
        print('  %-70s %s' % (name, 'ok' if ok else 'FAIL'))
        if not ok:
            fails += 1

    # a synthetic 3-frame car pair: 240 x 150 x 5 with a diagonal in plane 0
    w, h, planes, pad = GEOM[22528]
    bpr = w // 8
    frame = bytearray(bpr * h * planes + pad)
    # every row of every plane carries the same pseudo-random 30-byte pattern
    # (so the equality rate peaks at the stride, as on the object), except
    # that plane 0 also marches one pixel per row for the pixel checks
    seed = 12345
    pattern = bytearray()
    for _ in range(bpr):
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        pattern.append((seed >> 16) & 0x7f)          # bit 7 clear: the marching pixel owns it
    # the pattern drifts one byte every four rows, so that lag 30 beats its
    # harmonics (60, 90 ...) as it does on a real image
    for m in range(planes):
        for y in range(h):
            k = (y // 4) % bpr
            frame[m * bpr * h + y * bpr: m * bpr * h + (y + 1) * bpr] = pattern[k:] + pattern[:k]
    for y in range(h):
        frame[y * bpr + (y % bpr)] |= 0x80           # plane 0: one pixel per row, marching
    dat = bytes(frame) * 3
    pal = bytes(range(96)) * 3
    px, cols = read_frame(dat, pal, 1, GEOM[22528])
    check('synthetic frame: pixel (0,0) has bit 0 from the marching plane-0 pixel', px[0][0] & 1 == 1)
    check('synthetic frame: pixel (8,1) has bit 0 (row 1, byte 1)', px[1][8] & 1 == 1)
    check('synthetic frame: pixel (0,1) has no bit 0 (plane 0 byte 0 of row 1 is the pattern, bit 7 clear)', px[1][0] & 1 == 0)
    check('palette entry 1 is bytes 3..5', cols[1] == (3, 4, 5))
    with tempfile.TemporaryDirectory() as td:
        open(os.path.join(td, 'astdat.bin'), 'wb').write(dat)
        open(os.path.join(td, 'astpal.bin'), 'wb').write(pal)
        rows = census(td)
        r = dict(rows)['ast']
        check('census: 3 frames of 22,528 from the palette arithmetic', r[2] == 3 and r[4] == 22528 and r[5] == 0)
        check('census: geometry 240 x 150 x 5 + 28 attached', r[6] == (240, 150, 5, 28))
        check('census: the six absent pairs are reported missing', sum(1 for _, x in rows if x is None) == 6)
        pr = probe(os.path.join(td, 'astdat.bin'), 22528, nframes=1, maxlag=64)
        check('probe: the synthetic stride 30 is the top equality peak', pr['stride'] == 30)
        try:
            import numpy  # noqa
            check('probe uses numpy when present', True)
        except ImportError:
            check('probe falls back to pure python without numpy', True)
        # empty tree is refused
        empty = os.path.join(td, 'empty')
        os.mkdir(empty)
        try:
            buf = io.StringIO()
            old = sys.stdout
            sys.stdout = buf
            try:
                print_census(empty)
                refused = False
            except SystemExit:
                refused = True
            finally:
                sys.stdout = old
        except Exception:
            refused = False
        check('a census over a tree with no pair refuses', refused)
    check('frame_geometry of an unknown size is None', frame_geometry(12345) is None)
    print('%d checks, %d failures' % (11, fails))
    return fails


def main():
    nameguard.guard()
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--selftest', action='store_true')
    sub = ap.add_subparsers(dest='cmd')
    c = sub.add_parser('census'); c.add_argument('root')
    p = sub.add_parser('probe'); p.add_argument('dat'); p.add_argument('frame_size', type=int)
    r = sub.add_parser('render'); r.add_argument('dat'); r.add_argument('pal'); r.add_argument('index', type=int); r.add_argument('out'); r.add_argument('--scale', type=int, default=1)
    s = sub.add_parser('sheet'); s.add_argument('dat'); s.add_argument('pal'); s.add_argument('out'); s.add_argument('--cols', type=int, default=12); s.add_argument('--every', type=int, default=1)
    a = ap.parse_args()
    if a.selftest:
        sys.exit(1 if selftest() else 0)
    if a.cmd == 'census':
        print_census(dirguard.want_tree(a.root, 'pdframes'))
    elif a.cmd == 'probe':
        print_probe(dirguard.want_file(a.dat, 'pdframes'), a.frame_size)
    elif a.cmd == 'render':
        cmd_render(a)
    elif a.cmd == 'sheet':
        cmd_sheet(a)
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
