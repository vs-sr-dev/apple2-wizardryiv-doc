# -*- coding: utf-8 -*-
"""Apply the [Myth] narrative edits to cd32-platform-notes.md.

Every edit is an assertion: if the anchor text is not found exactly, the script
raises and writes nothing.  Insertions are anchored on text that must be
unique.  Run once; running twice will fail on the anchors it has already
replaced, which is the intended behaviour.

Usage: python3 tools/patch-myth.py cd32-platform-notes.md
"""
import io, sys

EDITS = []


def rep(old, new, count=1):
    EDITS.append(('rep', old, new, count))


def ins_after(anchor, new):
    EDITS.append(('ins', anchor, new, 1))


# ---------------------------------------------------------------- disc list
ins_after(
"| [Prey: An Alien Encounter, **CDTV**](https://github.com/vs-sr-dev/cd32-prey-doc/blob/main/docs/09-cdtv-1992.md) | **1992** | The same game a year earlier, published by KirkMoreno alone. **The first disc here not mastered with ISOCD**, the first CDTV disc, the oldest master by fourteen months, and the control that corrected two claims about the other three. 1,453 files, of which **1,201 are byte-identical to the CD32 release** |",
"\n| [Myth: History in the Making](https://github.com/vs-sr-dev/cd32-myth-doc) | **1992/1993** | System 3 Arcade Software, UK — developer and publisher in one, a label new to this set, and **the disc that is its own floppy release**. One track, **no audio track**, **five files and two directories**, 27,361 sectors of which **25,600 are a hole of exactly 50.000000 MiB** — 94.86 % of the declared volume — leaving a 2.72 MB game. Three of the five files are **901,120 bytes each: one 880 KiB Amiga floppy disk, exactly**, bootblocks and unused blocks included, so the floppy ancestor is not inferred but pressed. The 18,656-byte CD shim has **zero relocations**, four media back ends (DOS, floppy with MFM decode, hard disk with `RigidDiskBlock` parsing, CD through **Akiko**), a **hand-written `LoadSeg`**, and it hands the game a fixed key the floppy earned from its copy protection. Compression is **Bytekiller under the magic `DAVE`** — the programmer's first name — 23 streams, **depth 0**, every one validated three ways. **Expansion 1.369x, the lowest of ten.** The preparer field is a **fourth pattern: a company**, `ROB NORTHEN COMPUTING`, the author of RNC ProPack — on a master that does not use it. And the PVD's **1992-12-21 is falsified by the disc's own `.TM` block**, which is copyright 1993 |")

# ------------------------------------------------------------ preparer list
rep("""Universe      D J Pocock - ISOCD 1.04 by Pantaray, Inc. USA -
```""",
"""Universe      D J Pocock - ISOCD 1.04 by Pantaray, Inc. USA -
Superfrog     Kenny Grant - ISOCD 1.04 by Pantaray, Inc. USA -
Myth          ROB NORTHEN COMPUTING, UK. TEL: + 44 428 707771
              FAX: + 44 428 707772 - ISOCD 1.04 by Pantaray, Inc. USA -
```""")

# ---------------------------------------------------- preparer shape table
rep("""```
preparer shape                       discs   trailing run
`D J Pocock`                             5   232, every time
empty name, tool signature only          5   32 (on the four cut with ISOCD)
six other named operators                6   32
```""",
"""```
preparer shape                       discs   trailing run
`D J Pocock`                             5   232, every time
empty name, tool signature only          5   32 (on the four cut with ISOCD)
six other named operators                6   32
a COMPANY, with a phone and fax number   1   32          <- [Myth]
```""")

