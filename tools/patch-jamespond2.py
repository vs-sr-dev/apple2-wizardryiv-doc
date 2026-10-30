#!/usr/bin/env python3
"""Fold the James Pond 2 (CD32) findings into the shared checklist.

Same contract as every patch script in this directory: every anchor is
asserted UNIQUE before anything is written, and if any anchor is missing or
ambiguous the script writes nothing at all and says which one failed.

Usage: python tools/patch-jamespond2.py cd32-platform-notes.md
"""
import sys, io

EDITS = []


def edit(name, old, new):
    EDITS.append((name, old, new))


# ---------------------------------------------------------------- header
edit("intro: disc count",
"""next and added to by each. It currently rests on **eighteen discs**, so much of
it is still marked with the title it came from: treat it as a list of things to
*test*, not a list of things that are true of the format.""",
"""next and added to by each. It currently rests on **nineteen discs**, so much of
it is still marked with the title it came from: treat it as a list of things to
*test*, not a list of things that are true of the format.""")

edit("intro: the nineteenth",
"""And the eighteenth is the **first disc here read from the physical medium
instead of from an image file**,""",
"""And the nineteenth is the first disc here that is **three products on one
master** — a game, a 2 m 43 s cartoon and a three-language electronic book,
offered as three branches of a shell script — which is what finally separates
"the disc" from "the title" in section 10, and moves the size band's floor for
the second time in two discs. It is also the disc where the **data-preparer
field stops being anonymous**: the man named in it wrote the boot script, signed
it in the first person, dated it, and the directory confirms all three of his
dates. See sections 1, 8, 9 and 10, and open item 41.

And the eighteenth is the **first disc here read from the physical medium
instead of from an image file**,""")

edit("disc list: add the nineteenth row",
"""| [Alfred Chicken](https://github.com/vs-sr-dev/cd32-alfredchicken-doc) | **1993** | Twilight for Mindscape, UK — the **first di""",
"""| [James Pond 2: Codename RoboCod](https://github.com/vs-sr-dev/cd32-jamespond2-doc) | **1993** | Millennium Interactive, UK — a 1991 two-floppy platform game on a 195 MiB data track, and **three products on one master**: the game, a 2 m 43 s CDXL cartoon and a three-language electronic book, dispatched by a shell script that is a main loop. **65.55 % of the declared volume is a hole of exactly 128.000000 MiB** (65,536 sectors, 2^16, verified zero) and **93.90 % of the file bytes are CDXL video**, so two of the four hypotheses for a large data track are true at once for the first time. The **game is 1,033,508 bytes on disc / 1,258,076 resident — 18.1 % below Alfred Chicken's floor**, which had stood for one disc. Nothing packed, with a mechanism: all three hunks are `CHIP`, 1,185,496 of a 2 MB budget. **All seven Red Book tracks reachable** from byte 11 of an 86-record level table where bit 7 of the music id chooses Red Book or Paula, with the TOC never read. Five bitplanes with a **24-bit `LOCT` palette**, and an unreachable message in which the programmer apologises for the plane count and claims he left no debug symbols — **both verified**. A **three-language manual containing no characters at all**, 115 IFF ILBM pages measured in pixels. Preparer `Dean Ashton`, a **sixth name**, trailing run 32 — and the **first preparer identifiable from the disc in his own words**, in a signed 44-line comment whose three dates the filesystem confirms |
| [Alfred Chicken](https://github.com/vs-sr-dev/cd32-alfredchicken-doc) | **1993** | Twilight for Mindscape, UK — the **first di""")

# ---------------------------------------------------- section 1: preparer
edit("section 1: preparer shape table",
"""```
preparer shape                       discs   trailing run
`D J Pocock`                             5   232, every time
empty name, tool signature only          5   32 (on the four cut with ISOCD)
six other named operators                6   32
a COMPANY, with a phone and fax number   1   32          <- [Myth]
```""",
"""```
preparer shape                       discs   trailing run
`D J Pocock`                             5   232, every time
empty name, tool signature only          5   32 (on the four cut with ISOCD)
seven other named operators              7   32
a COMPANY, with a phone and fax number   2   32   <- [Myth], [Alfred Chicken]
```""")

