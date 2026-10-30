#!/usr/bin/env python3
"""Count MS-DOS-shaped paths and DOS text conventions in a corpus.

Three things separately, because they are three different pieces of evidence
about whether a PC was in the toolchain (step 35, open question 24):

  * backslash-separated paths  \\dir\\dir\\name.ext
  * CRLF line endings, and CRLF immediately followed by 0x1A (the DOS
    end-of-file marker), which together identify a file written by a DOS
    editor rather than one that merely contains a stray 0x0D
  * a census of raw backslash bytes, so the path count has a denominator

Usage: python3 tools/dospaths.py <dir-or-file>...
"""
import os, re, sys

PATH = re.compile(rb'[\x5c][A-Za-z0-9_]{1,20}[\x5c][ -~]{0,60}')
BS = b'\x5c'


def files(targets):
    for t in targets:
        if os.path.isdir(t):
            for dp, dn, fn in os.walk(t):
                for f in sorted(fn):
                    yield os.path.join(dp, f)
        else:
            yield t


def main():
    tot_bs = tot_crlf = tot_eof = 0
    hits = []
    for p in files(sys.argv[1:]):
        d = open(p, 'rb').read()
        tot_bs += d.count(BS)
        tot_crlf += d.count(b'\r\n')
        tot_eof += len(re.findall(b'\r\n\x1a', d))
        for m in PATH.finditer(d):
            s = m.group().split(b'\x00')[0]
            if s.count(BS) >= 2:
                hits.append((os.path.basename(p), m.start(), s))
    print("=== backslash paths (>=2 separators) : %d ===" % len(hits))
    for f, o, s in hits:
        print("  %-24s 0x%06x  %r" % (f, o, s.decode('latin-1')))
    print()
    print("raw backslash bytes in the corpus : %d" % tot_bs)
    print("CRLF pairs                        : %d" % tot_crlf)
    print("CRLF immediately followed by 0x1A : %d" % tot_eof)


if __name__ == '__main__':
    main()
