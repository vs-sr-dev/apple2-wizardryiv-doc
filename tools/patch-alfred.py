#!/usr/bin/env python3
"""In-place corrections to cd32-platform-notes.md for the eighteenth disc.

Every count below was RE-DERIVED from the section 10 baseline table with
tools/recount.py, not incremented.  That is the Myth lesson: the `.TM` section
was still saying "ten discs with the Commodore banner" four discs after it
stopped being true, and a number two discs stale is indistinguishable from a
number that was measured.

What the table actually says, with the Alfred Chicken column in place:

  18 discs, of which 17 are CD32-era (Prey CDTV is the CDTV one)
  .TM three SHA-1s identical ......... 16  (all but Speris, among CD32-era)
  preparer field = D J Pocock .........  5  -> 232-sector run, 5 of 5
  preparer field = anything else ...... 13  -> 32-sector run, 13 of 13
  Akiko driven directly ...............  3  (Dragonstone, Universe, Myth)
  compression involves RNC ............  7  (+ Alfred Chicken)

Every anchor is asserted unique; if one is not, nothing is written.
"""
import io

P = 'cd32-platform-notes.md'
s = io.open(P, encoding='utf-8').read()
edits = []


def sub(old, new, why):
    global s
    n = s.count(old)
    assert n == 1, "anchor %r appears %d times: %.70s" % (why, n, old)
    s = s.replace(old, new, 1)
    edits.append(why)


# ---- 1. the headline disc count
sub("It currently rests on **seventeen discs**, so much of",
    "It currently rests on **eighteen discs**, so much of",
    "headline disc count 17 -> 18")

# ---- 2. the .TM tally, three places, re-derived as 16 of 17 CD32-era
sub("### On CD32-era discs: fifteen discs, the same bytes",
    "### On CD32-era discs: sixteen discs, the same bytes",
    ".TM heading 15 -> 16")

sub("**All three SHA-1s match, byte for byte, on fifteen of the sixteen CD32-era\ndiscs**",
    "**All three SHA-1s match, byte for byte, on sixteen of the seventeen CD32-era\ndiscs**",
    ".TM 15/16 -> 16/17")

sub("The score is now **fifteen discs with the Commodore banner\nand one with the CDTV driver**",
    "The score is now **sixteen discs with the Commodore banner\nand one with the CDTV driver**",
    ".TM score 15 -> 16")

sub("| `.TM` block | **the mastering tool** | **fifteen discs, eleven labels, identical bytes** |",
    "| `.TM` block | **the mastering tool** | **sixteen discs, twelve labels, identical bytes** |",
    ".TM summary row 15 -> 16")

sub("| `.TM` block | the common 2,048 B | identical | **identical** | matches, fifteen discs have it |",
    "| `.TM` block | the common 2,048 B | identical | **identical** | matches, sixteen discs have it |",
    ".TM comparison row 15 -> 16")

# ---- 3. the preparer / trailing-run correlation, re-derived as 5 of 5 vs 13 of 13
sub("`Pocock` 232 on 5 of 5; everyone else 32 on **12 of 12**. "
    "**[Myth]'s field names a company with a phone and fax number**, so "
    "\"operator\" needs widening to include a contractor",
    "`Pocock` 232 on 5 of 5; everyone else 32 on **13 of 13**. "
    "**[Myth]'s field names a company with a phone and fax number, and "
    "[Alfred Chicken]'s names a second one, `Abersoft`** — so \"operator\" "
    "needs widening to include a contractor, and two contractors in eighteen "
    "discs is no longer a single anomaly. **[Alfred Chicken] is also the first "
    "same-publisher test of the correlation and it survives**: Mindscape's "
    "other disc, [Liberation], *is* Pocock with 232, and this one is Abersoft "
    "with 32 — so the field follows the work, not the label",
    "preparer correlation 12 of 12 -> 13 of 13, plus the same-label test")

sub("field this document has read on sixteen discs as \"the operator\". Trailing run",
    "field this document has read on seventeen discs as \"the operator\". Trailing run",
    "preparer read-on-N-discs 16 -> 17")

# ---- 4. the RNC tally, re-derived as 7 of 18
sub("Computing wrote **RNC ProPack**, which is on Dragonstone, Banshee, HeroQuest II,\n"
    "Universe and Gunship 2000, with Liberation's codec wearing its magic — six discs\n"
    "of seventeen. The firm that wrote it cut the master of a seventh, **and that\n"
    "seventh does not use it**: [Myth] packs with Bytekiller, written by the game's",
    "Computing wrote **RNC ProPack**, which is on Dragonstone, Banshee, HeroQuest II,\n"
    "Universe, Gunship 2000 and [Alfred Chicken], with Liberation's codec wearing its\n"
    "magic — seven discs of eighteen. The firm that wrote it cut the master of an\n"
    "eighth, **and that eighth does not use it**: [Myth] packs with Bytekiller, "
    "written by the game's",
    "RNC tally 6 of 17 -> 7 of 18")

sub("wrote **RNC ProPack**, which is on six of the seventeen discs here — and the\n"
    "    master it cut **does not use it**, packing with Bytekiller written by the",
    "wrote **RNC ProPack**, which is on seven of the eighteen discs here — and the\n"
    "    master it cut **does not use it**, packing with Bytekiller written by the",
    "RNC open-question tally 6/17 -> 7/18")

# ---- 5. the list-of-discs denominator used by the census section
sub("here against the seventeen discs in the list at the top of this document, and",
    "here against the eighteen discs in the list at the top of this document, and",
    "census denominator 17 -> 18")

sub("Seventeen discs, and they bracket the format rather than agreeing on it. Prey CD32",
    "Eighteen discs, and they bracket the format rather than agreeing on it. Prey CD32",
    "format bracket 17 -> 18")

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print("patched %s" % P)
for e in edits:
    print("  - %s" % e)
