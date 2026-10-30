#!/usr/bin/env python3
"""Split Universe's text blobs into their language blocks and compare them.

Every text blob on this disc is a concatenation of language blocks separated
by a run of exactly 160 zero bytes.  Nothing declares the block count, the
languages or the boundaries -- the 160-byte run is the only marker, and it is
the same length everywhere, which is what makes it recognisable rather than
just "some padding".

The tool reports, per blob:

  * the block boundaries and sizes,
  * a language guess per block, scored on stopwords and on the CP437 accented
    bytes each language actually uses,
  * the NUL-terminated strings in each block,
  * and how many strings are byte-identical to the English block -- which is
    where a translation stopped, or where the string was never text to begin
    with.

Usage: python3 tools/langsplit.py <dir> [--csv FILE] [--verbose]
"""
import sys, os, re, argparse, collections

PAD = b'\x00' * 160
STR = re.compile(rb'[\x20-\x7e\x0a\x80-\x9a\xe1]{4,}\x00')

# stopwords that do not overlap between these four languages
MARKS = {
    'en': [b' the ', b' you ', b' and ', b' this ', b' with ', b' that '],
    'fr': [b' les ', b' vous ', b' est ', b' une ', b' pour ', b' dans '],
    'de': [b' der ', b' die ', b' und ', b' nicht ', b' ich ', b' das '],
    'it': [b' che ', b' non ', b' della ', b' sono ', b' una ', b' per '],
}
# CP437 bytes each language leans on
ACCENT = {'fr': {0x82, 0x85, 0x8a, 0x87, 0x88}, 'de': {0x81, 0xe1, 0x84, 0x94},
          'it': {0x8a, 0x85, 0x97, 0x8d, 0x95}, 'en': set()}


def blocks(b):
    """Split on runs of >=160 zero bytes; return (start, end) per block."""
    out, i, n = [], 0, len(b)
    start = 0
    while i < n:
        if b[i] == 0:
            j = i
            while j < n and b[j] == 0:
                j += 1
            if j - i >= 160:
                if i > start:
                    out.append((start, i))
                start = j
            i = j
        else:
            i += 1
    if start < n:
        out.append((start, n))
    return out


def guess(seg):
    low = seg.lower()
    sc = {k: sum(low.count(w) for w in ws) for k, ws in MARKS.items()}
    for k, acc in ACCENT.items():
        sc[k] += sum(seg.count(bytes([a])) for a in acc) // 4
    best = max(sc, key=lambda k: sc[k])
    return (best if sc[best] else '??'), sc


def strings(seg):
    return [m.group()[:-1] for m in STR.finditer(seg)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root')
    ap.add_argument('--csv')
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()

    files = []
    for r, _d, fs in os.walk(args.root):
        for f in fs:
            files.append(os.path.join(r, f))
    files.sort()

    rows = ['blob,block,start,end,bytes,lang,strings,strbytes,identical_to_en']
    tally = collections.Counter()
    langbytes = collections.Counter()
    multi = 0
    print('%-46s %2s %8s %8s %4s %6s %8s %6s' %
          ('blob', '#', 'start', 'bytes', 'lang', 'strs', 'strbytes', '=EN'))
    for p in files:
        b = open(p, 'rb').read()
        bl = blocks(b)
        if len(bl) < 2:
            continue
        segs = [(s, e, b[s:e]) for s, e in bl]
        # keep only blobs where at least two blocks carry real text
        texty = [x for x in segs if len(strings(x[2])) >= 3]
        if len(texty) < 2:
            continue
        multi += 1
        rel = os.path.relpath(p, args.root).replace('\\', '/')
        en = None
        for i, (s, e, seg) in enumerate(segs):
            ss = strings(seg)
            lang, _sc = guess(seg)
            if lang == 'en' and en is None:
                en = set(ss)
            same = len(set(ss) & en) if en else 0
            tally[lang] += 1
            langbytes[lang] += sum(len(x) for x in ss)
            print('%-46s %2d %8d %8d %4s %6d %8d %6d' %
                  (os.path.basename(p)[:46] if i == 0 else '', i, s, e - s,
                   lang, len(ss), sum(len(x) for x in ss), same))
            rows.append('%s,%d,%d,%d,%d,%s,%d,%d,%d' %
                        (rel, i, s, e, e - s, lang, len(ss),
                         sum(len(x) for x in ss), same))
            if args.verbose and en and lang != 'en':
                for x in ss:
                    if x in en and len(x) > 6:
                        print('        untranslated: %r' % x[:70])
    print()
    print('blobs with language blocks: %d' % multi)
    print('blocks by language: %s' % dict(tally))
    print('string bytes by language: %s' % dict(langbytes))
    if args.csv:
        open(args.csv, 'w').write('\n'.join(rows) + '\n')


if __name__ == '__main__':
    main()