rep("""narrower **`D J Pocock` leaves 232 and nobody else does** — 5 of 5 against 11 of
11, across eleven studios.""",
"""narrower **`D J Pocock` leaves 232 and nobody else does** — 5 of 5 against 11 of
11, across eleven studios.

**A FOURTH SHAPE, AND IT IS NOT A PERSON.** [Myth]'s preparer field reads
`ROB NORTHEN COMPUTING, UK. TEL: + 44 428 707771 FAX: + 44 428 707772` before
the usual `- ISOCD 1.04 by Pantaray, Inc. USA -`. A **firm, with a telephone
number and a fax number**, advertising itself in a volume descriptor. Trailing
run **32**, so the correlation survives and *not-Pocock leaves 32* is now
**12 of 12**.

Two things follow.

**The box does not always hold a person, so "the operator" is too narrow a
label for what it records.** It records *whoever ran the tool*, and this disc
shows that could be a **mastering bureau under contract** rather than anyone at
the studio. That is a fifth possible owner for an artefact — not the studio, not
the label, not the tool, not one named person, but a contractor — and it fits
the `D J Pocock` group better than anything proposed so far: one name on five
masters from five unrelated studios and five unrelated publishers, findable
nowhere on any of them, is the shape of a bureau operator, not of an employee.
That remains an inference; the test is another disc naming a firm, or a
`D J Pocock` disc that names a firm anywhere else.

**And the firm is the author of the set's commonest cruncher.** Rob Northen
Computing wrote **RNC ProPack**, which is on Dragonstone, Banshee, HeroQuest II,
Universe and Gunship 2000, with Liberation's codec wearing its magic — six discs
of seventeen. The firm that wrote it cut the master of a seventh, **and that
seventh does not use it**: [Myth] packs with Bytekiller, written by the game's
own programmer. One negative, one for one, and it is the cleanest separation of
the mastering step from the build step this set has: the same firm's name is on
the master and its packer is nowhere in the game. **On the next disc, read the
preparer field for a company name as well as a person's, and if you find one,
ask whether its own tools appear in the payload.**""")

# ---------------------------------------------------------------- .TM count
rep("""**All three SHA-1s match, byte for byte, on fourteen of the fifteen CD32-era
discs** — Dragonstone, Marvin, Prey CD32, [Legends], [Liberation], [Microcosm],
[Gloom], [HeroQuest II], [Guardian], [Banshee], [Fire & Ice], [Universe],
**[Gunship 2000]** and **[Superfrog]**:""",
"""**All three SHA-1s match, byte for byte, on fifteen of the sixteen CD32-era
discs** — Dragonstone, Marvin, Prey CD32, [Legends], [Liberation], [Microcosm],
[Gloom], [HeroQuest II], [Guardian], [Banshee], [Fire & Ice], [Universe],
[Gunship 2000], [Superfrog] and **[Myth]**:""")

rep("""Ten studios, ten publishers, ten engines with nothing in common, and
**thirty-eight months** between Prey's CD32 master (1993-11-29) and Legends'.
Same 2,048 bytes, in a sector nothing on any of them reads.""",
"""Eleven studios, eleven publishers, eleven engines with nothing in common, and
**thirty-eight months** between Prey's CD32 master (1993-11-29) and Legends'.
Same 2,048 bytes, in a sector nothing on any of them reads.

**AND THE BLOCK DATES THE MASTER THAT CARRIES IT.** Its banner reads
`* Copyright (c) 1993 - Commodore Electronics Ltd. *`, and Prey's `/CD32.TM`
file puts the assembly of this version before 1993-06-10. So **a volume whose
PVD claims a date earlier than 1993 and which carries these bytes is lying about
its date**, and the check costs one `grep`. [Myth] is where that first paid: its
PVD says 1992-12-21 and it carries the 1993 banner, which is the first hard
falsification of that epoch anywhere in this set. The same argument applies
unchanged to [Banshee] and [Marvin], the two other discs stamped 1992-12-21,
because both carry the same block. **When a CD32-era PVD predates mid-1993, read
the trademark banner before believing the date.**""")

# ------------------------------------------------------------- compression
rep("""**[Banshee] makes it [7 of 7]**: 37 of 45 files RNC ProPack 1, four""",
"""**[Myth] makes it [12 of 12], and it is the end of the line for this rule's
positive side** — there is no stronger form available. The disc does not
*refer* to a floppy ancestor and does not *inherit* a floppy loader: it **is**
the floppy release. Three of its five files are 901,120 bytes each — one
880 KiB Amiga disk, exactly — carrying their own bootblocks with valid
checksums, their own chunk directories in block 2, and their own unused blocks
complete with a stray copy of Commodore's `ConClip`. The CD-specific part of the
product is an 18 KB shim that emulates a floppy drive out of CD sectors, and it
compresses nothing that the floppy release did not already compress.

**Which is also a warning about the census.** A file whose length is an exact
multiple of a known medium's capacity is a medium, not a file: 901,120 for an
Amiga DD floppy, 1,802,240 for an HD one, 368,640 or 737,280 for PC 5.25-inch
formats. Check the length before running any magic scan, because the streams are
one level down and the offsets that name them are in the image's own directory
block, not in the ISO. On [Myth] a disc-wide magic scan over the five files
would have found **zero**, because 22 of the 23 streams carry a magic the scan
does not know and the twenty-third carries none at all.

**[Banshee] makes it [7 of 7]**: 37 of 45 files RNC ProPack 1, four""")