edit("section 1: a fifth thing the field can record",
"""Two things follow.

**The box does not always hold a person, so "the operator" is too narrow a
label for what it records.**""",
"""**AND THE NINETEENTH DISC ANSWERS THE QUESTION THE OTHER SIX COULD NOT.**
[James Pond 2] is `Dean Ashton - ISOCD 1.04 by Pantaray, Inc. USA -`, a
**seventh named operator**, trailing run **32**, so *not-Pocock leaves 32* is
**14 of 14**. That part is routine. What is not routine is that this is the
**first disc where the person in that field is identifiable from the disc, in
the first person, at length**. Its `s/Startup-Sequence` is 3,922 bytes of which
twenty-one are the launcher; the rest is a comment signed

```
; This funky startup sequence hurriedly put together at 1:30am 14.07.93
; by the master of the kludged code, Dean Ashton.
```

and he is not the mastering operator in any separable sense — the same name is
on the game's own credit screen as `AGA CONVERSION BY DEAN ASHTON`, on a hidden
string in the executable as `Dean Ashton, programmer, June 1993`, and in the
boot script's credit list as the author of the whole A1200/CD32 conversion.

So the field has now held: an anonymous tool signature, a bureau operator
appearing on five unrelated masters, two contractor firms, a menu author who
demonstrably did not write the game ([Superfrog]), and now **the studio's own
conversion programmer, who cut the master himself**. That is five distinct
owner-types on nineteen discs, and it is why "the operator" was always going to
be too narrow: the box records *whoever ran the tool*, and on a small 1993 team
that is whoever was awake.

**Two consequences worth carrying.** First, **when a named preparer turns up,
grep the boot script for the name before anything else** — it is free, and on
this disc it is where the answer was. Second, this disc is the counter-example
to [Superfrog]'s: there, the preparer wrote the menu and demonstrably not the
game; here, the preparer wrote the conversion, the boot script and the CDXL
conversion. **The field says nothing about role. It says who was at the
keyboard.**

Two things follow.

**The box does not always hold a person, so "the operator" is too narrow a
label for what it records.**""")

# ---------------------------------------------------- section 2: .TM count
edit("section 2: .TM disc count",
"""**All three SHA-1s match, byte for byte, on sixteen of the seventeen CD32-era
discs**""",
"""**All three SHA-1s match, byte for byte, on seventeen of the eighteen CD32-era
discs**""")

# ---------------------------------------------------- section 5: compression
edit("section 5: a fifth disc with nothing packed",
"""## 6. Executables and overlays""",
"""### AND A DISC CAN HAVE A REASON NOT TO PACK, WHICH IS BETTER THAN A CORRELATION

Five discs of nineteen have nothing packed at all — both Prey masters, Marvin,
[Guardian] and [James Pond 2]. On the first four the finding is a negative and
stops there. On the fifth there is a **mechanism in the hunk table**, and it is
worth a step of its own because it costs one command.

```
python3 tools/hunkinfo.py extract/RoboCod
  hunk 0: 81158 longwords (324632 bytes) mem=CHIP
  hunk 1: 153403 longwords (613612 bytes) mem=CHIP
  hunk 2: 61813 longwords (247252 bytes) mem=CHIP
```

**All three hunks are `MEMF_CHIP`** — 1,185,496 bytes of the CD32's 2 MB of
chip RAM, for one program, before the game allocates a single buffer. A
whole-file decruncher needs a destination as large as the output *and* the
packed input live at the same time; there is no room. The 324,632-byte *code*
hunk does not need to be in chip RAM at all, so about 317 KB of the scarcest
memory on the machine is being spent on a link-time convenience, and the
compression decision follows from it.

**So: read the memory flags in the hunk table before concluding anything about
why a disc is or is not packed.** A game that has taken more than half of chip
RAM for itself cannot pack, whatever the medium looks like. This is the
complement of the [Legends] correction — there, a clean magic scan hid 65 %
packing; here, a clean magic scan is confirmed by an independent constraint.

And note what the same disc does compress: its 115-page manual is IFF ILBM with
**`ByteRun1`**, 7.36 MB of raster down to 2.98 MB, a ratio of 0.404. **A format's
own RLE is not a cruncher and should not be counted as one** — but it should be
measured, because on that disc it is the only compression there is and leaving
it out of the census would have said "nothing on this disc is compressed",
which is false in the way that matters to a reader.

## 6. Executables and overlays""")

