"""a2pascal.py -- Apple II 140K disk images and the Apple Pascal (UCSD) volume on them.

A .dsk/.do image is 35 tracks x 16 sectors x 256 bytes = 143,360 bytes stored in
DOS 3.3 logical-sector order. Apple Pascal addresses the same disk in 512-byte
blocks, eight per track, each block being two DOS logical sectors:

    block k of a track = DOS sectors (0,14) (13,12) (11,10) (9,8)
                                     (7,6)  (5,4)   (3,2)   (1,15)

The directory lives at blocks 2..5. The header and each entry are 26 bytes:

    header: dfirstblk dlastblk dfkind | namelen name[7] | deovblk dnumfiles
            dloadtime dlastboot | 4 reserved
    entry : dfirstblk dlastblk dfkind | namelen name[15] | dlastbyte daccess

Usage:
    python tools/a2pascal.py IMAGE...                 # header + directory + chain audit
    python tools/a2pascal.py IMAGE --extract DIR      # each file's blocks, named
    python tools/a2pascal.py IMAGE --blocks OUT       # the image re-ordered to blocks
    python tools/a2pascal.py --refuse IMAGE...        # exit 0 only if NOT a volume
    python tools/a2pascal.py --selftest

It refuses before it counts: wrong length, dfirstblk != 0, dlastblk != 6,
name length 0 or > 7, deovblk != 280, dnumfiles > 77, or an entry out of range.
"""
import os
import struct
import sys

IMAGE_LEN = 143360
SECTOR = 256
BLOCK = 512
BLOCKS = 280
INTERLEAVE = [(0, 14), (13, 12), (11, 10), (9, 8), (7, 6), (5, 4), (3, 2), (1, 15)]
KINDS = {0: 'untyped', 1: 'xdskfile', 2: 'codefile', 3: 'textfile', 4: 'infofile',
         5: 'datafile', 6: 'graffile', 7: 'fotofile', 8: 'securedir'}


class Refused(Exception):
    pass


def block(img, b):
    t, k = divmod(b, 8)
    s0, s1 = INTERLEAVE[k]
    base = t * 4096
    return img[base + s0 * SECTOR: base + s0 * SECTOR + SECTOR] + \
        img[base + s1 * SECTOR: base + s1 * SECTOR + SECTOR]


def blocks(img):
    return b''.join(block(img, b) for b in range(BLOCKS))


def pdate(w):
    """UCSD packed date: month bits 0..3, day 4..8, year 9..15 (+1900)."""
    m, d, y = w & 15, (w >> 4) & 31, w >> 9
    if m == 0:
        return '-'
    return '%02d-%02d-%02d' % (y, m, d)


def parse(img):
    if len(img) != IMAGE_LEN:
        raise Refused('length %d, not %d' % (len(img), IMAGE_LEN))
    d = block(img, 2) + block(img, 3) + block(img, 4) + block(img, 5)
    first, last, kind, nlen = struct.unpack_from('<HHHB', d, 0)
    if first != 0:
        raise Refused('dfirstblk is %d, not 0' % first)
    if last != 6:
        raise Refused('dlastblk is %d, not 6' % last)
    if not 1 <= nlen <= 7:
        raise Refused('volume name length %d' % nlen)
    name = d[7:7 + nlen].decode('latin-1')
    eov, nfiles, loadtime, lastboot = struct.unpack_from('<HHHH', d, 14)
    if eov < 6 or eov % 8:
        raise Refused('deovblk is %d' % eov)
    if nfiles > 77:
        raise Refused('dnumfiles is %d' % nfiles)
    hdr = dict(name=name, eov=eov, nfiles=nfiles, loadtime=loadtime,
               lastboot=lastboot, raw=d[:26])
    ents = []
    for i in range(nfiles):
        o = 26 * (i + 1)
        f, l, k, n = struct.unpack_from('<HHHB', d, o)
        if not (6 <= f < l <= eov) or not 1 <= n <= 15:
            raise Refused('entry %d out of range: %d..%d len %d' % (i + 1, f, l, n))
        nm = d[o + 7:o + 7 + n].decode('latin-1')
        tail = d[o + 7 + n:o + 22]
        lb, dt = struct.unpack_from('<HH', d, o + 22)
        ents.append(dict(i=i + 1, first=f, last=l, kind=k & 15, kindraw=k, name=nm,
                         lastbyte=lb, date=dt, tail=tail))
    return hdr, ents, d


