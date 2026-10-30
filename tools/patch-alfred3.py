#!/usr/bin/env python3
"""Add Alfred Chicken to the disc list, and correct the two stale phrases in the
intro that still say "one of the seventeen" and "one of the twelve".

Anchors asserted unique.
"""
import io

P = 'cd32-platform-notes.md'
s = io.open(P, encoding='utf-8').read()
edits = []


def sub(old, new, why):
    global s
    n = s.count(old)
    assert n == 1, "anchor %r appears %d times" % (why, n)
    s = s.replace(old, new, 1)
    edits.append(why)


sub("One of the seventeen is the **CDTV release",
    "One of the eighteen is the **CDTV release",
    "intro: one of the seventeen -> eighteen")

sub("And one of the twelve is a **CD32 title whose A1200 floppy release can be\ncompared with it block for block**",
    "And one of the eighteen is a **CD32 title whose A1200 floppy release can be\ncompared with it block for block**",
    "intro: one of the twelve -> eighteen (floppy control)")

sub("And one of the twelve is the **second disc here from a label that already had\none**",
    "And one of the eighteen is the **second disc here from a label that already\nhad one**",
    "intro: one of the twelve -> eighteen (same label)")

# the intro's list of "as unlike each other as CD32 titles can be" gains this disc
sub("""whose whole volume is **772 sectors**, one that leaves **95 % of its volume
empty in front of the files**, and one whose whole game is **2.25 MB with
nothing packed** — which makes the handful of things they agree on worth more
than the count suggests.""",
    """whose whole volume is **772 sectors**, one that leaves **95 % of its volume
empty in front of the files**, one whose whole game is **2.25 MB with
nothing packed**, and one that is **99 % Red Book audio with a 918-sector data
track** — which makes the handful of things they agree on worth more
than the count suggests.""",
    "intro: unlikeness list gains the 99 % audio disc")

# and the paragraph about what the newest disc contributed
sub("""negative**. See section 4.

## Discs this rests on""",
    """negative**. See section 4.

And the eighteenth is the **first disc here read from the physical medium
instead of from an image file**, which is the most productive single thing to
happen to this document since the two Prey masters. It settled three things no
image could: the thirteen-zero `CATALOG` four discs carry is **on the disc**, in
the subchannel, not lost by a dumper; the 32..232-sector overrun past the
declared volume is **cut into the glass master**, and is padding up to the next
track's pregap; and `MODE1/2048`, which every cue in this set asserts and no disc
had ever been checked for, is **verified** by descrambling raw sectors. It also
supplied per-track **ISRC** and real pregaps, fields the set had never read, and
a dating instrument it had no step for — **expanded RCS keywords**. See step 40
and open items 38–40.

## Discs this rests on""",
    "intro: the eighteenth disc paragraph")

ROW = ("| [Alfred Chicken](https://github.com/vs-sr-dev/cd32-alfredchicken-doc) | "
       "**1993** | Twilight for Mindscape, UK — the **first disc here read from "
       "physical media rather than from an image file**, and the one that "
       "settled what a file cannot. Ten tracks: a **918-sector** data track and "
       "**nine Red Book tracks**, so **99.02 % of the pressed disc is audio** "
       "and the game is 1.26 MB — **43.9 % below Guardian's floor**, which had "
       "stood for seventeen discs. The MCN read from **subchannel Q** is "
       "`0000000000000` with MCVAL set, so the thirteen zeros four discs carry "
       "are the master and not the dumper; the volume declares **691** sectors "
       "and the disc physically holds **918** of valid MODE1 — every one "
       "verified on sync, header address and EDC — with the extra **227** "
       "stopping exactly where track 2's pregap begins, which is what the "
       "32..232 overrun has always been. `MODE1/2048` **verified** by "
       "descrambling, ISRC **absent on all ten tracks**, and the nine audio "
       "tracks **perfectly contiguous** with one 150-sector pregap on the whole "
       "disc. 30 files, **RNC ProPack 1** validated 11 of 11 by CRC at depth 0, "
       "expansion **1.297x, the lowest of eleven**. The preparer is "
       "**`Abersoft`, the second company** in that field, with a 32-sector run — "
       "and since Mindscape's other disc, Liberation, is `D J Pocock` with 232, "
       "the field **follows the work, not the label**. Tiles derived three ways "
       "as **16x16x4**; **zero stored copper lists** but the screen mode "
       "hardcoded as `BPLCON0` immediates; **no text at all** — a fifth string "
       "model — with the game's own title existing only as a **320x184 "
       "picture**. And `intro`, built from source checked out **fourteen months "
       "before** `alfred`, ships a **working Amiga hardware debugger**: 47 "
       "custom-register description strings from Commodore's `hardware/custom.i` "
       "and `copdis`, a copper list disassembler |\n")

anchor = ("| [Myth: History in the Making](https://github.com/vs-sr-dev/cd32-myth-doc) | "
          "**1992/1993** |")
i = s.index(anchor)
j = s.index('\n', i) + 1
s = s[:j] + ROW + s[j:]
edits.append("disc list: Alfred Chicken row appended")

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print("patched %s" % P)
for e in edits:
    print("  - %s" % e)
