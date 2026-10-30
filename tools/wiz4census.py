"""wiz4census.py -- the census scripts behind notes/ for apple2-wizardryiv-doc.

Each subcommand prints one notes file. Inputs are the six side images (in the
object directory) and the files extracted by a2pascal.py / wiz4virt.py into
_work (see docs/02-the-technical-sheet.md for the order).

    python tools/wiz4census.py identity  OBJDIR     > notes/side-identity.txt
    python tools/wiz4census.py stale     OBJDIR     > notes/stale-directory.txt
    python tools/wiz4census.py coverage  OBJDIR     > notes/coverage.txt
    python tools/wiz4census.py census    OBJDIR     > notes/census.txt
    python tools/wiz4census.py krn       WORK       > notes/krn-census.txt
    python tools/wiz4census.py interp    WORK       > notes/interp-strings.txt
    python tools/wiz4census.py data      WORK       > notes/data-files.txt
    python tools/wiz4census.py slack     WORK       > notes/slack-text.txt
"""
import collections
import glob
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a2pascal as A  # noqa: E402
import wiz4krn as K  # noqa: E402
import wiz4virt as V  # noqa: E402


def sides(objdir):
    imgs = {}
    for p in sorted(glob.glob(os.path.join(objdir, '*.dsk'))):
        im = open(p, 'rb').read()
        imgs[V.side_number(im)[0]] = (os.path.basename(p), im)
    return imgs


def identity(objdir):
    for s, (name, im) in sorted(sides(objdir).items()):
        b0, b1 = A.block(im, 0), A.block(im, 1)
        print('side %s (%d)  stamp %r  %s' % ('ABCDEF'[s - 1], b1[510], b1[480:496].decode(), name))
        print('   boot strings:', [m.group().decode() for m in re.finditer(rb'[\x20-\x7e]{8,}', b0 + b1[:480])])


def stale(objdir):
    im = sides(objdir)[1][1]
    hdr, ents, d = A.parse(im)
    print('directory region 2048 bytes = 78 slots of 26; header + %d live entries; slots %d..77' % (hdr['nfiles'], hdr['nfiles'] + 1))
    seen = {}
    for slot in range(hdr['nfiles'] + 1, 78):
        r = d[slot * 26:slot * 26 + 26]
        if not r.strip(b'\0'):
            print('slot %2d  empty' % slot)
            continue
        f, l, k = struct.unpack_from('<HHH', r, 0)
        n = r[6]
        dt = struct.unpack_from('<H', r, 24)[0]
        nm = r[7:7 + n].decode('latin-1') if 1 <= n <= 15 else r[7:22].split(b'\0')[0].decode('latin-1')
        print('slot %2d  %-15s %4d..%4d  %-8s %s  namelen %2d' % (slot, nm, f, l, A.KINDS.get(k & 15, '?'), A.pdate(dt), n))
        seen.setdefault(nm, []).append(slot)
    print('distinct names in stale slots: %d' % len(seen))
    print(', '.join(sorted(seen)))


def the_map(imgs):
    return V.read_map(A.blocks(imgs[1][1])[6 * 512:10 * 512])[1]


