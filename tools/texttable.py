#!/usr/bin/env python3
"""Walk Myth's inline text records.

The game stores its display text as a chain of records, not as an offset
table, so none of the three offset-table traps applies.  A record is

    [flag] [column] [row] TEXT NUL

with flag $FF starting a new page and $00 continuing the current one, and
column/row being character positions (row values step in multiples of 8).
The separator byte doubles as the previous record's terminator, so the text
run ends at the next $00 or $FF rather than at a NUL of its own.
A raw strings dump reports the row byte as a leading character on every line,
which is why the credits look like `:MARK CALE` and `2THE FINAL` in one.

The walk starts at a given offset and stops at the first record whose text is
not printable, so the end of the table is found rather than assumed.

Usage: python3 tools/texttable.py <file> <start> [--max N]
"""
import sys, argparse

PRINT = set(range(0x20, 0x7f))


def walk(d, o, maxrec=4000):
    out = []
    while len(out) < maxrec and o + 4 < len(d):
        flag, col, row = d[o], d[o + 1], d[o + 2]
        if flag not in (0x00, 0xFF):
            break
        e = o + 3
        while e < len(d) and d[e] in PRINT:
            e += 1
        if e == o + 3 or e >= len(d) or d[e] not in (0x00, 0xFF):
            break
        out.append((o, flag, col, row, d[o + 3:e].decode('latin-1')))
        o = e
    return out, o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file')
    ap.add_argument('start')
    ap.add_argument('--max', type=int, default=4000)
    a = ap.parse_args()
    d = open(a.file, 'rb').read()
    recs, end = walk(d, int(a.start, 0), a.max)
    page = 0
    print("%-8s %-4s %-4s %-4s  %s" % ("offset", "flag", "col", "row", "text"))
    for o, flag, col, row, t in recs:
        if flag == 0xFF:
            page += 1
            print("  --- page %d ---" % page)
        print("%08x %-4s %-4d %-4d  %s" %
              (o, "NEW" if flag == 0xFF else "", col, row, t))
    print()
    print("%d records, %d pages, walk ended at 0x%x" % (len(recs), page, end))
    print("text bytes %d, record overhead %d (%.1f%%)" %
          (sum(len(r[4]) for r in recs), 3 * len(recs),
           100.0 * 3 * len(recs) / max(1, sum(len(r[4]) for r in recs) + 3 * len(recs))))


if __name__ == '__main__':
    main()
