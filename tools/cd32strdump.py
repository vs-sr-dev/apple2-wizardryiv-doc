#!/usr/bin/env python3
"""Printable-run dump with file offsets, and an optional per-hunk attribution.

`strings` is not present in this shell, and the offset matters: a banner inside
a CODE hunk means something different from the same bytes in a DATA hunk.

Usage:
    python3 tools/strdump.py <file> [--min N] [--max N] [--grep RE] [--hunks]
"""
import sys, os, re, struct, argparse


def hunks(d):
    """(index, kind, file_offset, length) for each hunk body, or [] if not a hunk file."""
    if d[:4] != b"\x00\x00\x03\xf3":
        return []
    o = 4
    n = struct.unpack_from(">I", d, o)[0]; o += 4
    while n:
        o += 4 * (n + 1)
        n = struct.unpack_from(">I", d, o)[0]; o += 4
    first, last = struct.unpack_from(">II", d, o); o += 8
    cnt = last - first + 1
    sizes = []
    for i in range(cnt):
        v = struct.unpack_from(">I", d, o)[0]; o += 4
        sizes.append((v & 0x3FFFFFFF) * 4)
    out = []
    i = 0
    while o < len(d) and i < cnt:
        t = struct.unpack_from(">I", d, o)[0] & 0x3FFFFFFF
        o += 4
        if t in (0x3E9, 0x3EA, 0x3EB):  # CODE DATA BSS
            ln = struct.unpack_from(">I", d, o)[0] * 4; o += 4
            kind = {0x3E9: "CODE", 0x3EA: "DATA", 0x3EB: "BSS"}[t]
            if t == 0x3EB:
                out.append((i, kind, None, ln))
            else:
                out.append((i, kind, o, ln))
                o += ln
        elif t == 0x3EC:  # RELOC32
            while True:
                c = struct.unpack_from(">I", d, o)[0]; o += 4
                if c == 0:
                    break
                o += 4 + 4 * c
        elif t == 0x3F2:  # END
            i += 1
            continue
        elif t in (0x3F0, 0x3F1):  # SYMBOL / DEBUG
            ln = struct.unpack_from(">I", d, o)[0] * 4; o += 4 + ln
        else:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--min", type=int, default=6)
    ap.add_argument("--max", type=int, default=0, help="truncate each run to N chars")
    ap.add_argument("--grep")
    ap.add_argument("--hunks", action="store_true")
    a = ap.parse_args()

    d = open(a.file, "rb").read()
    hs = hunks(d) if a.hunks else []

    def where(off):
        for i, k, fo, ln in hs:
            if fo is not None and fo <= off < fo + ln:
                return "%s%d+0x%x" % (k, i, off - fo)
        return "-"

    pat = re.compile(a.grep) if a.grep else None
    rx = re.compile(rb"[\x20-\x7e]{%d,}" % a.min)
    for m in rx.finditer(d):
        s = m.group().decode("ascii")
        if pat and not pat.search(s):
            continue
        if a.max and len(s) > a.max:
            s = s[:a.max] + "..."
        if hs:
            print("0x%08x %-14s %s" % (m.start(), where(m.start()), s))
        else:
            print("0x%08x %s" % (m.start(), s))


if __name__ == "__main__":
    main()
