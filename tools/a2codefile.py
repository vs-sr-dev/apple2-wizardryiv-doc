"""a2codefile.py -- an Apple Pascal codefile: segment dictionary, procedure
dictionaries, and the string constants the p-code carries.

Block 0 of a codefile is the segment dictionary: 16 (codeaddr block, codeleng)
word pairs, 16 eight-character names at 64, 16 segkind words at 192, 16
textaddr words at 224, 16 seginfo words at 256 (segnum = low byte, mtype bits
8..11, version bits 13..15). Each segment ends with a byte pair -- segment
number, procedure count -- preceded, growing downwards, by one 16-bit
self-relative pointer per procedure. The check that makes a parse a reading:
every pointer, subtracted from its own slot, must land inside its own segment.

String constants: the Apple Pascal LSA opcode is 0xA6 followed by a length
byte and the characters. --strings lists every A6-prefixed run of printable
characters whose length byte matches; it is a census of candidates, not a
disassembly.

Usage:
    python tools/a2codefile.py FILE                # dictionary + procedure audit
    python tools/a2codefile.py FILE --strings      # + LSA string constants per segment
    python tools/a2codefile.py --selftest
"""
import struct
import sys


class Refused(Exception):
    pass


def segments(d):
    if len(d) < 512 or len(d) % 512:
        raise Refused('length %d is not a whole number of blocks' % len(d))
    out = []
    for i in range(16):
        a, l = struct.unpack_from('<HH', d, i * 4)
        if not l:
            continue
        name = d[64 + i * 8:72 + i * 8].decode('latin-1')
        kind = struct.unpack_from('<H', d, 192 + i * 2)[0]
        info = struct.unpack_from('<H', d, 256 + i * 2)[0]
        if a * 512 + l > len(d):
            raise Refused('segment %s runs past the file' % name)
        out.append(dict(slot=i, name=name, addr=a, leng=l, kind=kind, segnum=info & 255,
                        mtype=(info >> 8) & 15, version=(info >> 13) & 7))
    if not out:
        raise Refused('no segment')
    return out


def procs(d, s):
    base = s['addr'] * 512
    end = base + s['leng']
    segnum, n = d[end - 2], d[end - 1]
    inside = 0
    entries = []
    for p in range(n):
        slot = end - 4 - 2 * p
        rel = struct.unpack_from('<H', d, slot)[0]
        tgt = slot - rel
        if base <= tgt < slot:
            inside += 1
        entries.append(tgt - base)
    return segnum, n, inside, entries


def lsa_strings(seg):
    out = []
    i = 0
    while i < len(seg) - 2:
        if seg[i] == 0xA6:
            n = seg[i + 1]
            s = seg[i + 2:i + 2 + n]
            if n >= 3 and len(s) == n and all(32 <= c < 127 for c in s):
                out.append((i, s.decode('ascii')))
                i += 2 + n
                continue
        i += 1
    return out


def report(path, strings=False):
    d = open(path, 'rb').read()
    segs = segments(d)
    tot_p = tot_in = tot_c = 0
    print('slot  name      block   bytes  seg#  mtype ver  procs  inside  tail-ok')
    for s in segs:
        segnum, n, inside, _ = procs(d, s)
        ok = segnum == s['segnum']
        tot_p += n
        tot_in += inside
        tot_c += s['leng']
        print('%3d   %-8s  %4d  %6d  %4d  %4d  %3d  %5d  %6d   %s' % (
            s['slot'], s['name'], s['addr'], s['leng'], s['segnum'], s['mtype'], s['version'],
            n, inside, 'yes' if ok else 'NO (%d)' % segnum))
    print('segments %d   code bytes %d   procedures %d   pointers inside their segment %d of %d' % (
        len(segs), tot_c, tot_p, tot_in, tot_p))
    if strings:
        for s in segs:
            seg = d[s['addr'] * 512:s['addr'] * 512 + s['leng']]
            st = lsa_strings(seg)
            print()
            print('== %s: %d LSA string constants' % (s['name'].strip(), len(st)))
            for o, t in st:
                print('  +%05d  %s' % (o, t))


def selftest():
    ok = 0
    d = bytearray(1024)
    struct.pack_into('<HH', d, 0, 1, 20)
    d[64:72] = b'TESTSEG '
    struct.pack_into('<H', d, 256, 7 | (2 << 8) | (2 << 13))
    seg = bytearray(20)
    seg[0:6] = b'\xa6\x04ABCD'
    # one procedure whose entry is at offset 8; slot at 16, rel = 16 - 8
    struct.pack_into('<H', seg, 16, 8)
    seg[18], seg[19] = 7, 1
    d[512:532] = seg
    s = segments(bytes(d))
    assert s[0]['segnum'] == 7 and s[0]['version'] == 2; ok += 1
    segnum, n, inside, ent = procs(bytes(d), s[0])
    assert (segnum, n, inside, ent) == (7, 1, 1, [8]); ok += 1
    assert lsa_strings(bytes(seg)) == [(0, 'ABCD')]; ok += 1
    for bad in (bytes(100), bytes(1024)):
        try:
            segments(bad)
            raise AssertionError('accepted')
        except Refused:
            ok += 1
    print('selftest: %d checks, 0 failures' % ok)


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] == '--selftest':
        selftest()
    else:
        try:
            report(a[0], '--strings' in a)
        except Refused as r:
            print('REFUSED: %s' % r)
            sys.exit(1)