# ---------------------------------------------------- section 8: the TOC
edit("section 8: third TOC-free disc",
"""## 9. Text""",
"""### A THIRD DISC PLAYS RED BOOK WITHOUT EVER READING THE TOC — AND IT IS THE ONE WITH THE MOST TO GET WRONG

[Fire & Ice] plays 22 tracks from constants; [Gloom] drives the drive through
Akiko with no `OpenDevice` at all. **[James Pond 2] is the third, and the
cleanest case yet**, because the mapping is *data* rather than code and can be
read out whole.

```
python3 tools/iocmd.py extract/RoboCod
     9 (0x09) x1   input.device IND_ADDHANDLER
    10 (0x0a) x1   input.device IND_REMHANDLER
    37 (0x25) x1   CD_PLAYTRACK   io_Length=#$1  io_Data=0  io_Offset=$6b8.l
    40 (0x28) x2   CD_PAUSE       io_Length=#$1 / #$0  (pause, then resume)
```

**Three CD commands on the whole disc.** No `CD_INFO`, no `CD_CONFIG`, no
`CD_TOCMSF`, no `CD_TOCLSN`, no `CD_GETNUMTRACKS`. Stopping is `CheckIO` /
`AbortIO` / `WaitIO` on the outstanding request, with no command at all.

And `io_Offset` comes from a table:

```
015b66  lea.l   $2cf3a.l, a0      ; the level table
015b6c  move.w  $3c59a.l, d0      ; the level number
015b72  mulu.w  #$c, d0           ; 12 bytes per record
015c8e  move.b  $b(a0), d0        ; byte 11 = the music id
00bd70  btst.b  #$7, d0           ; bit 7 -> Red Book, else the internal replayer
00bd78  bclr.b  #$7, d0           ; ...and the low seven bits are the TRACK NUMBER
```

**Bit 7 of a music identifier selects Red Book or Paula, per tune.** [Fire &
Ice] offers the same choice as a menu option; this disc bakes it into a data
table, and all **86** of its records choose Red Book — so the internal replayer
is present, reachable and never asked for. Tracks 3–8 are used 15/14/19/9/24/5
times and track 2 comes from a constant in the front end, which makes **all
seven audio tracks reachable** and the disc the third "every track reachable"
case after [Guardian] and [Marvin].

**Two things to carry.**

**When `io_Offset` is a variable rather than a constant, find the table before
giving up.** One `lea` and one `mulu` in the level-start routine gave the
address, the stride and the column; walking 86 records then gave the whole
soundtrack map for the cost of one script. A disc that plays "some tracks" and
a disc that plays "all of them from a table" look identical at the `io_Command`
histogram and are completely different findings.

**And a hardcoded table means the music is welded to the pressing.** There is
no TOC read anywhere, so the same executable on a disc with a different track
layout plays the wrong music silently. That is worth knowing before anyone
re-masters one of these.

**A watchdog with no query.** `CD_PLAYTRACK` plays one track and stops, so
continuous music needs the end noticed. [Fire & Ice] re-issues after a
`CD_INFO` poll every 150 frames. This disc has **no query at all**: it sets a
counter to 250 after each play, decrements it in the game loop and re-issues
when it expires. **If a disc plays Red Book and never queries the drive, look
for a bare countdown** — it is the cheapest version of the idea and it leaves
only a `move.l #$fa` and a `subi.l #$1` behind.

## 9. Text""")

