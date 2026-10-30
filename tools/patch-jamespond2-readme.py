#!/usr/bin/env python3
"""Fold the James Pond 2 disc into the checklist repository's own README.

Anchors asserted unique before anything is written.

Usage: python tools/patch-jamespond2-readme.py README.md
"""
import sys, io

EDITS = []


def edit(name, old, new):
    EDITS.append((name, old, new))


edit("section 10 row: column count and the floor",
"""| 10 | Baselines, disc by disc, side by side — **eighteen columns**,""",
"""| 10 | Baselines, disc by disc, side by side — **nineteen columns**,""")

edit("section 10 row: the floor moved twice",
"""The floor moved for the first time in eighteen discs |""",
"""The floor moved for the first time in eighteen discs — **and then again on the very next disc**, which is what shows the floor was measuring "titles that keep their content in the file system" rather than how small a game can be |""")

edit("section 5 row: a reason not to pack",
"""and getting the decruncher out of the loader |""",
"""getting the decruncher out of the loader, and **reading the hunk table's memory flags before concluding anything about why a disc is not packed** — a game holding 1.19 MB of a 2 MB chip budget has no room for a decrunch buffer, which is a mechanism where four earlier "nothing packed" discs had only an absence |""")

edit("section 8 row: the third TOC-free disc",
"""because a disc can play two of its five tracks""",
"""because a disc can play two of its five tracks — while a **third** disc plays **all seven** of its own and never reads the TOC at all, its whole soundtrack map being byte 11 of an 86-record level table with **bit 7 choosing Red Book or Paula**, and its watchdog a bare 250-frame countdown with no query""")

edit("section 9 row: the sixth string model",
"""and a disc that stores a text **generator** and shipped its source with a note to translators in it |""",
"""a disc that stores a text **generator** and shipped its source with a note to translators in it, and a **sixth string model**: a complete three-language manual with **no characters in it at all**, 115 IFF pictures of typeset text, where the localisation has to be measured in pixels — one shared palette, one page byte-identical across three languages, a Deluxe Paint chunk on 17 pages and none in German — and where **only a render can say what language it is** |""")

edit("discs table: add the row",
"""| [Alfred Chicken](https://github.com/vs-sr-dev/cd32-alfredchicken-doc) | **1993** |""",
"""| [James Pond 2: Codename RoboCod](https://github.com/vs-sr-dev/cd32-jamespond2-doc) | **1993** | Millennium Interactive, UK — a 1991 two-floppy platformer on a 195 MiB data track, and the first disc here that is **three products on one master**: the game, a 2 m 43 s CDXL cartoon and a three-language electronic book, dispatched by a boot script that is a shell-level main loop. **65.55 % of the volume is a hole of exactly 128.000000 MiB** — 65,536 sectors, 2^16, verified zero — *and* **93.90 % of the file bytes are CDXL video**, so the two leading hypotheses for a large data track are true at once for the first time; with the CDXL padding the data track is **69.75 % zero**. The **game is 1,033,508 bytes on disc / 1,258,076 resident**, 18.1 % below Alfred Chicken's floor. Nothing packed, and for a reason: **all three hunks are `CHIP`**, 1.19 MB of a 2 MB budget. **All seven Red Book tracks reachable** from an 86-record table where bit 7 of the music id picks Red Book or Paula, with **no TOC read anywhere**. Five bitplanes with a **24-bit AGA `LOCT` palette**, and an unreachable message in which the programmer apologises for the plane count and says he left no debug symbols — the copper list and the hunk chain confirm both. A **manual containing no characters**, measured in pixels. And the preparer field, `Dean Ashton`, is the **first whose owner identifies himself on the disc** — a signed 44-line development diary in the boot script whose three dates the filesystem confirms |
| [Alfred Chicken](https://github.com/vs-sr-dev/cd32-alfredchicken-doc) | **1993** |""")

edit("closing paragraph: the range",
"""These are about as unlike each other as Amiga CD titles can be — 1992 to 1996,
**0.23 %** of a disc to 89.4 % of one, **five files to 1,453**, a **1.6 MB** data
track to a **499 MB** one, two whose data tracks are **95 % zero**, one whose
whole game is **2.25 MB with nothing packed**, and one that is **three floppy
disks pressed whole** — which""",
"""These are about as unlike each other as Amiga CD titles can be — 1992 to 1996,
**0.23 %** of a disc to 89.4 % of one, **five files to 1,453**, a **1.6 MB** data
track to a **499 MB** one, **three** whose data tracks are 65–95 % zero, one whose
whole game is **2.25 MB with nothing packed**, one that is **three floppy
disks pressed whole**, and one that is **a game, a cartoon and a picture book on
one master with the game at 1.47 % of the bytes** — which""")


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    path = sys.argv[1]
    text = io.open(path, encoding='utf-8').read()
    bad = [(n, text.count(o)) for n, o, _ in EDITS if text.count(o) != 1]
    if bad:
        for name, n in bad:
            print("  anchor %-45s occurs %d times (need exactly 1)" % (name, n))
        raise SystemExit("REFUSING: %d of %d anchors not unique; nothing written"
                         % (len(bad), len(EDITS)))
    print("all %d anchors unique" % len(EDITS))
    before = len(text)
    for name, old, new in EDITS:
        text = text.replace(old, new, 1)
        print("  applied %s" % name)
    io.open(path, 'w', encoding='utf-8', newline='\n').write(text)
    print("OK: %d -> %d bytes (%+d)" % (before, len(text), len(text) - before))


if __name__ == '__main__':
    main()
