#!/usr/bin/env python3
"""recount.py -- re-derive the counts the document quotes, from the section 10
baseline table, instead of incrementing them.

The Myth session found the `.TM` section still saying "ten discs with the
Commodore banner" four discs after that stopped being true, and the Akiko
denominators still reading 14 when the set held 17.  A number that is two discs
stale is indistinguishable from a number that was measured, and the only defence
is to re-derive.

This reads the baseline table -- which `addcolumn.py` guarantees is rectangular
and complete -- and prints the counts the prose is supposed to agree with.

Usage: python3 tools/recount.py cd32-platform-notes.md
"""
import sys, io, re


def split_row(line):
    s = line.rstrip('\n').rstrip()
    return s[1:-1].split('|')


def find_table(lines, first_label):
    for i, ln in enumerate(lines):
        if not ln.startswith('|'):
            continue
        if i + 1 < len(lines) and re.match(r'^\|[\s:-]+\|', lines[i + 1]):
            j = i
            while j < len(lines) and lines[j].startswith('|'):
                j += 1
            body = [split_row(x) for x in lines[i + 2:j]]
            if body and body[0][0].strip() == first_label:
                return i, j
    raise SystemExit("table not found")


def main():
    lines = io.open(sys.argv[1], encoding='utf-8').read().split('\n')
    s, e = find_table(lines, "Publisher / studio")
    rows = [split_row(x) for x in lines[s:e]]
    header = [c.strip() for c in rows[0][1:]]
    data = {r[0].strip(): [c.strip() for c in r[1:]] for r in rows[2:]}
    n = len(header)

    out = sys.stdout
    try:
        out.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    print("baseline table: %d discs" % n, file=out)
    for i, h in enumerate(header):
        print("  %2d  %s" % (i + 1, re.sub(r'\*', '', h)), file=out)
    print(file=out)

    def count(row, test, label):
        if row not in data:
            print("  !! no such row: %r" % row, file=out)
            return
        cells = data[row]
        hits = [header[i] for i, c in enumerate(cells) if test(c)]
        print("%-34s %2d of %d" % (label, len(hits), n), file=out)
        for h in hits:
            print("      %s" % re.sub(r'\*', '', h), file=out)
        print(file=out)

    low = lambda c: c.lower()

    print("=== counts to check the prose against ===\n", file=out)

    count("`.TM` contents", lambda c: 'identical' in low(c),
          ".TM: identical three SHA-1s")
    count("Preparer field", lambda c: 'pocock' in low(c),
          "preparer field names D J Pocock")
    count("Akiko", lambda c: 'untouched' in low(c) or 'zero' in low(c)
          or 'all four figures zero' in low(c),
          "Akiko untouched")
    count("Akiko", lambda c: 'direct' in low(c),
          "Akiko driven directly")
    count("Compression", lambda c: 'rnc' in low(c),
          "compression mentions RNC")
    count("Save system", lambda c: 'none' in low(c),
          "save system: none")
    count("Music", lambda c: 'red book' in low(c),
          "music: Red Book present")
    count("PVD system id", lambda c: 'cdtv' in low(c),
          "PVD system id says CDTV")
    count("Tracks", lambda c: 'no audio' in low(c) or 'without audio' in low(c),
          "no audio track")
    count("`freeanim.library`", lambda c: 'not shipped' in low(c)
          or 'named but' in low(c), "freeanim named but not shipped")

    print("=== rows available, for writing further checks ===", file=out)
    for k in data:
        print("  %s" % k, file=out)


if __name__ == '__main__':
    main()