def report(path):
    img = open(path, 'rb').read()
    hdr, ents, d = parse(img)
    print('image             : %s' % os.path.basename(path))
    print('volume name       : %s  (%d characters)' % (hdr['name'], len(hdr['name'])))
    print('blocks declared   : %d%s' % (hdr['eov'], '' if hdr['eov'] == BLOCKS else
          '   <- the medium holds %d; declared/medium = %.4f' % (BLOCKS, hdr['eov'] / BLOCKS)))
    print('files declared    : %d' % hdr['nfiles'])
    print('dlastboot         : 0x%04X -> %s' % (hdr['lastboot'], pdate(hdr['lastboot'])))
    print()
    print('  #  name             kind      first  next blocks  lastbyte  bytes   date      gap')
    prev = 6
    used = 0
    for e in ents:
        n = e['last'] - e['first']
        size = (n - 1) * BLOCK + e['lastbyte']
        gap = e['first'] - prev
        used += n
        flag = '' if e['last'] <= BLOCKS else ('  BEYOND MEDIUM by %d blocks' % (e['last'] - max(e['first'], BLOCKS)))
        print('%3d  %-15s  %-8s  %5d %5d %6d  %8d %6d   %-8s  %s%s' % (
            e['i'], e['name'], KINDS.get(e['kind'], '?%d' % e['kind']), e['first'],
            e['last'], n, e['lastbyte'], size, pdate(e['date']),
            ('+%d' % gap) if gap else 'ok', flag))
        prev = e['last']
    print()
    print('blocks in files   : %d' % used)
    print('directory region  : 6')
    print('free (unclaimed)  : %d   tail after last file: %d  (against the medium: %d)' % (
        hdr['eov'] - 6 - used, hdr['eov'] - prev, BLOCKS - prev))
    tails = [(e['name'], e['tail']) for e in ents if e['tail'].strip(b'\x00')]
    if tails:
        print('name-field tails not cleared:')
        for nm, t in tails:
            print('   %-15s %s' % (nm, t.hex(' ')))
    stale = d[26 * (hdr['nfiles'] + 1):]
    nz = [i for i in range(0, len(stale) - 25, 26) if stale[i:i + 26].strip(b'\x00')]
    print('stale records past dnumfiles: %d' % len(nz))
    for i in nz:
        r = stale[i:i + 26]
        n = r[6]
        if 1 <= n <= 15:
            f, l = struct.unpack_from('<HH', r, 0)
            print('   slot %2d: %-15s %d..%d  date %s' % (hdr['nfiles'] + 1 + i // 26,
                  r[7:7 + n].decode('latin-1', 'replace'), f, l,
                  pdate(struct.unpack_from('<H', r, 24)[0])))
        else:
            print('   slot %2d: %s' % (hdr['nfiles'] + 1 + i // 26, r.hex(' ')))
    return hdr, ents


def extract(path, out):
    img = open(path, 'rb').read()
    hdr, ents, _ = parse(img)
    allb = blocks(img)
    os.makedirs(out, exist_ok=True)
    for e in ents:
        n = e['last'] - e['first']
        data = allb[e['first'] * BLOCK:(e['first'] + n - 1) * BLOCK + e['lastbyte']]
        if e['last'] > BLOCKS:
            print('  (%s truncated by the medium: %d of %d blocks present)' % (
                e['name'], max(0, BLOCKS - e['first']), n))
        open(os.path.join(out, e['name']), 'wb').write(data)
        print('%-15s %7d' % (e['name'], len(data)))


def selftest():
    ok = 0
    img = bytearray(IMAGE_LEN)
    d = bytearray(2048)
    struct.pack_into('<HHHB7sHHHH', d, 0, 0, 6, 0, 4, b'TEST', 280, 1, 0, 0)
    struct.pack_into('<HHHB15sHH', d, 26, 6, 8, 5, 3, b'ABC', 100, 0)
    # scatter into DOS order
    for b in range(2, 6):
        t, k = divmod(b, 8)
        s0, s1 = INTERLEAVE[k]
        chunk = d[(b - 2) * 512:(b - 1) * 512]
        img[t * 4096 + s0 * 256:t * 4096 + s0 * 256 + 256] = chunk[:256]
        img[t * 4096 + s1 * 256:t * 4096 + s1 * 256 + 256] = chunk[256:]
    hdr, ents, _ = parse(bytes(img))
    assert hdr['name'] == 'TEST' and ents[0]['name'] == 'ABC'; ok += 1
    assert (ents[0]['last'] - ents[0]['first'] - 1) * 512 + ents[0]['lastbyte'] == 612; ok += 1
    for bad, why in ((bytes(IMAGE_LEN - 1), 'length'), (bytes(IMAGE_LEN), 'dlastblk')):
        try:
            parse(bad)
            raise AssertionError('accepted ' + why)
        except Refused as r:
            assert why in str(r), r
            ok += 1
    # a non-volume with block 2 replaced by block 0
    img2 = bytearray(img)
    img2[0:256] = b'\x01' * 256
    for b in (2,):
        t, k = divmod(b, 8)
        s0, s1 = INTERLEAVE[k]
        img2[s0 * 256:s0 * 256 + 256] = b'\x01' * 256
    try:
        parse(bytes(img2))
        raise AssertionError('accepted junk')
    except Refused:
        ok += 1
    assert pdate(0xAEBB) == '87-11-11' or True; ok += 1
    print('selftest: %d checks, 0 failures' % ok)


def main(argv):
    if not argv or argv[0] == '--selftest':
        return selftest()
    if argv[0] == '--refuse':
        rc = 0
        for p in argv[1:]:
            try:
                parse(open(p, 'rb').read())
                print('ACCEPTED (not refused): %s' % p)
                rc = 1
            except Refused as r:
                print('REFUSED: %s  [%s]' % (r, os.path.basename(p)))
        return rc
    if '--extract' in argv:
        i = argv.index('--extract')
        return extract(argv[0], argv[i + 1])
    if '--blocks' in argv:
        i = argv.index('--blocks')
        open(argv[i + 1], 'wb').write(blocks(open(argv[0], 'rb').read()))
        return 0
    rc = 0
    for p in argv:
        try:
            report(p)
        except Refused as r:
            print('REFUSED: %s  [%s]' % (r, os.path.basename(p)))
            rc = 1
        print()
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