# ---------------------------------------------------------------- section 10
rep("""Sixteen discs, and they bracket the format rather than agreeing on it.""",
"""Seventeen discs, and they bracket the format rather than agreeing on it.""")

rep("""  factors now run 1.43x, 1.89x, 1.99x, 2.00x, 2.10x, 2.72x, 2.93x, **3.25x**,
  3.78x — and nothing about the genre picks the bin.""",
"""  factors now run **1.369x**, 1.43x, 1.89x, 1.99x, 2.00x, 2.10x, 2.72x, 2.93x,
  **3.25x**, 3.78x — ten of them — and nothing about the genre picks the bin.
  **[Myth] is the new bottom at 1.369x**, on a 2D platformer, which is the same
  genre that holds second place. Two of the ten extremes are the same genre, so
  the genre carries no information at all.
* **And the denominator can be somebody else's data.** [Myth]'s three floppy
  images contain **172,010 bytes — 6.36 % of its on-disc total — that no chunk
  table claims**, including a copy of Commodore's `ConClip` and 156 KB of
  high-entropy residue left on the physical media before the game was written to
  it. Measured on both sides against only the bytes the game reaches, the factor
  is 1.394x. **When a disc ships whole media rather than files, say which
  denominator the expansion figure uses.**""")

# ---------------------------------------------------------------- Akiko table
rep("""| | Discs using it | Which |
|---|---:|---|
| `$00B80000` as a **pointer load** — driving the drive | **2 of 14** | [Dragonstone], **[Universe]** |
| `$00B80030` — the **I²C port to the CD32's serial EEPROM** | **1 of 14** | **[Universe]** |
| `$00B80038` / `$00B8003C` — the **C2P port** | **0 of 14** | none |
| `$C0DE0000` — the identification constant | **0 of 14** | none |""",
"""| | Discs using it | Which |
|---|---:|---|
| `$00B80000` as a **pointer load** — driving the drive | **3 of 17** | [Dragonstone], [Universe], **[Myth]** |
| `$00B80030` — the **I²C port to the CD32's serial EEPROM** | **1 of 17** | **[Universe]** |
| `$00B80038` / `$00B8003C` — the **C2P port** | **0 of 17** | none |
| `$C0DE0000` — the identification constant | **0 of 17** | none |

*(These denominators were stale at "14" for three discs. They are recounted
here against the seventeen discs in the list at the top of this document, and
the lesson is the general one: **re-read the counts you quote, not only the ones
you add**.)*

**THE THIRD DRIVE-DRIVER, AND THE BASE RATE WAS THE WRONG PRIOR.** [Myth]
predicted `$00B80000` absent on the base rate — 2 of 16 — and was wrong. The
mechanism was available and would have got it right: **a disc that kills the
Exec in its first two hundred instructions and opens no device has no other way
to reach the CD.** [Myth] makes exactly three library calls in its whole loader
(`OpenLibrary`, `CloseLibrary`, `Disable`), zero `OpenDevice` anywhere on the
disc, and then drives eleven Akiko registers by hand: `$04` and `$08` for the CD
interrupt request and enable, `$10`/`$14` for the command buffer addresses,
`$18`–`$1F` for the transmit and receive ring indices, `$20`, and `$24` for the
CD DMA register. **Condition the Akiko prediction on whether the loader opens a
device, not on how many previous discs drove the chip.**""")

# ---------------------------------------------------------- 1992-12-21 epoch
rep("""```
Banshee   41 file records            1992-12-21 15:11:46 .. 15:27:34
Marvin    PVD                        1992-12-21 15:15:40
Marvin    all nine directory records 1992-12-21 15:24:31 .. 15:26:43
```""",
"""```
Banshee   41 file records            1992-12-21 15:11:46 .. 15:27:34
Marvin    PVD                        1992-12-21 15:15:40
Marvin    all nine directory records 1992-12-21 15:24:31 .. 15:26:43
Myth      the bulk write group       1992-12-21 15:12:38 .. 15:15:31
```

**A THIRD DISC, AND THE FIRST ONE THAT CAN BE PROVEN WRONG FROM INSIDE ITS OWN
IMAGE.** [Myth]'s bulk group falls inside Banshee's window and brackets Marvin's
PVD: three discs, three unrelated publishers, three unrelated studios, one
afternoon.

[Myth] is the hard case, because it is a **1992 game** — its bootblock and its
credit screen both say `1992` — so a 1992 master date looked like it might
simply be correct. It is not, and the disc says so: the `.TM` block it carries
reads `Copyright (c) 1993 - Commodore Electronics Ltd.`, and its loader needs a
68020 and Akiko, neither of which existed in a shipping Commodore console in
December 1992. **A date that happens to match the game's real year is the
hardest one to doubt, and the trademark banner settles it for one `grep`.** All
three of these discs carry that block, so the same argument falsifies all three.

**And the window is where the session STARTS, not where it lives.** [Myth]'s
records run from 15:12:38 to 17:10:58 — nearly two hours — and only the first
three minutes fall inside the shared quarter hour. That is a genuine test of the
stored-base-date hypothesis rather than a restatement of it: a machine that
restores a fixed date at boot and runs forward predicts that the *first* bulk
write clusters and that everything after it does not. Three discs now show a
clustered start. **On the fourth, look for the first bulk write near 15:1x and
let the rest of the session run where it likes.**""")

