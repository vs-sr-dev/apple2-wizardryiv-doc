#!/usr/bin/env python3
"""Dump every readable run of the XOR-obfuscated text on this disc.

Fire & Ice stores all of its user-visible text XORed with 0x1b, both in the
main executable's chip DATA hunk and inside the PowerPacker-packed `.bin`
resources (which must be unpacked first -- see tools/pp20.py).  This tool
walks a directory, XORs every file with the key, and prints every run of
printable characters that is mostly letters and spaces, with its file
offset.

The key is not hard-coded into the search: `--find-key` scores all 256
candidates on English-like output over the region given.

Usage:
    python3 tools/textdump.py DIR [--key 0x1b] [-n 5] [--min-alpha 0.75]
"""
import os, sys, argparse

PRINT = set(range(0x20, 0x7f))


def find_key(d):
    import re
    best = (0, 0)
    for k in range(256):
        dec = bytes(b ^ k for b in d)
        s = sum(len(m.group(0))
                for m in re.finditer(rb"[A-Z][a-z]{2,}(?: [A-Za-z]{2,})+", dec))
        if s > best[0]:
            best = (s, k)
    return best[1]


def runs(d, key, minlen, min_alpha):
    dec = bytes(b ^ key for b in d)
    out, start = [], None
    for i, b in enumerate(dec):
        if b in PRINT:
            if start is None:
                start = i
        else:
            if start is not None and i - start >= minlen:
                out.append((start, dec[start:i]))
            start = None
    if start is not None and len(dec) - start >= minlen:
        out.append((start, dec[start:]))
    res = []
    for off, s in out:
        a = sum(1 for c in s if 65 <= c <= 90 or 97 <= c <= 122 or c == 32)
        if a >= len(s) * min_alpha:
            res.append((off, s.decode('latin-1')))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--key", type=lambda s: int(s, 0))
    ap.add_argument("--find-key", action="store_true")
    ap.add_argument("-n", type=int, default=5)
    ap.add_argument("--min-alpha", type=float, default=0.75)
    a = ap.parse_args()
    for root, _, names in os.walk(a.dir):
        for n in sorted(names):
            p = os.path.join(root, n)
            rel = os.path.relpath(p, a.dir).replace(chr(92), '/')
            d = open(p, 'rb').read()
            key = find_key(d) if (a.find_key or a.key is None) else a.key
            r = runs(d, key, a.n, a.min_alpha)
            if not r:
                continue
            print("### %s   (XOR key 0x%02x, %d runs)" % (rel, key, len(r)))
            for off, s in r:
                print("    %08x  %s" % (off, s))
            print()


main()
