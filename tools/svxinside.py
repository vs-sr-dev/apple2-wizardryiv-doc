#!/usr/bin/env python3
"""svxinside.py -- census of the IFF 8SVX samples embedded in a file that is
not itself an IFF file (Power Drive's two music players, music.rnc and
gmusic.rnc unpacked: one CODE hunk each with the samples linked in).

IFF 8SVX is Electronic Arts' published IFF-85 with Commodore's 8SVX form
(VHDR: oneShotHiSamples, repeatHiSamples, samplesPerHiCycle, samplesPerSec,
ctOctave, sCompression, volume).  A sample is found by its magic only:
`FORM`, a length that fits in the file, `8SVX` at +8.  The seconds are
BODY bytes / samplesPerSec, for compression 0 (every sample here).

    python tools/svxinside.py FILE [FILE ...]
    python tools/svxinside.py --selftest
"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dirguard, nameguard


def forms(d):
    o = 0
    while True:
        o = d.find(b'FORM', o)
        if o < 0:
            return
        if o + 12 <= len(d):
            n = struct.unpack_from('>I', d, o + 4)[0]
            if d[o + 8:o + 12] == b'8SVX' and 12 <= n <= len(d) - o - 8:
                yield o, n + 8
                o += n + 8
                continue
        o += 4


def chunks(f):
    o, out = 12, {}
    while o + 8 <= len(f):
        tag = f[o:o + 4]
        n = struct.unpack_from('>I', f, o + 4)[0]
        out.setdefault(tag, f[o + 8:o + 8 + n])
        o += 8 + n + (n & 1)
    return out


def census(d):
    rows = []
    for o, n in forms(d):
        c = chunks(d[o:o + n])
        vh = c.get(b'VHDR', b'')
        if len(vh) < 20:
            rows.append((o, n, None))
            continue
        one, rep, cyc, rate, octs, comp, vol = struct.unpack('>IIIHBBI', vh[:20])
        body = c.get(b'BODY', b'')
        name = c.get(b'NAME', b'').split(b'\0')[0].decode('latin-1')
        anno = c.get(b'ANNO', b'').split(b'\0')[0].decode('latin-1')
        rows.append((o, n, dict(one=one, rep=rep, rate=rate, octaves=octs, comp=comp,
                                vol=vol, body=len(body), name=name, anno=anno,
                                seconds=(len(body) / rate) if rate else None)))
    return rows


def report(path):
    d = open(path, 'rb').read()
    rows = census(d)
    print('%s: %d bytes, %d FORM 8SVX by magic' % (os.path.basename(path), len(d), len(rows)))
    total = 0.0
    tb = 0
    for o, n, r in rows:
        if r is None:
            print('  at %7d  %7d B  (no VHDR)' % (o, n))
            continue
        print('  at %7d  %7d B  rate %5d Hz  body %6d B  %6.2f s  oneshot %6d rep %6d oct %d comp %d vol %d  name %r anno %r'
              % (o, n, r['rate'], r['body'], r['seconds'] or 0, r['one'], r['rep'], r['octaves'], r['comp'], r['vol'], r['name'], r['anno']))
        total += r['seconds'] or 0
        tb += r['body']
    print('  total: %d samples, %d body bytes, %.2f s' % (len(rows), tb, total))
    return rows


def _svx(rate, body, name=b''):
    vhdr = struct.pack('>IIIHBBI', len(body), 0, 32, rate, 1, 0, 0x10000)
    inner = b'8SVX' + b'VHDR' + struct.pack('>I', 20) + vhdr
    if name:
        inner += b'NAME' + struct.pack('>I', len(name)) + name + (b'\0' if len(name) & 1 else b'')
    inner += b'BODY' + struct.pack('>I', len(body)) + body + (b'\0' if len(body) & 1 else b'')
    return b'FORM' + struct.pack('>I', len(inner)) + inner


def selftest():
    fails = 0

    def check(n, ok):
        nonlocal fails
        print('  %-64s %s' % (n, 'ok' if ok else 'FAIL'))
        if not ok:
            fails += 1

    a = _svx(8000, b'\x01' * 16000, b'kick')
    b = _svx(11025, b'\x02' * 11025)
    blob = b'\x4e\x71' * 50 + a + b'\x00' * 7 + b + b'FORMxxxx'
    rows = census(blob)
    check('two samples found by magic inside code and padding', len(rows) == 2)
    check('first: 8000 Hz, 2.00 s, name kick', rows[0][2]['rate'] == 8000 and abs(rows[0][2]['seconds'] - 2.0) < 1e-9 and rows[0][2]['name'] == 'kick')
    check('second: 11025 Hz, 1.00 s, no name', rows[1][2]['rate'] == 11025 and abs(rows[1][2]['seconds'] - 1.0) < 1e-9 and rows[1][2]['name'] == '')
    check('offsets are where the samples were placed', rows[0][0] == 100 and rows[1][0] == 100 + len(a) + 7)
    check('a FORM whose length overruns the file is skipped', census(b'FORM\x00\x00\x10\x008SVX') == [])
    check('a FORM that is not 8SVX is skipped', census(b'FORM\x00\x00\x00\x04ILBM') == [])
    check('empty input: nothing', census(b'') == [])
    print('7 checks, %d failures' % fails)
    return fails


def main():
    nameguard.guard()
    if len(sys.argv) > 1 and sys.argv[1] == '--selftest':
        sys.exit(1 if selftest() else 0)
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        report(dirguard.want_file(p, 'svxinside'))


if __name__ == '__main__':
    main()