# ---------------------------------------------------------------- step 37
rep("""    Nothing is known about what that means, because **no disc in this set has
    had that field checked**, so there is no baseline to compare against. That
    is exactly why it is a step: it costs one line of code per disc, and after
    three or four discs it will either be a normal artefact of the mastering
    tool or it will be a finding. Report it either way. (Sections 1 and 3.)""",
"""    **THE SECOND POINT EXISTS NOW, AND IT IS THE NORMAL CASE.** [Myth]'s root
    directory record reads 1992-12-21 16:59:24: **one second older than the
    newest of the five files it indexes** and 1h46m46s newer than the oldest,
    stored identically in the same three places, with its one subdirectory dated
    with its file. Its PVD is a normal +11m33s.

    Both discs were cut with **ISOCD 1.04**, so the one thing the baseline
    settles immediately is that **[Superfrog]'s seven-day-old root record is not
    a tool artefact** — the same tool version writes a contemporaneous record on
    the other disc. What it cannot yet separate is a reused staging directory
    from a hand-set date. Two points; report the third with the sign, and
    **report it especially when it is normal**, because that is how this closes.
    (Sections 1 and 3.)""")

# ---------------------------------------------- open question 30 (zero hole)
rep("""    The three earlier gaps are odd numbers and were never explained. Gunship's
    is a round binary number to the byte, and that changes what kind of thing it
    can be: a round reservation is something **asked for**, not something a
    layout algorithm produces.""",
"""    **[Myth] is the fifth, and the second round binary number: 25,600 sectors =
    52,428,800 bytes = exactly 50.000000 MiB, every byte zero, 94.86 % of its
    declared volume** — the largest share the anomaly has ever taken, on the
    smallest volume it has ever appeared in. Two exact binary reservations on
    two unrelated masters, both cut with ISOCD 1.04, both in front of the files,
    one 100 MiB and one 50 MiB.

    That is now enough to name the shape of the answer: it looks like a
    **reserved-space figure typed into the mastering tool in megabytes**. The
    test is cheap and specific — **a sixth disc with a front hole, and its size
    in MiB**. If the sizes keep landing on round binary values the parameter is
    real; if a 1.03 master produces one, the parameter is not new to 1.04.

    The three earlier gaps are odd numbers and were never explained. Gunship's
    is a round binary number to the byte, and that changes what kind of thing it
    can be: a round reservation is something **asked for**, not something a
    layout algorithm produces.""")

# ---------------------------------------------- open question 33 (root date)
rep("""    **No other disc in this set has had this field read**, so there is no
    baseline and no way to tell an ISOCD artefact from a staging-directory
    inheritance from a hand-set date. This is now step 37 precisely because it is
    cheap: read it on every disc, report it with the sign, and after a few discs
    the question answers itself. (Sections 1, 3.)""",
"""    **PARTLY ANSWERED, by [Myth], and the answer is that it is not the tool.**
    Myth's root directory record is 1992-12-21 16:59:24, **one second older than
    the newest of the five files it indexes** and 1h46m46s newer than the oldest
    — stored identically in the same three places, with its single subdirectory
    dated with its file. That is what a normal root record looks like, and Myth
    was cut with **ISOCD 1.04, the same version as Superfrog**. So the anomaly
    belongs to Superfrog's master and not to the mastering tool.

    What two points still cannot separate is a **reused staging directory** from
    a **hand-set date**. Read the field on the third and fourth disc; the
    baseline now exists to compare against. (Sections 1, 3.)""")