def coverage(objdir):
    imgs = sides(objdir)
    mp = the_map(imgs)
    cls = {}
    for s in range(1, 7):
        for b in (0, 1):
            cls[(s, b)] = 'decoded: boot+identity'
    bands = [((2, 5), 'decoded: directory'), ((6, 9), 'decoded: SYSTEM.RELOC map'),
             ((10, 35), 'identified: interpreter 6502 code'), ((36, 43), 'decoded: 200.CHARSET (rendered)'),
             ((44, 67), 'identified: WERDNA.DATA'), ((68, 69), 'identified: KANA.KEYMAP'),
             ((70, 70), 'decoded: codefile container'), ((71, 225), 'identified: p-code (container closed)'),
             ((226, 285), 'identified: monster tiles'), ((286, 292), 'identified: MAZE.INFO'),
             ((293, 412), 'decoded: text + tree'), ((413, 414), 'identified: SCENARIO.DATA header block'),
             ((415, 9999), 'identified: SCENARIO.DATA')]
    for s in range(1, 6):
        used = set()
        for v, ph, n in mp[s]:
            for k in range(n):
                used.add(ph + k)
                if v + k >= 2:
                    cls[(s, ph + k)] = next(c for (a, z), c in bands if a <= v + k <= z)
        for b in range(280):
            if b not in used:
                cls[(s, b)] = 'decoded: all-zero'
    for (a, z), c in {(2, 5): 'decoded: directory', (6, 209): 'identified: ANIM.DATA',
                      (210, 213): 'decoded: TESTANIM codefile', (214, 239): 'identified: interpreter 6502 code',
                      (240, 243): 'decoded: TESTANIM codefile', (244, 269): 'identified: interpreter 6502 code',
                      (270, 279): 'decoded: all-zero'}.items():
        for b in range(a, z + 1):
            cls[(6, b)] = c
    blk = {s: A.blocks(im) for s, (_, im) in imgs.items()}
    zero_bad = [k for k, c in cls.items() if c == 'decoded: all-zero' and blk[k[0]][k[1] * 512:k[1] * 512 + 512] != bytes(512)]
    cnt = collections.Counter(cls.values())
    for c, n in sorted(cnt.items()):
        print('%-45s %5d blocks %8d bytes %7.2f %%' % (c, n, n * 512, 100.0 * n / 1680))
    d = sum(n for c, n in cnt.items() if c.startswith('decoded'))
    i = sum(n for c, n in cnt.items() if c.startswith('identified'))
    print('decoded    %d blocks %d bytes %.2f %%' % (d, d * 512, 100.0 * d / 1680))
    print('identified %d blocks %d bytes %.2f %%' % (i, i * 512, 100.0 * i / 1680))
    print('total      %d blocks, residue %d;  "all-zero" blocks that are not zero: %d' % (len(cls), 1680 - d - i, len(zero_bad)))


def census(objdir):
    imgs = sides(objdir)
    mp = the_map(imgs)
    car = {}
    for s in range(1, 6):
        for v, ph, n in mp[s]:
            for k in range(n):
                car.setdefault(v + k, []).append(s)
    x = [v for v in car if v >= 2]
    print('distinct virtual blocks >= 2: %d   carriers histogram %s' % (len(x), dict(sorted(collections.Counter(len(car[v]) for v in x).items()))))
    print('side  boot+id  mapped(excl.0-1)  free')
    for s in range(1, 6):
        used = sum(n for _, _, n in mp[s])
        print('  %s      2        %3d             %3d' % ('ABCDE'[s - 1], used - 2, 280 - used))


def krn(work):
    t, ib, idx, out, audit, w1 = K.parse(open(os.path.join(work, 'virt/ASCII.HUFF'), 'rb').read(),
                                         open(os.path.join(work, 'virt/ASCII.KRN'), 'rb').read())
    print('# message number, block, lines, characters  (text not reproduced)')
    for n, b, ls in out:
        print('%05d  %3d  %3d  %5d' % (n, b, len(ls), sum(map(len, ls))))
    c = collections.Counter(ch for _, _, ls in out for s in ls for ch in s)
    tot = sum(c.values())
    print('# characters %d  NUL %d (%.2f %%)  space %d  code lengths NUL %d space %d' % (
        tot, c[0], 100.0 * c[0] / tot, c[32], len(t.codes[0]), len(t.codes[32])))
    rng = lambda a, z: sum(len(ls) for n, _, ls in out if a <= n <= z)  # noqa: E731
    print('# monster-name lines (12983..13479) %d, item lines (14002..14214) %d, spell lines (5000, 5048) %d' % (
        rng(12983, 13479), rng(14002, 14214), rng(5000, 5048)))
    print('# lines containing "Be Seeing You" %d; binary 10-byte-line messages %d' % (
        sum(b'Be Seeing You' in s for _, _, ls in out for s in ls),
        sum(1 for _, _, ls in out if ls and all(len(x) == 10 for x in ls) and any(c < 32 for x in ls for c in x))))
    lead = collections.Counter(s[:1] for _, _, ls in out for s in ls if s)
    print('# leading markers', {k.decode(): v for k, v in lead.items() if k in (b'@', b'^', b'#', b'$', b'*')})


