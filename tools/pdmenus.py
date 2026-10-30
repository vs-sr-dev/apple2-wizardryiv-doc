#!/usr/bin/env python3
"""pdmenus.py -- the five-language menu table inside Power Drive's
`rmenus.rnc` (unpacked, 103,232 bytes, loaded at $155000 by rboot.bin).

THE MODEL, READ FROM A HEX DUMP (docs/06)
-----------------------------------------
There is no table of fixed 8-byte slots.  Each menu item is a record whose
tail is FIVE big-endian longwords: absolute addresses, in the image loaded at
$155000, of the item's label in English, French, German, Spanish and Italian
(the order of the five language labels at 0x17F94: ENGLISH, FRANCAISES,
DEUTSCHE, ESPANOL, ITALIANO).  Each label is a run of printable bytes
terminated by 0xFF, usually padded with a leading and a trailing space.
When two languages use the same word the record carries the SAME pointer
twice (` REPAIR` for English and French, $16D16E both), so "identical across
languages" is a fact of the pointers, not a string comparison.

The reader finds every group of five consecutive longwords that all point
inside the image (base .. base+len) at strings that end in 0xFF within 40
bytes, on an even offset, and reports: the records, the labels per language,
how many pointers each language shares with English, how many labels are
distinct, and the whole table (it is the UI of a 1994 rally game, and it is
published whole).

    python tools/pdmenus.py _work/unpacked/rmenus.rnc.unp [--base 0x155000] [--table]
    python tools/pdmenus.py --selftest
"""
import argparse, os, sys, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dirguard, nameguard

LANGS = ('EN', 'FR', 'DE', 'ES', 'IT')
BASE = 0x155000


def label_at(d, off, maxlen=40):
    """The 0xFF-terminated printable run at off, or None."""
    if off < 0 or off >= len(d):
        return None
    end = d.find(b'\xff', off, off + maxlen)
    if end < 0:
        return None
    s = d[off:end]
    if not s or any(c < 0x20 or c > 0x7e for c in s):
        return None
    return s.decode('ascii')


def pointer_runs(d, base=BASE):
    """Maximal runs of consecutive longwords that each point at a 0xFF-terminated
    label inside the image: [(offset, [offs...], [labels...])]."""
    runs = []
    o = 0
    while o + 4 <= len(d):
        p = struct.unpack_from('>I', d, o)[0] - base
        lab = label_at(d, p) if 0 <= p < len(d) else None
        if lab is None:
            o += 2
            continue
        start, offs, labels = o, [], []
        while o + 4 <= len(d):
            p = struct.unpack_from('>I', d, o)[0] - base
            lab = label_at(d, p) if 0 <= p < len(d) else None
            if lab is None:
                break
            offs.append(p)
            labels.append(lab)
            o += 4
        runs.append((start, offs, labels))
    return runs


def find_records(d, base=BASE):
    """A menu record is a run of EXACTLY five label pointers.  Longer runs are
    pointer tables (the high-score rows, the car list) and are not records."""
    return [r for r in pointer_runs(d, base) if len(r[1]) == 5]


def find_tables(d, base=BASE):
    """Runs of two or more pointers that are not five: tables.  Runs of one
    are the code's own references to strings and are only counted."""
    return [r for r in pointer_runs(d, base) if len(r[1]) >= 2 and len(r[1]) != 5]


def count_singles(d, base=BASE):
    return sum(1 for r in pointer_runs(d, base) if len(r[1]) == 1)


