#!/usr/bin/env python3
"""Second pass on the James Pond 2 update: re-derive the counts the prose
quotes, instead of leaving them one disc stale.

Every anchor is asserted unique before anything is written. Nothing is
incremented by hand — each new figure below was read out of
`tools/recount.py` or out of the section 10 table directly.

Usage: python tools/patch-jamespond2b.py cd32-platform-notes.md
"""
import sys, io

EDITS = []


def edit(name, old, new):
    EDITS.append((name, old, new))


edit("intro: one of the nineteen (CDTV control)",
"""One of the eighteen is the **CDTV release of a title whose CD32 release is also
here**,""",
"""One of the nineteen is the **CDTV release of a title whose CD32 release is also
here**,""")

edit("intro: one of the nineteen (floppy control)",
"""And one of the eighteen is a **CD32 title whose A1200 floppy release can be
compared with it block for block**,""",
"""And one of the nineteen is a **CD32 title whose A1200 floppy release can be
compared with it block for block**,""")

edit("intro: one of the nineteen (same label)",
"""And one of the eighteen is the **second disc here from a label that already
had one**,""",
"""And one of the nineteen is the **second disc here from a label that already
had one**,""")

edit("section 4: denominator",
"""here against the eighteen discs in the list at the top of this document, and""",
"""here against the nineteen discs in the list at the top of this document, and""")

edit("section 10: opening sentence",
"""Eighteen discs, and they bracket the format rather than agreeing on it. Prey CD32""",
"""Nineteen discs, and they bracket the format rather than agreeing on it. Prey CD32""")

edit("open item 14 table cell: the preparer/trailing-run row",
"""`Pocock` 232 on 5 of 5; everyone else 32 on **13 of 13**. **[Myth]'s field names a company with a phone and fax number, and [Alfred Chicken]'s names a second one, `Abersoft`** — so "operator" needs widening to include a contractor, and two contractors in eighteen discs is no longer a single anomaly. **[Alfred Chicken] is also the first same-publisher test of the correlation and it survives**: Mindscape's other disc, [Liberation], *is* Pocock with 232, and this one is Abersoft with 32 — so the field follows the work, not the label |""",
"""`Pocock` 232 on 5 of 5; everyone else 32 on **14 of 14**. **[Myth]'s field names a company with a phone and fax number, and [Alfred Chicken]'s names a second one, `Abersoft`** — so "operator" needs widening to include a contractor, and two contractors in nineteen discs is no longer a single anomaly. **[Alfred Chicken] is also the first same-publisher test of the correlation and it survives**: Mindscape's other disc, [Liberation], *is* Pocock with 232, and this one is Abersoft with 32 — so the field follows the work, not the label. **And [James Pond 2] closes the "who is it?" half of the question**: preparer `Dean Ashton`, trailing run 32, and the man is on the disc in the first person — a signed, dated comment in the boot script — *and* is the game's own conversion programmer by both credit screens. So the box holds a fifth kind of owner, **the studio's own programmer**, and it says nothing about role: it says who was at the keyboard |""")

edit("open item: seventeen discs -> nineteen",
"""field this document has read on seventeen discs as "the operator". Trailing run""",
"""field this document has read on nineteen discs as "the operator". Trailing run""")

edit("open item: RNC denominator",
"""wrote **RNC ProPack**, which is on seven of the eighteen discs here — and the""",
"""wrote **RNC ProPack**, which is on seven of the nineteen discs here — and the""")


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    path = sys.argv[1]
    text = io.open(path, encoding='utf-8').read()

    bad = [(n, text.count(o)) for n, o, _ in EDITS if text.count(o) != 1]
    if bad:
        for name, n in bad:
            print("  anchor %-48s occurs %d times (need exactly 1)" % (name, n))
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