# ---------------------------------------------------- section 9: string model
edit("section 9: a sixth string model",
"""## 10. Baselines""",
"""### A SIXTH STRING MODEL: A COMPLETE LOCALISATION WITH NO CHARACTERS IN IT

[Alfred Chicken] was the fifth model — **no text at all**, with the game's own
title existing only as a 320 x 184 picture. [James Pond 2] is the sixth and it
is the mirror image: a **complete three-language manual**, eleven chapters,
115 pages, 7.36 MB of raster — and a prose census over the whole 195 MiB volume
of **10,875 bytes, 0.0155 % of the file bytes**, whose largest single
contributor is the **boot script**.

The manual is 115 IFF ILBM pages, 320 x 200 x 8 planes, `ByteRun1`, in `uk`,
`fr` and `gr` sets of 37, 38 and 40 pages. There is not one character in any of
them. So every measurement this section prescribes — string count, encoding,
byte-identical strings across a localisation, accents remapped onto punctuation
— returns **zero**, and zero is not the same as nothing to measure.

**What to measure when the text is pixels.** Three things, none of which needs
a character, and all three paid on that disc:

1. **Count the distinct palettes.** All 115 pages share **one** byte-identical
   768-byte `CMAP`; the same disc's CDXL streams carry a fresh palette in every
   one of 2,530 chunks. One artist against one palette versus a frame-by-frame
   quantiser, separated without opening a pixel.
2. **Diff the same page number across languages, pixel by pixel.** Unpack the
   `ByteRun1`, convert the planes to one index per pixel, and count differences.
   On that disc exactly **one page of 115 is byte-identical across all three
   languages**, and it is the largest and the inkiest — the one full-page
   illustration with no text on it. Every other page differs by 3.7 % to 25.9 %
   of its pixels, mean 12.94 %. **That is the pixel-domain form of "count the
   byte-identical strings to find where the translation stopped"**, and here it
   proves the translation stopped nowhere.
3. **Read the chunk list, not only the image.** 17 of the 115 pages carry a
   Deluxe Paint **`DPPS`** page-setup chunk — **ten English, seven French, zero
   German**. A chunk nobody reads, present on a subset, is a build split for
   the cost of one parse; and it names the paint package, which is otherwise
   unrecorded anywhere on the disc.

**And the page counts alone are a finding, available from `ls`.** 40 German
pages against 38 French and 37 English is German running 8.1 % long, and the
chapter indices confirm it independently: identical files for English and
French, every German chapter one page later from chapter 2 onward.

**One thing measurement cannot reach, and it is worth admitting rather than
guessing.** Which language `gr` is, and what the book is called, are not
recoverable from any byte in it. Both were settled by **rendering one page and
looking** — `gr` is German, and the book's title page reads `FI5H FILE`, which
also explains the otherwise inexplicable `if $RoboSelection EQ "FI5H"` in the
boot script. **When the content is pixels, the measurements tell you about the
production and only a render tells you about the content.** Budget for one
render per disc of this shape; it is step 24 applied to a manual.

**A localisation split the set had not produced.** That disc translates its
**manual** into three languages and its **game** into none: no
`GetLanguageSelection`, no second language string anywhere in the executable.
[Universe] translates prose and interface together; [Legends] translates
neither. **Count the two separately**, because a disc can do one and not the
other.

## 10. Baselines""")

