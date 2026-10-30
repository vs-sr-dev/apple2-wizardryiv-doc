#!/usr/bin/env python3
"""Recover the floppy disk layout of the 1993 release from the CD executable.

`SuperFrogCD` carries four parallel vocabularies of the same asset names --
one per AmigaDOS device -- so the assignment of assets to floppies in the
original release can be read straight out of the CD binary:

    SDDISK1:  the CD path, redirected by `Assign SDDISK1: SFData`
    DF0:      internal drive
    DF1:      second drive
    DF2:      third drive

This prints the per-device sets, the union of the floppy devices, and the
difference against the SDDISK1 set both ways, so any asset that exists on one
side and not the other is visible rather than assumed away.

Usage: python3 tools/floppymap.py <file>
"""
import sys, re
from collections import defaultdict

PAT = re.compile(rb"(SDDISK1|DF[0-3]):([A-Za-z0-9_.\-]{1,24})\x00")


def main():
    d = open(sys.argv[1], "rb").read()
    per = defaultdict(set)
    order = defaultdict(list)
    for m in PAT.finditer(d):
        dev = m.group(1).decode("latin1")
        nm = m.group(2).decode("latin1")
        per[dev].add(nm)
        if nm not in order[dev]:
            order[dev].append(nm)
    for dev in sorted(per):
        print("=== %s: %d names ===" % (dev, len(per[dev])))
        print("   " + " ".join(sorted(per[dev])))
        print()
    fl = set()
    for dev in ("DF0", "DF1", "DF2", "DF3"):
        fl |= per.get(dev, set())
    cd = per.get("SDDISK1", set())
    print("union of DF0/DF1/DF2 : %d names" % len(fl))
    print("SDDISK1              : %d names" % len(cd))
    print()
    print("on a floppy but NOT under SDDISK1 (%d): %s" %
          (len(fl - cd), " ".join(sorted(fl - cd)) or "none"))
    print()
    print("under SDDISK1 but on NO floppy (%d): %s" %
          (len(cd - fl), " ".join(sorted(cd - fl)) or "none"))
    print()
    ov = defaultdict(list)
    for nm in sorted(fl):
        ds = [dev for dev in ("DF0", "DF1", "DF2") if nm in per.get(dev, set())]
        ov[",".join(ds)].append(nm)
    print("=== assets by which floppy drive(s) name them ===")
    for k in sorted(ov):
        print("  %-12s %3d: %s" % (k, len(ov[k]), " ".join(ov[k])))


main()
