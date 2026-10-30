#!/usr/bin/env python3
"""idstrings.py -- find the strings that identify a build: RCS/SCCS keywords,
AmigaDOS `$VER:` version cookies, bare build banners, and device/library names.

The checklist asks for `$VER:` first and a bare banner second.  This disc turns
out to carry a third kind that the set has not seen before: **expanded RCS
`$Header:` keywords**, which carry a filesystem path, a revision number, a
timestamp and a user name, and which are therefore a stronger dating instrument
than a `$VER:` -- a `$VER:` is written by hand, an RCS keyword is stamped by the
version control system at check-out.

Output is written as UTF-8 regardless of the console code page, because this
shell's default encoding cannot represent every byte a 1993 Amiga binary holds.

Usage: idstrings.py FILE...
"""
import sys, re, os, glob

PATTERNS = [
    (re.compile(rb'\$Header:[^$]{0,200}\$'), 'RCS $Header'),
    (re.compile(rb'\$Id:[^$]{0,200}\$'), 'RCS $Id'),
    (re.compile(rb'\$Revision:[^$]{0,100}\$'), 'RCS $Revision'),
    (re.compile(rb'\$Date:[^$]{0,100}\$'), 'RCS $Date'),
    (re.compile(rb'\$Author:[^$]{0,100}\$'), 'RCS $Author'),
    (re.compile(rb'\$Log:[^$]{0,200}\$'), 'RCS $Log'),
    (re.compile(rb'@\(#\)[\x20-\x7e]{4,120}'), 'SCCS what()'),
    (re.compile(rb'\$VER:[\x20-\x7e]{1,90}'), 'AmigaDOS $VER:'),
    (re.compile(rb'[A-Za-z0-9_.-]{2,40}\.(?:library|device|font)\x00'), 'name'),
]


def main():
    files = []
    for a in sys.argv[1:]:
        if os.path.isdir(a):
            files += [p for p in glob.glob(a + '/**/*', recursive=True)
                      if os.path.isfile(p)]
        else:
            files += glob.glob(a)
    out = sys.stdout
    try:
        out.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    for p in sorted(files):
        d = open(p, 'rb').read()
        hits = []
        for rx, kind in PATTERNS:
            for m in rx.finditer(d):
                s = m.group().rstrip(b'\x00').decode('latin-1')
                hits.append((m.start(), kind, s))
        if not hits:
            continue
        print("=== %s (%d bytes)" % (p, len(d)), file=out)
        seen = set()
        for off, kind, s in sorted(hits):
            key = (kind, s)
            if kind == 'name' and key in seen:
                continue
            seen.add(key)
            print("  0x%06x  %-14s %s" % (off, kind, s), file=out)


if __name__ == '__main__':
    main()
