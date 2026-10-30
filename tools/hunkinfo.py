#!/usr/bin/env python3
"""Walk an AmigaDOS hunk file and report its structure and relocation density.

Step 36 of the checklist: a file beginning 0x000003F3 need not be a program.
The tell is the ratio of relocations to code bytes.  This prints, per hunk,
the type, the declared size, whether the memory flags ask for CHIP or FAST,
and the number of relocation entries, then the whole-file ratio.

Usage: python3 tools/hunkinfo.py <file>... [--list-relocs]
"""
import sys, struct

HT = {0x3E7: "UNIT", 0x3E8: "NAME", 0x3E9: "CODE", 0x3EA: "DATA", 0x3EB: "BSS",
      0x3EC: "RELOC32", 0x3ED: "RELOC16", 0x3EE: "RELOC8", 0x3EF: "EXT",
      0x3F0: "SYMBOL", 0x3F1: "DEBUG", 0x3F2: "END", 0x3F3: "HEADER",
      0x3F7: "BREAK", 0x3F8: "DREL32", 0x3F9: "DREL16", 0x3FA: "DREL8",
      0x3FB: "LIB", 0x3FC: "INDEX", 0x3E5: "BSS?", 0x3F5: "RELOC32SHORT"}
MEMF = {0: "any", 1: "CHIP", 2: "FAST", 3: "follows"}


def walk(d, name, listr):
    if len(d) < 8 or struct.unpack_from(">I", d, 0)[0] != 0x3F3:
        print("%s: not a hunk file (first longword %08x)" %
              (name, struct.unpack_from(">I", d, 0)[0] if len(d) >= 4 else 0))
        return
    p = 4
    # resident library name list, normally empty
    names = []
    while True:
        n = struct.unpack_from(">I", d, p)[0]
        p += 4
        if n == 0:
            break
        names.append(d[p:p + n * 4].rstrip(b"\0").decode("latin1", "replace"))
        p += n * 4
    tabsize, first, last = struct.unpack_from(">III", d, p)
    p += 12
    sizes = []
    for i in range(last - first + 1):
        v = struct.unpack_from(">I", d, p)[0]
        p += 4
        sizes.append((v & 0x3FFFFFFF, MEMF[(v >> 30) & 3]))
    print("=== %s (%d bytes) ===" % (name, len(d)))
    if names:
        print("  resident library names: %s" % names)
    print("  hunk table: size=%d first=%d last=%d" % (tabsize, first, last))
    for i, (s, m) in enumerate(sizes):
        print("    hunk %d: %d longwords (%d bytes) mem=%s" % (i, s, s * 4, m))
    idx = 0
    totreloc = 0
    codebytes = 0
    relocs_by_hunk = {}
    while p < len(d) - 3:
        t = struct.unpack_from(">I", d, p)[0]
        tt = t & 0x3FFFFFFF
        p += 4
        nm = HT.get(tt, "?%x" % tt)
        if tt in (0x3E9, 0x3EA):
            n = struct.unpack_from(">I", d, p)[0]
            p += 4
            print("  hunk %d %-8s %d bytes at file offset %d" % (idx, nm, n * 4, p))
            if tt == 0x3E9:
                codebytes += n * 4
            p += n * 4
        elif tt == 0x3EB:
            n = struct.unpack_from(">I", d, p)[0]
            p += 4
            print("  hunk %d %-8s %d bytes (no file image)" % (idx, nm, n * 4))
        elif tt in (0x3EC,):
            cnt = 0
            while True:
                n = struct.unpack_from(">I", d, p)[0]
                p += 4
                if n == 0:
                    break
                h = struct.unpack_from(">I", d, p)[0]
                p += 4
                offs = list(struct.unpack_from(">%dI" % n, d, p))
                p += 4 * n
                cnt += n
                relocs_by_hunk.setdefault(idx, []).extend(offs)
                if listr:
                    print("    RELOC32 -> hunk %d: %d entries: %s" %
                          (h, n, ", ".join("0x%x" % o for o in offs[:2000])))
            print("  hunk %d %-8s %d entries" % (idx, nm, cnt))
            totreloc += cnt
        elif tt == 0x3F5:
            n = struct.unpack_from(">H", d, p)[0]
            cnt = 0
            while n:
                p += 2
                h = struct.unpack_from(">H", d, p)[0]
                p += 2
                offs = list(struct.unpack_from(">%dH" % n, d, p))
                p += 2 * n
                cnt += n
                relocs_by_hunk.setdefault(idx, []).extend(offs)
                if p % 4:
                    p += 2
                n = struct.unpack_from(">H", d, p)[0]
            p += 2
            if p % 4:
                p += 2
            print("  hunk %d %-8s %d entries" % (idx, nm, cnt))
            totreloc += cnt
        elif tt == 0x3F0:
            while True:
                n = struct.unpack_from(">I", d, p)[0]
                p += 4
                if n == 0:
                    break
                p += n * 4 + 4
            print("  hunk %d %-8s" % (idx, nm))
        elif tt == 0x3F1:
            n = struct.unpack_from(">I", d, p)[0]
            p += 4 + n * 4
            print("  hunk %d %-8s %d bytes" % (idx, nm, n * 4))
        elif tt == 0x3F2:
            idx += 1
            continue
        else:
            print("  hunk %d unhandled %s at %d, stopping" % (idx, nm, p - 4))
            break
    print("  TOTAL relocations: %d over %d code bytes -> %.2f per KB of code" %
          (totreloc, codebytes, 1024.0 * totreloc / codebytes if codebytes else 0))
    for h, offs in sorted(relocs_by_hunk.items()):
        if offs:
            print("  hunk %d relocs span 0x%x..0x%x (%d entries)" %
                  (h, min(offs), max(offs), len(offs)))
    print()


def main():
    listr = "--list-relocs" in sys.argv
    for f in sys.argv[1:]:
        if f.startswith("--"):
            continue
        walk(open(f, "rb").read(), f, listr)


main()
