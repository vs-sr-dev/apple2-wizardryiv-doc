#!/usr/bin/env python3
"""Slot occupancy and translation completeness across Universe's four
language blocks.

Universe ships every line of the game in English, French, German and Italian,
in that order, inside the same blob, separated by a run of exactly 160 zero
bytes.  The four blocks are *positionally parallel*: record i of the French
block is the translation of record i of the English block.  Nothing declares
that -- there is no language table, no count and no index -- and it only shows
up once the blocks are split and the record counts are compared.

Two things fall out of the alignment and both are the point of this tool:

  * a slot that is empty in one block and filled in the other three is a line
    somebody did not write.
  * a slot whose four strings are byte-identical is a line nobody translated
    (or one that was never text -- a number, a name, a code).

Usage: python3 tools/slots.py <unpacked-dir> [--csv FILE]
"""
import sys, os, re, argparse

PAD = b'\x00' * 160
STR = re.compile(rb'[\x20-\x7e\x0a\x80-\x9a\xe1]{2,}\x00')
LANGS = ['EN', 'FR', 'DE', 'IT']


def blocks(b):
    out, i, n, start = [], 0, len(b), 0
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


def strings(seg):
    return [m.group()[:-1] for m in STR.finditer(seg)]


def prose(s):
    return len(s) >= 12 and b' ' in s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root')
    ap.add_argument('--csv')
    args = ap.parse_args()

    files = []
    for r, _d, fs in os.walk(args.root):
        for f in fs:
            files.append(os.path.join(r, f))
    files.sort()

    rows = ['blob,blocks,records_per_block,identical_all_four,'
            'empty_in_one_only']
    tot_al = tot_id = tot_gap = 0
    nblob = 0
    print('%-44s %2s %6s %8s %8s' %
          ('blob', 'bl', 'recs', 'same4', 'gap'))
    for p in files:
        b = open(p, 'rb').read()
        bl = [(s, e) for s, e in blocks(b) if len(strings(b[s:e])) >= 8]
        if len(bl) != 4:
            continue
        sets = [strings(b[s:e]) for s, e in bl]
        if len(set(len(x) for x in sets)) != 1:
            # the blocks do not line up record for record; report and skip
            print('%-44s %2d  UNALIGNED %s' %
                  (os.path.basename(p)[:44], len(bl),
                   [len(x) for x in sets]))
            continue
        n = len(sets[0])
        nblob += 1
        same = [i for i in range(n)
                if len(set(s[i] for s in sets)) == 1 and prose(sets[0][i])]
        gap = [i for i in range(n)
               if sum(1 for s in sets if not s[i].strip()) == 1]
        tot_al += n
        tot_id += len(same)
        tot_gap += len(gap)
        print('%-44s %2d %6d %8d %8d' %
              (os.path.basename(p)[:44], len(bl), n, len(same), len(gap)))
        for i in same:
            print('      identical in all four @%3d: %r' %
                  (i, sets[0][i][:64].decode('latin-1')))
        rows.append('%s,%d,%d,%d,%d' %
                    (os.path.relpath(p, args.root).replace('\\', '/'),
                     len(bl), n, len(same), len(gap)))
    print()
    print('blobs with four aligned language blocks: %d' % nblob)
    print('records aligned four ways              : %d' % tot_al)
    print('records identical in all four languages: %d' % tot_id)
    print('records empty in exactly one language  : %d' % tot_gap)
    if args.csv:
        open(args.csv, 'w').write('\n'.join(rows) + '\n')


if __name__ == '__main__':
    main()
