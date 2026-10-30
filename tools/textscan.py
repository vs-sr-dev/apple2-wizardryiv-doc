#!/usr/bin/env python3
"""Find and dump Universe's string tables, and measure how much of the game
is text.

Every block of prose on this disc uses the same shape and nothing announces
it: a run of 32-bit big-endian offsets at the head of a blob, each pointing at
a four-byte record header followed by NUL-terminated 8-bit text.

Three details have to be right or the scan misses most of the tables:

  * the table's length is not stored anywhere.  It ends at the first entry
    that does not point at a plausible record.
  * entries may repeat, and may point *backwards*.  The writers reuse a line
    rather than storing it twice, so a record's extent comes from its NUL
    terminator and never from the next offset.
  * an entry of 0 is an empty slot, not a parse failure.  Empty slots are the
    interesting part -- see tools/slots.py.

Text is 7-bit ASCII plus CP437 for the accented range (see docs/06).

Usage:
    python3 tools/textscan.py <dir> [--dump FILE] [--csv FILE]
"""
import sys, os, argparse

HDR = 4          # bytes of record header before the text
PRINT = set(range(0x20, 0x7f)) | {0x0a}

CP437 = {0x80: 'C,', 0x81: 'ue', 0x82: 'e/', 0x83: 'a^',
         0x84: 'ae', 0x85: 'a\\', 0x86: 'ao', 0x87: 'c,',
         0x88: 'e^', 0x89: 'ee', 0x8a: 'e\\', 0x8b: 'ie',
         0x8c: 'i^', 0x8d: 'i\\', 0x8e: 'Ae', 0x8f: 'Ao',
         0x90: 'E/', 0x91: 'ae', 0x92: 'AE', 0x93: 'o^',
         0x94: 'oe', 0x95: 'o\\', 0x96: 'u^', 0x97: 'u\\',
         0x98: 'ye', 0x99: 'Oe', 0x9a: 'Ue', 0xa0: 'a/',
         0xa1: 'i/', 0xa2: 'o/', 0xa3: 'u/', 0xa4: 'n~',
         0xa5: 'N~', 0xe1: 'ss'}

NUL = b'\x00'


def hdrlen(b, o):
    """Records come in two shapes and nothing distinguishes them but the
    first byte.  A speech record carries a four-byte header (0xffff or a
    small pair, then two layout bytes); a plain name or description has no
    header at all and the text starts at the offset.  The first byte of a
    header is never printable, and the first byte of text always is."""
    if o >= len(b):
        return 0
    c = b[o]
    return HDR if (c < 0x20 or c >= 0x7f) else 0


def _text_at(b, o):
    t = b[o + hdrlen(b, o):]
    z = t.find(NUL)
    return t[:z] if z >= 0 else t


def parse_table(b):
    n = len(b)
    if n < 32:
        return None
    offs = []
    i = 0
    while i + 4 <= n:
        v = int.from_bytes(b[i:i + 4], 'big')
        if v == 0:
            offs.append(0)
            i += 4
            continue
        if not (HDR < v < n) or v <= i + 3:
            break
        if b[v:].find(NUL) < 0:
            break
        offs.append(v)
        i += 4
    while offs and offs[-1] == 0:
        offs.pop()
    if len(offs) < 4:
        return None
    first = min(o for o in offs if o)
    if 4 * len(offs) > first:
        offs = offs[:first // 4]
    if len(offs) < 4:
        return None
    recs = []
    for o in offs:
        if o == 0:
            recs.append((0, b'', b''))
        else:
            h = hdrlen(b, o)
            recs.append((o, b[o:o + h], _text_at(b, o)))
    filled = [t for _o, _h, t in recs if t]
    if len(filled) < 3:
        return None
    good = sum(1 for t in filled
               if sum(c in PRINT for c in t) >= 0.85 * len(t))
    if good < 0.9 * len(filled):
        return None
    return recs


def decode(t):
    """Printable ASCII verbatim; CP437 accents transliterated so the dump is
    plain ASCII; anything else as <NN> so control codes stay visible."""
    out = []
    for c in t:
        if 0x20 <= c < 0x7f:
            out.append(chr(c))
        elif c in CP437:
            out.append(CP437[c])
        else:
            out.append('<%02x>' % c)
    return ''.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root')
    ap.add_argument('--dump')
    ap.add_argument('--csv')
    ap.add_argument('--max', type=int, default=0,
                    help='truncate each dumped string to N characters '
                         '(0 = no truncation). The committed note uses 64: '
                         'this repository documents the structure of the '
                         "game's script, it does not redistribute it.")
    args = ap.parse_args()

    files = []
    for r, _d, fs in os.walk(args.root):
        for f in fs:
            files.append(os.path.join(r, f))
    files.sort()

    tables, dump, rows = [], [], []
    total_blob = 0
    for p in files:
        b = open(p, 'rb').read()
        total_blob += len(b)
        recs = parse_table(b)
        if not recs:
            continue
        uniq = set(t for _o, _h, t in recs if t)
        tb = sum(len(t) for t in uniq)
        empty = sum(1 for _o, _h, t in recs if not t)
        rel = os.path.relpath(p, args.root).replace('\\', '/')
        tables.append((rel, len(b), len(recs), empty, len(uniq), tb))
        rows.append('%s,%d,%d,%d,%d,%d' %
                    (rel, len(b), len(recs), empty, len(uniq), tb))
        dump.append('=== %s  (%d bytes, %d slots, %d empty, %d unique, '
                    '%d text bytes)' %
                    (rel, len(b), len(recs), empty, len(uniq), tb))
        for i, (o, h, t) in enumerate(recs):
            if o == 0:
                dump.append('%4d --EMPTY SLOT--' % i)
            else:
                d = decode(t)
                if args.max and len(d) > args.max:
                    d = d[:args.max] + ' [...%d more]' % (len(d) - args.max)
                dump.append('%4d @%-7d %s  %s' % (i, o, h.hex(), d))
        dump.append('')

    tables.sort(key=lambda r: -r[5])
    print('%-56s %8s %6s %6s %6s %8s' %
          ('blob', 'bytes', 'slots', 'empty', 'uniq', 'text'))
    for rel, nb, nr, ne, nu, tb in tables:
        print('%-56s %8d %6d %6d %6d %8d' % (rel[-56:], nb, nr, ne, nu, tb))
    print()
    print('string tables      %d' % len(tables))
    print('slots              %d' % sum(r[2] for r in tables))
    print('empty slots        %d' % sum(r[3] for r in tables))
    print('unique strings     %d' % sum(r[4] for r in tables))
    print('text bytes         %d' % sum(r[5] for r in tables))
    print('bytes scanned      %d' % total_blob)

    if args.dump:
        head = []
        if args.max:
            head = [
                'Strings truncated to %d characters.' % args.max,
                '',
                "This note records the shape of Universe's string tables --"
                ' slot index, byte',
                'offset, record header, and enough text to identify the'
                ' record. Run the tool',
                'without --max against your own disc image for the full'
                ' text: this repository',
                'documents the structure of the script, it does not'
                ' redistribute it.',
                '', '']
        open(args.dump, 'w', encoding='utf-8').write(
            '\n'.join(head + dump))
    if args.csv:
        open(args.csv, 'w').write(
            'blob,bytes,slots,empty,unique,textbytes\n' +
            '\n'.join(rows) + '\n')


if __name__ == '__main__':
    main()
