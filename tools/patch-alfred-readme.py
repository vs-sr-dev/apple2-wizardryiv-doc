#!/usr/bin/env python3
"""Update the checklist's own README for the eighteenth disc.

Anchors asserted unique.
"""
import io

P = 'README.md'
s = io.open(P, encoding='utf-8').read()
edits = []


def sub(old, new, why):
    global s
    n = s.count(old)
    assert n == 1, "anchor %r appears %d times" % (why, n)
    s = s.replace(old, new, 1)
    edits.append(why)


sub("| 10 | Baselines, disc by disc, side by side — **seventeen columns**, and the "
    "size band now stated as an on-disc measurement after a same-label pair pinned "
    "down which of three numbers it was ever measuring |",
    "| 10 | Baselines, disc by disc, side by side — **eighteen columns**, and the "
    "size band now stated as an on-disc measurement after a same-label pair pinned "
    "down which of three numbers it was ever measuring. The floor moved for the "
    "first time in eighteen discs |",
    "section 10: seventeen -> eighteen columns")

sub("| 11 | The order of work that worked (**39 steps**)",
    "| 11 | The order of work that worked (**40 steps**)",
    "section 11: 39 -> 40 steps")

sub("and parse the one file that is most of the disc with a resynchroniser |",
    "parse the one file that is most of the disc with a resynchroniser, and — "
    "if the disc is physical — **read it twice by two different paths, cross-check "
    "the overlap, and make every sector prove its own identity from its descrambled "
    "header** |",
    "section 11: step 40 summary")

sub("| 8 | Red Book **and whether anything plays it**",
    "| 8 | Red Book **and whether anything plays it** — and on a physical disc the "
    "denominator is finally measured rather than inherited from someone's cue: "
    "**MCN and per-track ISRC from subchannel Q**, pre-emphasis and channel-count "
    "bits from CONTROL, and real pregaps",
    "section 8: subchannel fields")

ROW = ("| [Alfred Chicken](https://github.com/vs-sr-dev/cd32-alfredchicken-doc) | "
       "**1993** | Twilight for Mindscape — the **first disc here read from the "
       "plastic rather than from an image file**, and it settled three things no "
       "image could. The `0000000000000` `CATALOG` that four discs carry is **on "
       "the disc**, read from subchannel Q with MCVAL set, so it is the mastering "
       "and not a dumper losing a real EAN. The **32..232-sector overrun** past the "
       "declared volume is **cut into the glass master**: the volume declares 691 "
       "sectors, the disc holds **918** of valid MODE1 — every one verified on sync, "
       "header address and EDC — and the extra 227 stop exactly where the next "
       "track's pregap begins, so the run is padded up to the following track. And "
       "**`MODE1/2048` is verified** by descrambling raw sectors, which no disc in "
       "this set had ever been checked for. Ten tracks, **99.02 % of the pressed "
       "disc audio**, and a 1.26 MB game that **breaks Guardian's floor by 43.9 %** "
       "after it had stood for seventeen discs. Preparer **`Abersoft`, the second "
       "company** in that field — and since Mindscape's other disc is `D J Pocock`, "
       "the field **follows the work, not the label**. Its `intro`, built from "
       "source checked out **fourteen months before** the game, ships a **working "
       "Amiga hardware debugger** |\n")

anchor = ("| [Myth: History in the Making](https://github.com/vs-sr-dev/cd32-myth-doc) | "
          "**1992/1993** |")
i = s.index(anchor)
j = s.rindex('\n', 0, i) + 1
s = s[:j] + ROW + s[j:]
edits.append("README disc list: Alfred Chicken row prepended")

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print("patched %s" % P)
for e in edits:
    print("  - %s" % e)