# ---------------------------------------------------- section 10: the band
edit("section 10: the floor moves again",
"""## 11. The order of work that worked""",
"""**AND THE FLOOR MOVED AGAIN, ON THE VERY NEXT DISC, FOR THE SAME REASON.**
[James Pond 2] is **1,033,508 bytes on disc and 1,258,076 resident** —
**18.1 %** and **23.1 %** below [Alfred Chicken], which had itself broken a
floor that stood for seventeen discs. Two discs in a row, and both are platform
games whose content lives somewhere other than the data track: Alfred Chicken
puts 99.02 % of its pressed disc into Red Book, this one puts 41.95 % into Red
Book and 32.22 % of its volume into CDXL video.

That is enough to state what the floor was ever measuring. **It was measuring
"titles that keep their content in the file system", not "how small an Amiga
game can be".** A 1993 CD conversion can put the content in Red Book, in a
video stream, or in a picture-book manual and ship an executable that would
have fitted on two floppies — 959,956 bytes, 1.07 double-density disks. The
**ceiling has never moved** across nineteen discs, five years and every genre
the format had, and it is bounded by 2 MB of chip RAM and a 68EC020. **Quote
the ceiling; treat the floor as a property of the question.**

**And this disc forces the definition to be stated rather than assumed.** Its
file set is 70,262,959 bytes, of which 93.90 % is a cartoon and 4.38 % is a
manual. Quoting the disc total would overstate the game by a factor of **68**.
[Superfrog] made the same point at a factor of 2; this one makes it
unignorable. **Before quoting a band figure, say which files you counted**, and
if the disc has a non-game payload, give both numbers.

**A note on the expansion column.** That disc's is **1.217x**, below [Myth]'s
1.369x and [Alfred Chicken]'s 1.297x — and it is **not the same kind of
number**. Theirs are decompression ratios; this one is a `BSS` declaration on a
disc where nothing is packed, so it is bounded below by whatever the
uninitialised data happens to be. **The column mixes two quantities and should
be split** the next time it is touched.

## 11. The order of work that worked""")

# ---------------------------------------------------- section 11: new steps
edit("section 11: step on reading the boot script's prose",
"""23. **Read the credits screen before reading the code.**""",
"""22b. **If a disc contains prose with a date in it, test the date against the
    directory before you use the prose for anything else.** [James Pond 2]'s
    boot script is 3,922 bytes of which twenty-one are the launcher; the rest is
    a signed comment making three checkable claims, and all three pass. It says
    the script was written at **1:30am on 14.07.93** and four files are stamped
    00:03:13 to 01:18:00 that morning. It says *"it's now Sunday 15th August
    1993, at 10:05am"* — 1993-08-15 **was** a Sunday, and three directory
    records are stamped 10:41, 10:42 and 10:49, 36 to 45 minutes later. It
    complains that *"Friday 13th was so bad for us"* while converting animation
    — 1993-08-13 **was** a Friday, and `Intro.cdxl` is stamped 21:33:05 that
    evening.

    ```
    python3 -c "import datetime; print(datetime.date(1993,8,15).strftime('%A'))"
    Sunday
    ```

    Three checks, three `strftime` calls. **And if the prose survives, the rest
    of it has earned a hearing**: that same comment names four development tools
    that leave no other trace on the disc — 16-bit TARGA captures taken with the
    red and blue cables swapped, an ARexx script written to fix them, an A3000
    that died mid-conversion, and a NEC CD-ROM drive on an A4000/040 with beta
    driver software — and it explains a measurable property of the disc's
    largest asset (the CDXL audio arrived as "2 big AIFF sound samples", which
    is why it is one mono stream played on two Paula channels).

    **The general rule: a comment is evidence, and it is falsifiable evidence.**
    Test it like a `$VER:`.

23. **Read the credits screen before reading the code.**""")

