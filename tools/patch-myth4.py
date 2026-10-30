# -*- coding: utf-8 -*-
"""Fourth [Myth] patch: the checklist repository's own README.

Usage: python3 tools/patch-myth4.py README.md
"""
import io, sys

EDITS = [
 ("""| Disc | Master | What it is |
|---|---|---|
| [Superfrog](https://github.com/vs-sr-dev/cd32-superfrog-doc) |""",
  """| Disc | Master | What it is |
|---|---|---|
| [Myth: History in the Making](https://github.com/vs-sr-dev/cd32-myth-doc) | **1992/1993** | System 3 Arcade Software, UK — developer and publisher in one, and **the disc that is its own floppy release**: five files, two directories, no audio track, and three of the five files are **901,120 bytes each — one 880 KiB Amiga floppy disk, exactly**. **94.86 % of the declared volume is a hole of exactly 50.000000 MiB**, leaving a 2.72 MB game. An 18 KB CD shim with **zero relocations**, four media back ends, a **hand-written `LoadSeg`** and an **Akiko** CD driver; **Bytekiller under the magic `DAVE`**, the programmer's first name; **expansion 1.369x, the lowest of ten**; a preparer field naming **a company** — the author of RNC ProPack, on a master that does not use it; and a PVD date of 1992-12-21 that **the disc's own `.TM` block falsifies** |
| [Superfrog](https://github.com/vs-sr-dev/cd32-superfrog-doc) |"""),

 ("""| 11 | The order of work that worked (**37 steps**)""",
  """| 11 | The order of work that worked (**39 steps**)"""),

 ("""These are about as unlike each other as Amiga CD titles can be — 1992 to 1996,
**0.23 %** of a disc to 89.4 % of one, 34 files to 1,453, a **1.6 MB** data
track to a **499 MB** one, one whose data track is **95 % zero**, and one whose
whole game is **2.25 MB with nothing packed** — which""",
  """These are about as unlike each other as Amiga CD titles can be — 1992 to 1996,
**0.23 %** of a disc to 89.4 % of one, **five files to 1,453**, a **1.6 MB** data
track to a **499 MB** one, two whose data tracks are **95 % zero**, one whose
whole game is **2.25 MB with nothing packed**, and one that is **three floppy
disks pressed whole** — which"""),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'README.md'
    s = io.open(path, encoding='utf-8').read()
    n = len(s)
    for i, (a, b) in enumerate(EDITS):
        c = s.count(a)
        if c != 1:
            raise SystemExit("EDIT %d: anchor found %d times:\n  %r" % (i, c, a[:80]))
        s = s.replace(a, b, 1)
        print("edit %d ok" % i)
    io.open(path, 'w', encoding='utf-8', newline='\n').write(s)
    print("wrote %s: %d -> %d" % (path, n, len(s)))


if __name__ == '__main__':
    main()