# --------------------------------------------- artefact ownership table (14)
rep("""    | artefact | owner | evidence |
    |---|---|---|
    | cruncher | **the label** | two Team 17 discs, two studios, two years, one packer; five other studios, five other crunchers |
    | `.TM` block | **the mastering tool** | fourteen discs, eleven labels, identical bytes |
    | preparer field, trailing run | **the operator** | `Pocock` 232 on 5 of 5; everyone else 32 on 11 of 11 |
    | colour depth, save system, music format | **the studio** | Speris and Superfrog disagree on all three |""",
"""    | artefact | owner | evidence |
    |---|---|---|
    | cruncher | **the label** | two Team 17 discs, two studios, two years, one packer; five other studios, five other crunchers. **[Myth] adds a label with no prior**, using one packer — its own programmer's — so it is consistent and cannot separate label from studio, because System 3 is both |
    | `.TM` block | **the mastering tool** | **fifteen discs, eleven labels, identical bytes** |
    | preparer field, trailing run | **the operator, or a bureau** | `Pocock` 232 on 5 of 5; everyone else 32 on **12 of 12**. **[Myth]'s field names a company with a phone and fax number**, so "operator" needs widening to include a contractor |
    | colour depth, save system, music format | **the studio** | Speris and Superfrog disagree on all three; **[Myth] makes it three discs agreeing on none of them** — 5/4-plane ECS output, no save system at all, OctaMED |""")

rep("""    **What to do on the next same-label pair:** stop asking which single owner
    build practice has, and instead assign each artefact to the step that
    produced it — the game build or the mastering run — before comparing. And
    look for a disc that names the operator *and* the authors, because that is
    what turns the assignment from an inference into a measurement.""",
"""    **What to do on the next same-label pair:** stop asking which single owner
    build practice has, and instead assign each artefact to the step that
    produced it — the game build or the mastering run — before comparing. And
    look for a disc that names the operator *and* the authors, because that is
    what turns the assignment from an inference into a measurement.

    **[Myth] separates the steps by timestamp, which no earlier disc could.**
    Its three floppy images and its boot script were written in one 2m53s burst;
    the CD-specific loader was written **alone, 1h44m34s later**; the master was
    cut 11m33s after that. So the build artefacts (Bytekiller, the `DAVE`
    container, the chunk tables, the trackloader), the conversion artefacts (the
    Akiko driver, the forced protection key, a one-byte patch to a memory probe)
    and the mastering artefacts (the ISO volume, the preparer field, the `.TM`
    block, the 50 MiB hole, the 32-sector run) are separated *by the disc's own
    dates* rather than by inference. **Sort the directory by timestamp and look
    for a record that stands alone: that is where the conversion is.**""")

# ------------------------------------------------- the five places for music
rep("""### A FIFTH PLACE FOR THE MUSIC, AND A `M.K.` SCAN CANNOT SEE IT""",
"""### AND A DISC CAN USE TWO OF THE FIVE PLACES AT ONCE

[Myth] has no audio track and uses **place 1 and place 2 together**: two OctaMED
`MMD0` modules that each occupy a whole asset chunk, and two IFF `8SVX` samples
**inside a hunk executable**, invisible to any census of files. The modules are
validated by their own declared length matching the chunk to the byte, and the
8SVX carry `ANNO` chunks naming the tool — `Audio Master` on one and
`Audio Master II` on the other, two versions of one sampler on one disc.

Two counts worth taking on any module: **how many instrument slots are empty**
(2 of 18 here) and **how many are named** (**0 of 18** — both modules were saved
with a two-byte `iinfo` entry, so there is no room for a name and the composer
has to come from the credit screen). And check the play sequence against the
block count: one of Myth's two modules never plays block 2 of its four.

### A FIFTH PLACE FOR THE MUSIC, AND A `M.K.` SCAN CANNOT SEE IT""")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'cd32-platform-notes.md'
    s = io.open(path, encoding='utf-8').read()
    n_before = len(s)
    for i, (kind, anchor, new, count) in enumerate(EDITS):
        found = s.count(anchor)
        if found != 1:
            raise SystemExit("EDIT %d: anchor found %d times, expected 1:\n  %r"
                             % (i, found, anchor[:90]))
        if kind == 'rep':
            s = s.replace(anchor, new, 1)
        else:
            s = s.replace(anchor, anchor + new, 1)
        print("edit %2d ok  (%+d chars)" % (i, len(new) - (len(anchor) if kind == 'rep' else 0)))
    io.open(path, 'w', encoding='utf-8', newline='\n').write(s)
    print("wrote %s: %d -> %d chars, %d edits" % (path, n_before, len(s), len(EDITS)))


if __name__ == '__main__':
    main()
