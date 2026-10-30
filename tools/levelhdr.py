#!/usr/bin/env python3
"""Read the header of Superfrog's level map files and the build reference in it.

Every `*MA*` (map) and some `*MS*` files carry, at fixed offsets 0xAF and 0xF8
of their unpacked image, a string of the form

    @SDIFF:<name>-IFF
     SDIFF:<name>-IFF

`SDIFF:` is an AmigaDOS assign that exists only on the developers' machine --
it is not created by any script on this disc -- and `<name>-IFF` is the IFF
source of the level's block sheet, which did not ship.  So each shipped map
still names the art file it was built from.

This reports every occurrence, the letter case (which is not consistent), and
checks each referenced name against the disc.

Usage: python3 tools/levelhdr.py <resident-dir> <iso-dir>
"""
import os, sys, re

PAT = re.compile(rb"@?([Ss][Dd][Ii][Ff][Ff]):([A-Za-z0-9_.\-]{1,24})")


def main():
    res, iso = sys.argv[1], sys.argv[2]
    on = set()
    for dp, dn, fn in os.walk(iso):
        for f in fn:
            on.add(f.lower())
    rows = []
    for f in sorted(os.listdir(res)):
        d = open(os.path.join(res, f), "rb").read()
        seen = []
        for m in PAT.finditer(d):
            seen.append((m.start(), m.group(1).decode("latin1"), m.group(2).decode("latin1")))
        if seen:
            rows.append((f, len(d), seen))
    print("%-46s %9s %8s %-8s %-16s %s" %
          ("file", "resident", "offset", "assign", "target", "on disc?"))
    cases = {}
    targets = set()
    for f, n, seen in rows:
        for off, asg, tgt in seen:
            cases[asg] = cases.get(asg, 0) + 1
            targets.add(tgt)
            print("%-46s %9d   0x%04x %-8s %-16s %s" %
                  (f, n, off, asg, tgt, "yes" if tgt.lower() in on else "NO"))
    print()
    print("files carrying the reference : %d" % len(rows))
    print("letter case of the assign    : %s" % cases)
    print("distinct targets             : %d" % len(targets))
    print("targets present on the disc  : %d" %
          sum(1 for t in targets if t.lower() in on))
    print()
    print("Note: `SDIFF:` is created by no script on this disc; `SDDISK1:` is the")
    print("only assign the launcher makes.  So the reference resolves nowhere on")
    print("the shipped media and is a leftover from the build machine.")


main()
