#!/usr/bin/env python3
"""Count the device-qualified paths a binary asks for, by device.

The rule "compression <=> floppy origin" is tested from the disc, and on this
disc the evidence is not indirect: the CD executable carries its data-file
names with a floppy drive still attached to the front of them.  This counts
every NUL-terminated string of the form `<DEVICE>:<name>` and groups by the
device, so the two vocabularies can be compared entry for entry.

Usage: python3 tools/devpaths.py <dir> [--device NAME]
"""
import os, sys, re
from collections import defaultdict

PAT = re.compile(rb"([A-Za-z][A-Za-z0-9_]{1,10}[0-9]?):([A-Za-z0-9_.\-]{1,24})\x00")


def main():
    root = sys.argv[1]
    want = sys.argv[sys.argv.index("--device") + 1].lower() if "--device" in sys.argv else None
    per = defaultdict(lambda: defaultdict(set))
    for dp, dn, fn in os.walk(root):
        for f in sorted(fn):
            p = os.path.join(dp, f)
            d = open(p, "rb").read()
            rel = p[len(root):].replace(os.sep, "/")
            for m in PAT.finditer(d):
                dev = m.group(1).decode("latin1")
                nm = m.group(2).decode("latin1")
                if want and dev.lower() != want:
                    continue
                per[dev][rel].add(nm)
    for dev in sorted(per, key=lambda k: -sum(len(v) for v in per[k].values())):
        tot = sum(len(v) for v in per[dev].values())
        print("=== %s:  %d distinct names across %d files ===" % (dev, tot, len(per[dev])))
        for rel in sorted(per[dev]):
            names = sorted(per[dev][rel])
            print("  %-48s %3d: %s" % (rel, len(names), " ".join(names[:24])))
            if len(names) > 24:
                print("  %-48s      %s" % ("", " ".join(names[24:])))
        print()


main()
