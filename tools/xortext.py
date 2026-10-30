#!/usr/bin/env python3
"""Recover the XOR-obfuscated string table in the Fire & Ice main executable.

The game's user-visible text is not stored as plain ASCII.  Every byte is
XORed with a single constant, which shows up immediately once you notice
that the word separator in the raw dump is `;` (0x3B) rather than a space
(0x20):  0x3B ^ 0x20 = 0x1B.

The tool does not assume the key.  It recovers it the same way: for each
candidate key 0..255 it XORs the file and scores the result on how much
printable, space-separated English text falls out, then dumps every run of
at least `-n` characters that decodes cleanly.

Usage:
    python3 tools/xortext.py FILE                 # recover key, dump strings
    python3 tools/xortext.py FILE --key 0x1b
    python3 tools/xortext.py FILE --range 0x1770 0x2000
"""
import sys, argparse, re

PRINT = set(range(0x20, 0x7f))
WORDY = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ")


def score(data, key):
    """Longest-run-weighted count of plausible words after XOR by `key`."""
    dec = bytes(b ^ key for b in data)
    total = 0
    for m in re.finditer(rb"[A-Za-z][A-Za-z'\-]{2,}", dec):
        total += len(m.group(0))
    # a key that just maps everything to letters is not interesting; require
    # spaces to appear at a plausible English rate
    sp = dec.count(b' ')
    if sp == 0:
        return 0
    return total


def runs(data, key, minlen):
    dec = bytes(b ^ key for b in data)
    out, start = [], None
    for i, b in enumerate(dec):
        if b in PRINT:
            if start is None:
                start = i
        else:
            if start is not None and i - start >= minlen:
                out.append((start, dec[start:i].decode('latin-1')))
            start = None
    if start is not None and len(dec) - start >= minlen:
        out.append((start, dec[start:].decode('latin-1')))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--key", type=lambda s: int(s, 0))
    ap.add_argument("-n", type=int, default=5)
    ap.add_argument("--range", nargs=2, type=lambda s: int(s, 0))
    a = ap.parse_args()
    d = open(a.file, 'rb').read()
    if a.range:
        lo, hi = a.range
    else:
        lo, hi = 0, len(d)
    seg = d[lo:hi]

    if a.key is None:
        best = sorted(((score(seg, k), k) for k in range(256)), reverse=True)
        print("# key search (top 5):", file=sys.stderr)
        for s, k in best[:5]:
            print("#   key 0x%02x  score %d" % (k, s), file=sys.stderr)
        key = best[0][1]
    else:
        key = a.key
    print("# XOR key 0x%02x" % key, file=sys.stderr)

    for off, s in runs(seg, key, a.n):
        # only print runs that look like text rather than XORed code
        letters = sum(1 for c in s if c.isalpha() or c == ' ')
        if letters * 100 >= len(s) * 70:
            print("%08x  %s" % (lo + off, s))


main()
