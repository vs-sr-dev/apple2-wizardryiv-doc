"""wiz4virt.py -- the virtual drive of Wizardry IV (Apple II), rebuilt from its own map.

The boot side's Pascal directory describes a 2,048-block volume. No side holds
it: each side holds an ordered subset of its blocks, compacted, and the map of
which subset is where is the file SYSTEM.RELOC (blocks 6..9 of side A):

    word 0          2 (not resolved; constant on this pressing)
    then, per side: side number, extent count N, then N triples
                    (virtual first block, physical first block, block count)
    a side number of 0 ends the list.

This tool reads that map from side A, checks it (extents of each side tile
the physical blocks from 0 with no gap and no overlap; no side exceeds 280),
assembles the virtual volume, and CHECKS EVERY VIRTUAL BLOCK THAT MORE THAN
ONE SIDE CARRIES FOR BYTE IDENTITY. Blocks 0 and 1 of every side are local
(boot block and identity block) and are reported, not compared.

Usage:
    python tools/wiz4virt.py SIDE_A SIDE_B ... SIDE_E            # map + audit
    python tools/wiz4virt.py SIDE_A ... SIDE_E --volume OUT      # the virtual volume
    python tools/wiz4virt.py SIDE_A ... SIDE_E --extract DIR     # its files, by directory
    python tools/wiz4virt.py --selftest
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a2pascal  # noqa: E402

BLOCK = 512


class Refused(Exception):
    pass


def side_number(img):
    """Byte 510 of block 1 is the side number on every side of this pressing."""
    b1 = a2pascal.block(img, 1)
    return b1[510], b1[480:496].decode('latin-1')


def read_map(reloc):
    w = struct.unpack_from('<%dH' % (len(reloc) // 2), reloc)
    head = w[0]
    i = 1
    sides = {}
    while i < len(w) and w[i] != 0:
        side, n = w[i], w[i + 1]
        if not 1 <= side <= 16 or not 1 <= n <= 64:
            raise Refused('side record at word %d: side %d count %d' % (i, side, n))
        ex = [tuple(w[i + 2 + 3 * k:i + 5 + 3 * k]) for k in range(n)]
        sides[side] = ex
        i += 2 + 3 * n
    return head, sides, i


def check_map(sides):
    for s, ex in sides.items():
        p = 0
        for v, ph, n in ex:
            if ph != p:
                raise Refused('side %d: extent at phys %d, expected %d' % (s, ph, p))
            p += n
        if p > a2pascal.BLOCKS:
            raise Refused('side %d uses %d blocks' % (s, p))
        vs = sorted(ex)
        for (v0, _, n0), (v1, _, _) in zip(vs, vs[1:]):
            if v0 + n0 > v1:
                raise Refused('side %d: virtual extents overlap at %d' % (s, v1))


def assemble(imgs, sides):
    """imgs: side number -> image bytes. Returns (volume dict v->bytes, carriers v->[sides], conflicts)."""
    blk = {s: a2pascal.blocks(img) for s, img in imgs.items()}
    vol, car, conf = {}, {}, []
    for s, ex in sorted(sides.items()):
        for v, ph, n in ex:
            for k in range(n):
                data = blk[s][(ph + k) * BLOCK:(ph + k + 1) * BLOCK]
                vv = v + k
                car.setdefault(vv, []).append(s)
                if vv < 2:
                    continue
                if vv in vol and vol[vv] != data:
                    conf.append((vv, s))
                vol.setdefault(vv, data)
    return vol, car, conf


def load(paths):
    imgs = {}
    for p in paths:
        img = open(p, 'rb').read()
        s, stamp = side_number(img)
        imgs[s] = img
        print('side %d  identity "%s"  %s' % (s, stamp, os.path.basename(p)))
    if 1 not in imgs:
        raise Refused('no side 1 among the inputs')
    hdr, ents, _ = a2pascal.parse(imgs[1])
    reloc = [e for e in ents if e['name'] == 'SYSTEM.RELOC']
    if not reloc:
        raise Refused('side 1 has no SYSTEM.RELOC')
    e = reloc[0]
    raw = a2pascal.blocks(imgs[1])[e['first'] * BLOCK:e['last'] * BLOCK]
    head, sides, end = read_map(raw)
    check_map(sides)
    return imgs, hdr, ents, head, sides, end, raw


def report(paths):
    imgs, hdr, ents, head, sides, end, raw = load(paths)
    print()
    print('SYSTEM.RELOC word 0 : %d' % head)
    print('side records        : %d, list ends at word %d (byte %d of %d)' % (len(sides), end, 2 * end, len(raw)))
    for s, ex in sorted(sides.items()):
        used = sum(n for _, _, n in ex)
        print('  side %d: %2d extents, %3d physical blocks used, %3d free' % (s, len(ex), used, a2pascal.BLOCKS - used))
        for v, ph, n in ex:
            print('      virtual %4d..%4d  -> physical %3d..%3d  (%d)' % (v, v + n - 1, ph, ph + n - 1, n))
    missing = [s for s in sides if s not in imgs]
    vol, car, conf = assemble({s: imgs[s] for s in sides if s in imgs}, sides)
    print()
    print('sides supplied      : %s   missing: %s' % (sorted(imgs), missing or 'none'))
    multi = [v for v in car if v >= 2 and len(car[v]) > 1]
    print('virtual blocks held : %d distinct (0..%d)' % (len(car), max(car)))
    print('held by >1 side     : %d   byte-identical: %d   CONFLICTS: %d' % (
        len(multi), len(multi) - len(set(v for v, _ in conf)), len(set(v for v, _ in conf))))
    for v, s in conf[:20]:
        print('   conflict: virtual %d differs on side %d' % (v, s))
    hist = {}
    for v in car:
        hist[len(car[v])] = hist.get(len(car[v]), 0) + 1
    print('carriers histogram  : %s' % ', '.join('%d side(s): %d' % kv for kv in sorted(hist.items())))
    print()
    print('directory files against the map:')
    for e in ents:
        rng = range(e['first'], e['last'])
        have = [v for v in rng if v in car]
        sides_of = sorted(set(s for v in have for s in car[v]))
        print('  %-15s %4d..%4d  %4d blocks  mapped %4d  (%s)  on sides %s' % (
            e['name'], e['first'], e['last'] - 1, len(rng), len(have),
            'all' if len(have) == len(rng) else ('NONE' if not have else 'PART'),
            ''.join('ABCDEF'[s - 1] for s in sides_of) or '-'))
    return vol, ents


def main(argv):
    if not argv or argv[0] == '--selftest':
        return selftest()
    paths = [a for a in argv if not a.startswith('--')]
    if '--volume' in argv or '--extract' in argv:
        out = argv[argv.index('--volume' if '--volume' in argv else '--extract') + 1]
        paths = [p for p in paths if p != out]
        imgs, hdr, ents, head, sides, end, raw = load(paths)
        vol, car, conf = assemble({s: imgs[s] for s in sides if s in imgs}, sides)
        if '--volume' in argv:
            top = max(vol) + 1
            data = b''.join(vol.get(v, b'\0' * BLOCK) for v in range(top))
            open(out, 'wb').write(data)
            print('wrote %d blocks (%d bytes), %d of them unmapped and zero-filled' % (
                top, len(data), sum(1 for v in range(2, top) if v not in vol)))
        else:
            os.makedirs(out, exist_ok=True)
            for e in ents:
                rng = range(e['first'], e['last'])
                have = [v for v in rng if v in vol]
                if not have:
                    print('  %-15s not on any side -- skipped' % e['name'])
                    continue
                gaps = [v for v in rng if v not in vol]
                data = b''.join(vol.get(v, b'\0' * BLOCK) for v in rng)
                if gaps:
                    print('  %-15s %d unmapped block(s) zero-filled: virtual %s' % (
                        e['name'], len(gaps), ','.join(map(str, gaps))))
                data = data[:len(data) - BLOCK + e['lastbyte']]
                open(os.path.join(out, e['name']), 'wb').write(data)
                print('  %-15s %7d bytes' % (e['name'], len(data)))
        return 0
    try:
        report(paths)
    except (Refused, a2pascal.Refused) as r:
        print('REFUSED: %s' % r)
        return 1
    return 0


def selftest():
    ok = 0
    words = [2, 1, 2, 0, 0, 10, 50, 10, 5, 2, 1, 0, 0, 2, 0]
    raw = struct.pack('<%dH' % len(words), *words)
    head, sides, end = read_map(raw)
    assert head == 2 and sides == {1: [(0, 0, 10), (50, 10, 5)], 2: [(0, 0, 2)]}; ok += 1
    check_map(sides); ok += 1
    for bad in ({1: [(0, 0, 10), (50, 11, 5)]}, {1: [(0, 0, 10), (5, 10, 5)]}, {1: [(0, 0, 281)]}):
        try:
            check_map(bad)
            raise AssertionError('accepted %r' % bad)
        except Refused:
            ok += 1
    try:
        read_map(struct.pack('<4H', 2, 99, 1, 0))
        raise AssertionError('accepted side 99')
    except Refused:
        ok += 1
    print('selftest: %d checks, 0 failures' % ok)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
