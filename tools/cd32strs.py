#!/usr/bin/env python3
"""Printable-run dump that does not invent strings out of 68000 opcodes.

The trap, from the Gunship disc and live again on this one: `4E 75` is `rts`
and reads as `Nu` in ASCII, so a naive run dump glues a `u` (and often an `N`)
onto the front of the next string and produces library and device names that
do not exist -- `Nucd.device`, `N]Nuscsi.device`, `Nugameport.device`.
`4E 5D` is `unlk a5` and reads as `N]`; `4E 71` is `nop` and reads as `Nq`.

So every run is re-read from the bytes: if it begins with one of those
opcode digraphs and the bytes immediately before it are the tail of an
instruction stream rather than of a string, the digraph is stripped and
reported, rather than being silently kept or silently dropped.

Usage: python3 tools/strs.py FILE [--min N] [--max N] [--grep RE] [--raw]
"""
import sys, re, argparse

OPCODE_PREFIXES = [
    (b"\x4e\x75", "rts"), (b"\x4e\x71", "nop"), (b"\x4e\x5d", "unlk a5"),
    (b"\x4e\x5e", "unlk a6"), (b"\x4e\x73", "rte"), (b"\x4e\x77", "rtr"),
]


def runs(d, mn):
    out = []
    cur = []
    start = 0
    for i, b in enumerate(d):
        if 32 <= b < 127 or b == 9:
            if not cur:
                start = i
            cur.append(b)
        else:
            if len(cur) >= mn:
                out.append((start, bytes(cur)))
            cur = []
    if len(cur) >= mn:
        out.append((start, bytes(cur)))
    return out


def strip_opcode(off, s, d):
    """Return (new_off, new_s, note)."""
    for pre, name in OPCODE_PREFIXES:
        want = pre.decode("latin1")
        if s.startswith(want):
            # the digraph is at file offset `off`; treat it as an opcode when it
            # is even-aligned, which is where a 68000 instruction has to be
            if off % 2 == 0:
                return off + 2, s[2:], "stripped %r (%s)" % (want, name)
    return off, s, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--min", type=int, default=5)
    ap.add_argument("--max", type=int, default=0)
    ap.add_argument("--grep", default=None)
    ap.add_argument("--raw", action="store_true",
                    help="do not strip opcode digraphs; show what a naive dump would say")
    a = ap.parse_args()
    d = open(a.file, "rb").read()
    rx = re.compile(a.grep) if a.grep else None
    for off, b in runs(d, a.min):
        s = b.decode("latin1")
        note = ""
        if not a.raw:
            off, s, note = strip_opcode(off, s, d)
            if len(s) < a.min:
                continue
        if rx and not rx.search(s):
            continue
        shown = s[:a.max] if a.max else s
        print("0x%08x %s%s" % (off, shown, ("   [%s]" % note) if note else ""))


main()
