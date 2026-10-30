#!/usr/bin/env python3
"""Count `jsr d16(a6)` library calls by displacement, and name the candidates.

A `4E AE xxxx` encoding says nothing about which library base is in a6, and
several displacements mean different things in exec and in graphics -- -456 is
exec/DoIO and graphics/OwnBlitter, -462 is exec/SendIO and graphics/DisownBlitter.
Any tool that prints one name per displacement is asserting something the bytes
do not contain.  This one prints every candidate and leaves the disambiguation
to the reader.

    python3 tools/lvoscan.py FILE [FILE ...]
"""
import sys, re, struct, collections

LVO = {
    -30: ["dos/Open"], -36: ["dos/Close"], -42: ["dos/Read"], -48: ["dos/Write"],
    -120: ["exec/Disable"], -126: ["exec/Enable"],
    -132: ["exec/Forbid"], -138: ["exec/Permit"],
    -192: ["graphics/LoadRGB4"], -198: ["exec/AllocMem"],
    -210: ["exec/FreeMem"],
    -222: ["graphics/LoadView"], -228: ["graphics/WaitBlit"],
    -270: ["graphics/WaitTOF"],
    -294: ["exec/AllocSignal"],
    -408: ["exec/OldOpenLibrary"], -414: ["exec/CloseLibrary"],
    -444: ["exec/OpenDevice"], -450: ["exec/CloseDevice"],
    -456: ["exec/DoIO", "graphics/OwnBlitter"],
    -462: ["exec/SendIO", "graphics/DisownBlitter"],
    -474: ["exec/WaitIO"], -480: ["exec/AbortIO"],
    -552: ["exec/OpenLibrary"],
    -882: ["graphics/LoadRGB32"],
    -36 - 0: ["dos/Close"],
}


def main():
    for p in sys.argv[1:]:
        d = open(p, "rb").read()
        c = collections.Counter()
        for m in re.finditer(b"\x4e\xae", d):
            o = m.start()
            if o + 4 > len(d):
                continue
            disp = struct.unpack_from(">h", d, o + 2)[0]
            if disp < 0:
                c[disp] += 1
        print("=== %s : %d jsr d16(a6) sites, %d distinct displacements ==="
              % (p, sum(c.values()), len(c)))
        for disp in sorted(c, reverse=True):
            names = LVO.get(disp)
            tag = " | ".join(names) if names else "-"
            print("   %5d (0x%04X) x%-4d %s" % (disp, disp & 0xFFFF, c[disp], tag))
        print()


if __name__ == "__main__":
    main()