edit("section 11: the boot script as a program",
"""24. **Render the title logo and read it, because the game may be called
    something else.**""",
"""23b. **Read the boot script as a program, and read the strings of whatever it
    dispatches to.** Four discs now have something in the boot script that is
    not about launching a game, and on [James Pond 2] the script *is* the
    program: `Lab select` plants a label, three `if` blocks switch on an
    environment variable, and `Skip select BACK` jumps back unconditionally — a
    main loop at the shell level, offering a game, a 2 m 43 s cartoon and an
    electronic book as three equal branches, forever, with no exit.

    Two mechanics are worth recognising on sight. The dispatch is through
    **`ENV:`**, which is why `Assign >NIL: ENV: Ram:` is the third line and is
    load-bearing for the whole disc — without it there is no `ENV:` on a
    read-only volume and none of the three branches ever matches. And **one of
    the three tokens appears nowhere else in the script**: `FI5H`. Reading only
    the script leaves the book looking unreachable; reading `RoboSelect`'s
    strings finds `RoboSelection\\0Cartoon\\0FI5H\\0RoboCod\\0` in one run at
    offset `0x85e` and settles it in one command. **A boot script's tokens are
    half of the evidence; the program that writes the variable is the other
    half.**

24. **Render the title logo and read it, because the game may be called
    something else.**""")

# ---------------------------------------------------- open items
edit("open items: add item 41",
"""## Contributing from a pipeline""",
"""41. **Does the trailing 32/232 run and the image overrun ever get confused,
    and has an earlier disc's overrun been mis-read?** [James Pond 2] has a
    trailing unclaimed run of **32** inside its declared volume *and* an image
    overrun of **150**, and the prediction written for it aimed at the wrong
    one of the two. They are separate quantities: the trailing run takes two
    values across nineteen discs (32 and 232, correlating with the preparer
    field) and the overrun has taken thirteen (0, 80, 86, 87, 103, 106, 150,
    152, 152, 152, 180, 225, 227). **Say which one you mean, every time.**

    And that disc raises a question about the overrun that an image cannot
    answer: **its 150-sector overrun is numerically identical to the
    `PREGAP 00:02:00` its cue declares on track 02.** Either the master pads
    the data run up to the pregap (which is what [Alfred Chicken] proved from
    the plastic) and the burner generates the pregap from the directive, or the
    ripper wrote the pregap into the tail of track 1 *and* declared it, in
    which case a disc burnt from that cue is 150 sectors too long. At least one
    earlier image in the set also has a 150-sector overrun and its track-2
    pregap was never checked against it. **On any disc read from plastic, check
    the overrun against the next track's pregap explicitly** — it costs one
    subchannel read and it would close this for the whole set.

42. **How many discs ship `lowlevel.library` and `nonvolatile.library`, and are
    they the same builds?** Every OS-friendly CD32 title has to ship both, and
    they are Commodore's, so a hash table across the set would be the cheapest
    cross-disc fingerprint available — the same trick that found `SetPatch` 39.6
    circulating between Marvin and [Legends] and `freeanim` between Liberation
    and [Gloom]. [James Pond 2] carries `lowlevel.library` at **6,944** bytes
    and [Alfred Chicken] at **6,920**, with different SHA-1s, which is two
    points and a difference. The pipelines do not commit their extracted trees,
    so nobody can do this from the repositories as they stand. **Re-extract
    `libs/` and `c/` from every image and hash them once**; it produces a column
    for the whole set rather than a fact about one disc.

## Contributing from a pipeline""")


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    path = sys.argv[1]
    text = io.open(path, encoding='utf-8').read()

    # ---- validate every anchor BEFORE writing anything
    bad = []
    for name, old, new in EDITS:
        n = text.count(old)
        if n != 1:
            bad.append((name, n))
        if new.count(old.strip()[:40]) == 0 and old.strip()[:40] not in new:
            pass  # replacements need not contain the anchor
    if bad:
        for name, n in bad:
            print("  anchor %-45s occurs %d times (need exactly 1)" % (name, n))
        raise SystemExit("REFUSING: %d of %d anchors are not unique; nothing written"
                         % (len(bad), len(EDITS)))
    print("all %d anchors unique" % len(EDITS))

    # ---- apply
    before = len(text)
    for name, old, new in EDITS:
        text = text.replace(old, new, 1)
        print("  applied %s" % name)

    io.open(path, 'w', encoding='utf-8', newline='\n').write(text)
    print("OK: %d -> %d bytes (+%d)" % (before, len(text), len(text) - before))


if __name__ == '__main__':
    main()
