"""wiz4maze.py -- the level maps inside Wizardry IV's SCENARIO.DATA.

A level record starts on a block boundary (odd blocks 99..127 of SCENARIO.DATA
on this pressing, one record every 1,024 bytes). It opens with four wall
arrays of 120 bytes -- WEST, SOUTH, EAST, NORTH, the order of the original
Wizardry TMAZE record -- each 20 columns x 6 bytes, a column being 20 two-bit
values packed least significant first (40 bits, the sixth byte zero):

    0 open   1 wall   2 door   3 hidden door (Wizardry I's TWALL names)

then, at +480, a 1-bit-per-square grid (20 columns x 4 bytes) and, at +560, a
4-bit-per-square grid (20 columns x 10 bytes). x runs 0..19 west to east, y
0..19 south to north.

THE CLOSURE: a real map mostly agrees with itself -- the east wall of (x,y) is the
west wall of (x+1,y), the north wall of (x,y) the south wall of (x,y+1). The
tool prints both agreement ratios for every candidate record and calls a
record a level only above 0.95 on both. A random block scores about 0.4.
Wizardry has one-way walls, so a dense record between 0.6 and 0.95 is listed
separately rather than discarded (blocks 107, 111 and 127 on this pressing).

Usage:
    python tools/wiz4maze.py SCENARIO.DATA                    # census of level records
    python tools/wiz4maze.py SCENARIO.DATA --ascii BLOCK      # one level as ASCII
    python tools/wiz4maze.py SCENARIO.DATA --ascii BLOCK --crop X0 X1 Y0 Y1
    python tools/wiz4maze.py SCENARIO.DATA --png OUT.png      # all levels, one sheet (needs PIL)
    python tools/wiz4maze.py --selftest
"""
import sys

REC = 1024


def walls(s, r, k):
    a = s[r + 120 * k:r + 120 * k + 120]
    return [[(a[6 * x + (2 * y) // 8] >> ((2 * y) % 8)) & 3 for y in range(20)] for x in range(20)]


def level(s, blk):
    r = blk * 512
    if r + 640 > len(s):
        return None
    return [walls(s, r, k) for k in range(4)]


def agreement(L):
    W, S, E, N = L
    ew = sum(E[x][y] == W[x + 1][y] for x in range(19) for y in range(20)) / 380.0
    ns = sum(N[x][y] == S[x][y + 1] for x in range(20) for y in range(19)) / 380.0
    return ew, ns


def census(s):
    out = []
    for blk in range(len(s) // 512):
        L = level(s, blk)
        if L is None:
            continue
        ew, ns = agreement(L)
        nz = sum(v != 0 for a in L for c in a for v in c)
        out.append((blk, ew, ns, nz, ew > 0.95 and ns > 0.95 and nz > 40))
    return out


def ascii(L, x0=0, x1=20, y0=0, y1=20):
    W, S, E, N = L
    hz = {0: '   ', 1: '---', 2: '-D-', 3: '-?-'}
    vt = {0: ' ', 1: '|', 2: 'D', 3: '?'}
    rows = []
    for y in range(y1 - 1, y0 - 1, -1):
        rows.append('%2d ' % y + ''.join('+' + hz[N[x][y]] for x in range(x0, x1)) + '+')
        rows.append('   ' + ''.join(vt[W[x][y]] + '   ' for x in range(x0, x1)) + vt[E[x1 - 1][y]])
    rows.append('   ' + ''.join('+' + hz[S[x][y0]] for x in range(x0, x1)) + '+')
    rows.append('   ' + ''.join(' %-3d' % x for x in range(x0, x1)))
    return '\n'.join(rows)


def png(s, out):
    from PIL import Image, ImageDraw
    levels = [c[0] for c in census(s) if c[4]]
    C = 12
    cols = 5
    rws = (len(levels) + cols - 1) // cols
    im = Image.new('RGB', (cols * (20 * C + 30), rws * (20 * C + 40)), (20, 20, 20))
    d = ImageDraw.Draw(im)
    colr = {1: (230, 230, 230), 2: (240, 170, 40), 3: (90, 160, 255)}
    for i, blk in enumerate(levels):
        W, S, E, N = level(s, blk)
        ox, oy = (i % cols) * (20 * C + 30) + 10, (i // cols) * (20 * C + 40) + 25
        d.text((ox, oy - 18), 'block %d' % blk, fill=(200, 200, 90))
        for x in range(20):
            for y in range(20):
                X, Y = ox + x * C, oy + (19 - y) * C
                for v, seg in ((W[x][y], (X, Y, X, Y + C)), (E[x][y], (X + C, Y, X + C, Y + C)),
                               (N[x][y], (X, Y, X + C, Y)), (S[x][y], (X, Y + C, X + C, Y + C))):
                    if v:
                        d.line(seg, fill=colr[v], width=2)
    im.save(out)
    print('wrote %s, %d levels' % (out, len(levels)))


def selftest():
    ok = 0
    s = bytearray(2048)
    # a 20x20 box: west wall on x=0, east wall on x=19, south on y=0, north on y=19,
    # and one interior wall between (4,4) and (5,4) written on both sides
    def put(k, x, y, v):
        o = 120 * k + 6 * x + (2 * y) // 8
        s[o] |= v << ((2 * y) % 8)
    for y in range(20):
        put(0, 0, y, 1)
        put(2, 19, y, 1)
    for x in range(20):
        put(1, x, 0, 1)
        put(3, x, 19, 1)
    put(2, 4, 4, 2)
    put(0, 5, 4, 2)
    L = level(bytes(s), 0)
    ew, ns = agreement(L)
    assert ew == 1.0 and ns == 1.0; ok += 1
    put(2, 7, 7, 1)  # an east wall with no matching west wall
    ew, ns = agreement(level(bytes(s), 0))
    assert ew < 1.0 and ns == 1.0; ok += 1
    rnd = bytes((i * 37 + 11) % 256 for i in range(2048))
    ew, ns = agreement(level(rnd, 0))
    assert ew < 0.95 or ns < 0.95; ok += 1
    assert '-D-' in ascii(L) or 'D' in ascii(L); ok += 1
    print('selftest: %d checks, 0 failures' % ok)


def main(a):
    if not a or a[0] == '--selftest':
        return selftest()
    s = open(a[0], 'rb').read()
    if '--png' in a:
        return png(s, a[a.index('--png') + 1])
    if '--ascii' in a:
        blk = int(a[a.index('--ascii') + 1])
        crop = (0, 20, 0, 20)
        if '--crop' in a:
            i = a.index('--crop')
            crop = tuple(int(v) for v in a[i + 1:i + 5])
        L = level(s, blk)
        ew, ns = agreement(L)
        print('block %d   E/W agreement %.3f   N/S agreement %.3f' % (blk, ew, ns))
        print(ascii(L, *crop))
        return 0
    lv = 0
    print('block   E/W     N/S    walls  level?')
    for blk, ew, ns, nz, isl in census(s):
        oneway = (not isl) and nz > 300 and ew > 0.6 and ns > 0.6
        if isl or oneway:
            print('%5d   %.3f   %.3f   %4d   %s' % (blk, ew, ns, nz,
                  'LEVEL' if isl else 'one-sided walls? (agreement below 0.95 on a dense map)'))
        lv += isl
    print('level records: %d' % lv)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
