#!/usr/bin/env python3
"""Find AmigaOS library and device names without inventing any.

A printable-run dump glues the ASCII of nearby 68000 opcodes onto the front of
a string -- `4E 75` (`rts`) reads `Nu`, `4E 5D` (`unlk a5`) reads `N]`, and the
result is names like `Nucd.device` and `,_Nudiskfont.library` that no library
ever had.  Rather than trying to strip a prefix, this finds the NUL-terminated
suffix and walks *backwards* from it while the byte is in the character set a
real library name uses -- lowercase ASCII, digits, `.`, `_`, `-`.  Uppercase
`N` is not in that set, so an opcode byte can never be absorbed.

Usage: python3 tools/libscan.py <dir-or-file>...
"""
import os, sys, re
from collections import Counter, defaultdict

TAILS = (b".library\x00", b".device\x00", b".font\x00", b".datatype\x00")
OK = set(b"abcdefghijklmnopqrstuvwxyz0123456789._-")


def find(d):
    out = []
    for tail in TAILS:
        start = 0
        while True:
            i = d.find(tail, start)
            if i < 0:
                break
            start = i + 1
            j = i
            while j > 0 and d[j - 1] in OK:
                j -= 1
            # `4E 75` is `rts`; its low byte is a lowercase `u`, which IS a legal
            # name character, so the backwards walk absorbs it and invents
            # `ufreeanim.library`, `udos.library`, `ucd.device`.  The test is
            # exact: if the name starts with `u` and the byte before it is 0x4E,
            # that `u` is the second half of an opcode, not the first letter.
            stripped = False
            while j < i and d[j] == 0x75 and j > 0 and d[j - 1] == 0x4E:
                j += 1
                stripped = True
            name = d[j:i + len(tail) - 1].decode("latin1")
            if name.startswith(".") or len(name) < 3:
                continue
            out.append((j, name, stripped))
    return sorted(set(out))


def main():
    per = defaultdict(set)
    allc = Counter()
    for root in sys.argv[1:]:
        files = []
        if os.path.isdir(root):
            for dp, dn, fn in os.walk(root):
                for f in sorted(fn):
                    files.append(os.path.join(dp, f))
        else:
            files = [root]
        for p in files:
            d = open(p, "rb").read()
            rel = p[len(root):].replace(os.sep, "/") if os.path.isdir(root) else p
            for off, nm, stripped in find(d):
                per[rel].add(nm + ("*" if stripped else ""))
                allc[nm] += 1
    for rel in sorted(per):
        print("%-52s %s" % (rel, "  ".join(sorted(per[rel]))))
    print()
    print("  * = a leading `u` was stripped: the preceding byte is 0x4E, so the pair")
    print("    is `rts` and the `u` is opcode, not name.")
    print()
    print("=== all names, by number of files mentioning them ===")
    for nm, v in allc.most_common():
        print("  %-28s %3d" % (nm, v))


main()