def report(d, base=BASE, table=False):
    recs = find_records(d, base)
    tabs = find_tables(d, base)
    print('rmenus image %d bytes, base $%X: %d records of exactly five label pointers; %d pointer tables (lengths %s); %d single pointers (code references)'
          % (len(d), base, len(recs), len(tabs), ','.join(str(len(t[1])) for t in tabs), count_singles(d, base)))
    if not recs:
        sys.exit('pdmenus: no five-pointer record found -- not rmenus, or the base is wrong')
    shared = collections.Counter()
    distinct = [set() for _ in LANGS]
    identical_all = 0
    empty = collections.Counter()
    for o, offs, labels in recs:
        for i in range(1, 5):
            if offs[i] == offs[0]:
                shared[LANGS[i]] += 1
        if len(set(offs)) == 1:
            identical_all += 1
        for i, x in enumerate(offs):
            distinct[i].add(x)
            if not labels[i].strip():
                empty[LANGS[i]] += 1
    print('records whose five pointers are one and the same: %d' % identical_all)
    for i, l in enumerate(LANGS):
        print('  %s: distinct labels %3d, blank labels %2d%s' % (
            l, len(distinct[i]), empty[l],
            '' if i == 0 else ', pointer shared with EN in %d of %d records' % (shared[l], len(recs))))
    lo = min(min(x) for _, x, _ in recs)
    hi = max(max(x) for _, x, _ in recs)
    print('label pool spans image offsets 0x%X .. 0x%X; records span 0x%X .. 0x%X'
          % (lo, hi, recs[0][0], recs[-1][0]))
    if table:
        print()
        for o, offs, labels in tabs:
            print('table at 0x%05X (%d pointers): %s' % (o, len(offs), ' '.join('|' + l.strip() + '|' for l in labels)))
        print()
        print('%-7s %-24s %-24s %-24s %-24s %-24s' % ('rec', *LANGS))
        for o, offs, labels in recs:
            print('0x%05X %s' % (o, ' '.join('%-24s' % ('|' + l.strip() + '|') for l in labels)))
    return recs


def selftest():
    fails = 0

    def check(name, ok):
        nonlocal fails
        print('  %-70s %s' % (name, 'ok' if ok else 'FAIL'))
        if not ok:
            fails += 1

    base = 0x1000
    pool = b' REPAIR\xff REPARA\xff RIPARA\xff EXIT\xff SORTIE\xff'
    img = bytearray(64)                       # records first, pool after
    p0 = base + 64                            # REPAIR
    p1 = p0 + 8                               # REPARA
    p2 = p1 + 8                               # RIPARA
    p3 = p2 + 8                               # EXIT
    p4 = p3 + 6                               # SORTIE
    struct.pack_into('>5I', img, 4, p0, p0, p0, p1, p2)      # EN=FR=DE REPAIR, ES, IT
    struct.pack_into('>5I', img, 30, p3, p4, p3, p3, p3)     # EXIT / SORTIE
    d = bytes(img) + pool
    recs = find_records(d, base)
    check('two records found at their offsets', [r[0] for r in recs] == [4, 30])
    # a run of six pointers is a table, not a record
    img6 = bytearray(64)
    struct.pack_into('>6I', img6, 4, p0, p0, p0, p1, p2, p3)
    d6 = bytes(img6) + pool
    check('a run of six pointers is not a record', find_records(d6, base) == [])
    check('... but is reported as a table of six', [len(t[1]) for t in find_tables(d6, base)] == [6])
    check('record 1: EN/FR/DE share one pointer, ES and IT differ',
          recs[0][1][0] == recs[0][1][1] == recs[0][1][2] and len(set(recs[0][1])) == 3)
    check('labels read to the 0xFF', recs[0][2] == [' REPAIR', ' REPAIR', ' REPAIR', ' REPARA', ' RIPARA'])
    check('record 2: French differs, the other four share', recs[1][2][1] == ' SORTIE' and recs[1][1][0] == recs[1][1][4])
    check('a wrong base finds nothing', find_records(d, 0x9000) == [])
    check('empty input finds nothing', find_records(b'', base) == [])
    check('a label with a control byte is rejected', label_at(b'AB\x01\xff', 0) is None)
    check('a label with no 0xFF within 40 bytes is rejected', label_at(b'A' * 50, 0) is None)
    print('%d checks, %d failures' % (10, fails))
    return fails


def main():
    nameguard.guard()
    ap = argparse.ArgumentParser()
    ap.add_argument('file', nargs='?')
    ap.add_argument('--base', type=lambda s: int(s, 0), default=BASE)
    ap.add_argument('--table', action='store_true')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        sys.exit(1 if selftest() else 0)
    if not a.file:
        ap.error('file required')
    d = open(dirguard.want_file(a.file, 'pdmenus'), 'rb').read()
    report(d, a.base, a.table)


if __name__ == '__main__':
    main()
