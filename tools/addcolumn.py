#!/usr/bin/env python3
"""Add one disc's column to the section 10 baseline table, safely.

Written on [Superfrog] after a column was added to the narrative and not to
every row on [Gunship 2000], and reused unchanged on every disc since.  The
contract is:

  1. locate the table by its row labels, not by line number;
  2. validate BEFORE  -- every row must have the same number of cells;
  3. append exactly one cell to every row, taken from a label->text map;
  4. validate AFTER   -- every row must have the same number of cells, that
     number must be exactly one more than before, and NO NEW CELL MAY BE
     EMPTY;
  5. refuse to write if any check fails, and say which row failed.

Usage: python3 tools/addcolumn.py <notes.md> <column.py>

where <column.py> defines TITLE (the header cell) and CELLS (a dict from row
label to cell text).  Every existing row label must appear in CELLS.
"""
import sys, os, re, io, importlib.util


def split_row(line):
    """Split a markdown table row into cells. Leading and trailing pipes are
    delimiters, not cells."""
    s = line.rstrip('\n')
    assert s.startswith('|') and s.rstrip().endswith('|'), s[:60]
    return s.rstrip()[1:-1].split('|')


def join_row(cells):
    return '|' + '|'.join(cells) + '|'


def label(cells):
    return cells[0].strip()


def find_table(lines, first_label):
    """Return (start, end) line indices of the contiguous table whose first
    data row carries `first_label`."""
    for i, ln in enumerate(lines):
        if not ln.startswith('|'):
            continue
        # a table header is followed by a separator row
        if i + 1 < len(lines) and re.match(r'^\|[\s:-]+\|', lines[i + 1]):
            j = i
            while j < len(lines) and lines[j].startswith('|'):
                j += 1
            body = [split_row(x) for x in lines[i + 2:j]]
            if body and label(body[0]) == first_label:
                return i, j
    raise SystemExit("table whose first data row is %r not found" % first_label)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    notes, colmod = sys.argv[1], sys.argv[2]
    spec = importlib.util.spec_from_file_location("column", colmod)
    col = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(col)

    lines = io.open(notes, encoding='utf-8').read().split('\n')
    first = next(iter(col.CELLS))
    s, e = find_table(lines, first)
    rows = [split_row(x) for x in lines[s:e]]

    # ---- validate BEFORE
    widths = set(len(r) for r in rows)
    if len(widths) != 1:
        for i, r in enumerate(rows):
            print("  row %2d  %-34s %d cells" % (i, label(r), len(r)))
        raise SystemExit("REFUSING: table is already ragged, widths %s" % sorted(widths))
    before = widths.pop()
    print("table at lines %d-%d, %d rows, %d cells each" % (s + 1, e, len(rows), before))

    # ---- check every data row has a cell waiting for it
    missing = [label(r) for r in rows[2:] if label(r) not in col.CELLS]
    if missing:
        for m in missing:
            print("  no cell supplied for row %r" % m)
        raise SystemExit("REFUSING: %d of %d data rows have no new cell" %
                         (len(missing), len(rows) - 2))
    extra = [k for k in col.CELLS if k not in [label(r) for r in rows[2:]]]
    if extra:
        raise SystemExit("REFUSING: cells supplied for rows that do not exist: %s" % extra)

    # ---- append
    out = []
    for i, r in enumerate(rows):
        if i == 0:
            r = r + [' %s ' % col.TITLE]
        elif i == 1:
            r = r + ['---']
        else:
            r = r + [' %s ' % col.CELLS[label(r)].strip()]
        out.append(r)

    # ---- validate AFTER
    widths = set(len(r) for r in out)
    if len(widths) != 1:
        raise SystemExit("REFUSING: table would be ragged, widths %s" % sorted(widths))
    after = widths.pop()
    if after != before + 1:
        raise SystemExit("REFUSING: width went %d -> %d, expected +1" % (before, after))
    empty = [label(r) for r in out[2:] if not r[-1].strip()]
    if empty:
        for m in empty:
            print("  new cell is empty for row %r" % m)
        raise SystemExit("REFUSING: %d new cells are empty" % len(empty))

    lines[s:e] = [join_row(r) for r in out]
    io.open(notes, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
    print("OK: %d rows widened %d -> %d, %d new cells, none empty" %
          (len(out), before, after, len(out) - 2))


if __name__ == '__main__':
    main()
