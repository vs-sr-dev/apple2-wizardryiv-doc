#!/usr/bin/env python3
"""Survey the T17Man document scripts: grammar, not content.

The five `.Man`/`.man` files on this disc are not compiled data.  They are the
source of a small markup language, complete with `#` comment banners, and the
viewer `T17Man` parses them at run time.  This tool reports the STRUCTURE --
which directives exist, how often, how many lines and sections, and whether
every file name a script mentions resolves to a file that is actually on the
disc -- and deliberately does not print the prose, which is the game's manual
and is not ours to redistribute.

Usage: python3 tools/manscript.py <iso-tree> [--sample N]
"""
import os, sys, re
from collections import Counter, OrderedDict

DIRECTIVE = re.compile(rb"^@([A-Za-z_][A-Za-z0-9_]*)\s*:?", re.M)
ASSIGN = re.compile(rb'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"([^"]*)"', re.M)
QUOTED = re.compile(rb'"([^"]*)"')


def main():
    root = sys.argv[1]
    sample = int(sys.argv[sys.argv.index("--sample") + 1]) if "--sample" in sys.argv else 0
    scripts = []
    for dp, dn, fn in os.walk(root):
        for f in sorted(fn):
            if f.lower().endswith((".man",)):
                scripts.append(os.path.join(dp, f))
    # the set of paths that exist, matched case-insensitively as AmigaDOS does
    onDisc = {}
    for dp, dn, fn in os.walk(root):
        for f in fn:
            rel = os.path.join(dp, f)[len(root):].replace(os.sep, "/").lstrip("/")
            onDisc[rel.lower()] = rel

    alldir = Counter()
    print("%-40s %8s %6s %6s %6s %8s" %
          ("script", "bytes", "lines", "cmnt", "direct", "assigns"))
    per = OrderedDict()
    for p in sorted(scripts):
        d = open(p, "rb").read()
        rel = p[len(root):].replace(os.sep, "/")
        lines = d.count(b"\n") + 1
        cmnt = len([l for l in d.split(b"\n") if l.strip().startswith(b"#")])
        dirs = DIRECTIVE.findall(d)
        asg = ASSIGN.findall(d)
        alldir.update(x.decode("latin1") for x in dirs)
        per[rel] = (d, dirs, asg)
        print("%-40s %8d %6d %6d %6d %8d" % (rel, len(d), lines, cmnt, len(dirs), len(asg)))
    print()
    print("=== directive vocabulary across all scripts ===")
    for k, v in alldir.most_common():
        print("  @%-16s x%d" % (k, v))
    print()
    print("=== every quoted file name, and whether it is on the disc ===")
    miss = 0
    seen = set()
    for rel, (d, dirs, asg) in per.items():
        for name, target in asg:
            t = target.decode("latin1")
            if not t or t in seen:
                continue
            seen.add(t)
            # scripts live in /SuperFrog and name things relative to it
            cands = [t, "SuperFrog/" + t]
            hit = None
            for c in cands:
                if c.lower() in onDisc:
                    hit = onDisc[c.lower()]
                    break
            print("  %-24s -> %-34s %s" %
                  (name.decode("latin1"), t, ("OK  " + hit) if hit else "*** NOT ON THE DISC"))
            if not hit:
                miss += 1
    print()
    print("  references that do not resolve: %d" % miss)
    if sample:
        print()
        print("=== first %d non-comment, non-blank lines of the English script ===" % sample)
        for rel, (d, dirs, asg) in per.items():
            if "English" not in rel:
                continue
            n = 0
            for l in d.split(b"\n"):
                s = l.strip()
                if not s or s.startswith(b"#"):
                    continue
                print("    %s" % s.decode("latin1")[:78])
                n += 1
                if n >= sample:
                    break


main()