def interp(work):
    blah = open(os.path.join(work, 'vol6/BLAH'), 'rb').read()
    for n, d in (('side A SYSTEM.INTERP (87-11-12, shipped)', open(os.path.join(work, 'vol1/SYSTEM.INTERP'), 'rb').read()),
                 ('side F SYSTEM.INTERP (87-11-04)', open(os.path.join(work, 'vol6/SYSTEM.INTERP'), 'rb').read()),
                 ('side F BLAH bytes 2048..15359', blah[2048:15360])):
        print('==', n)
        for m in re.finditer(rb'[\x20-\x7e]{10,}', d):
            s = m.group().decode()
            if len(set(s)) > 3:
                print('  0x%04x  %s' % (m.start(), s[:80]))


def data(work):
    v = lambda f: open(os.path.join(work, 'virt', f), 'rb').read()  # noqa: E731
    s = v('SCENARIO.DATA')
    print('== SCENARIO.DATA header: title len %d %r, stale %s' % (s[0], s[1:1 + s[0]], s[1 + s[0]:41].hex()))
    o = 0x6a
    for i in range(26):
        f = s[o:o + 10]
        print('  +%d  len %d  %-9s tail %s' % (o, f[0], f[1:1 + f[0]].decode('latin-1'), f[1 + f[0]:].hex()))
        o += 10
    w = v('WERDNA.DATA')
    print('== WERDNA.DATA')
    for i in range(8):
        r = w[i * 512:(i + 1) * 512]
        print('  slot %d name %s fields %s' % (i, r[1:1 + r[0]].decode(), [(r[o], r[o + 1:o + 15].decode('latin-1')) for o in (0xdc, 0xec, 0xfc)]))
    m = v('MAZE.INFO')
    print('== MAZE.INFO 62 records', [struct.unpack_from('<BBH', m, i) for i in range(0, 248, 4)])
    for mm in re.finditer(rb'[\x20-\x7e\r]{10,}', m):
        print('  text 0x%x %r' % (mm.start(), mm.group()[:70]))
    c = v('200.CHARSET')
    e = [g for g in range(512) if c[g * 8:g * 8 + 8] == bytes(8)]
    print('== 200.CHARSET blank glyphs %d: 0..127 %d, 128..255 %d, 256..511 %d' % (
        len(e), sum(g < 128 for g in e), sum(128 <= g < 256 for g in e), sum(g >= 256 for g in e)))
    mo = v('200.MONSTERS')
    t = [mo[i:i + 8] for i in range(0, len(mo), 8)]
    print('== 200.MONSTERS tiles %d, blank %d, all-printable %d' % (
        len(t), sum(x == bytes(8) for x in t), sum(all(32 <= b < 127 or b == 13 for b in x) for x in t)))
    an = open(os.path.join(work, 'vol6/ANIM.DATA'), 'rb').read()
    pr = []
    for i in range(0, 512, 4):
        p = struct.unpack_from('<HH', an, i)
        pr.append(p)
        if p[1] == 65535:
            break
    print('== ANIM.DATA index entries %d %s' % (len(pr), pr))


def slack(work):
    vol = open(os.path.join(work, 'virtual.vol'), 'rb').read()
    for b in range(226, 286):
        x = vol[b * 512:(b + 1) * 512]
        for m in re.finditer(rb'(?:[\x20-\x7e]|\r){8,}', x):
            t = m.group().replace(b'\r', b' / ')
            if re.search(rb'[;|]|ROUTINE|Sector|Read|Write|sta|lda|Op1|\.equ', t):
                print('virtual %3d +%3d  %s' % (b, m.start(), t[:100].decode('latin-1')))
    k = open(os.path.join(work, 'virt/KANA.KEYMAP'), 'rb').read()
    i, out = 0x1a8, []
    while i < 0x260:
        c = k[i]
        if c == 0x10:
            out.append(' ' * max(0, k[i + 1] - 32))
            i += 2
            continue
        out.append('\n' if c == 13 else chr(c) if 32 <= c < 127 else '.')
        i += 1
    print('KANA.KEYMAP 0x1A8..0x25F (DLE indents expanded):')
    print(''.join(out))


if __name__ == '__main__':
    cmd, arg = sys.argv[1], sys.argv[2]
    {'identity': identity, 'stale': stale, 'coverage': coverage, 'census': census,
     'krn': krn, 'interp': interp, 'data': data, 'slack': slack}[cmd](arg)
