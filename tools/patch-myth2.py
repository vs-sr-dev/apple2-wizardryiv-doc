# -*- coding: utf-8 -*-
"""Second [Myth] patch: two new steps, three new open items, and the text-model
addition. Same contract as patch-myth.py -- every anchor must be unique or the
script writes nothing.

Usage: python3 tools/patch-myth2.py cd32-platform-notes.md
"""
import io, sys

EDITS = []


def rep(old, new):
    EDITS.append((old, new))


# ------------------------------------------------- section 9, a fourth model
rep("""A parser that assumed a length field, forward-only offsets and one record
shape found 26 tables and 61 KB on that disc.""",
"""**A FOURTH MODEL, AND IT IS NOT A FLAT TABLE AT ALL.** The set has now seen
four ways of storing display text: an offset table into flat strings
([Universe]), everything inline in the code ([Gunship 2000]), separate text
files parsed at run time ([Superfrog]), and — on [Myth] — **a relocated
longword page index over chains of position-prefixed records**. A record there
is

```
[flag] [column] [row] TEXT
```

with `$FF` starting a new page, `$00` continuing one, and **the next record's
flag byte serving as this record's terminator**; there is no NUL. Two things
follow that are worth carrying:

* the page-index entries are covered by `HUNK_RELOC32`, so `relocs.py --list 0`
  **proves they are pointers** instead of leaving it to plausibility — and each
  one lands one byte *past* its page's flag, on the `column` byte;
* a raw strings dump reports the `row` byte as a leading character on every
  line, so the credits come out as `:MARK CALE`, `2THE FINAL` and
  `HALAN HUNNISETT`. **When every string in a dump has one junk character in
  front of it, that character is the layout, and the record header is three
  bytes wide.**

Myth's two tables hold 12 and 10 entries, one ending at an explicit
`$FFFFFFFF` and one running straight into the data it points at, with **zero
empty slots** and no repeated or backward entry — so of the three traps below,
only the second applies, and it applies with `$00`/`$FF` in the terminator's
place. **Establish which model a disc uses before writing the parser; the traps
are model-specific and two of the four models have none of them.**

A parser that assumed a length field, forward-only offsets and one record
shape found 26 tables and 61 KB on that disc.""")

# --------------------------------------------------------- steps 38 and 39
rep("""    Both discs were cut with **ISOCD 1.04**, so the one thing the baseline
    settles immediately is that **[Superfrog]'s seven-day-old root record is not
    a tool artefact** — the same tool version writes a contemporaneous record on
    the other disc. What it cannot yet separate is a reused staging directory
    from a hand-set date. Two points; report the third with the sign, and
    **report it especially when it is normal**, because that is how this closes.
    (Sections 1 and 3.)

## Contributing from a pipeline""",
"""    Both discs were cut with **ISOCD 1.04**, so the one thing the baseline
    settles immediately is that **[Superfrog]'s seven-day-old root record is not
    a tool artefact** — the same tool version writes a contemporaneous record on
    the other disc. What it cannot yet separate is a reused staging directory
    from a hand-set date. Two points; report the third with the sign, and
    **report it especially when it is normal**, because that is how this closes.
    (Sections 1 and 3.)

38. **Check every file length against the capacities of removable media before
    running any scan.** [Myth] has five files, and three of them are **901,120
    bytes each — 80 tracks x 2 sides x 11 sectors x 512 bytes, one
    double-density Amiga floppy disk, exactly.** The CD32 release is the 1992
    three-floppy release pressed whole, bootblocks and unused blocks included,
    with an 18 KB shim that emulates a floppy drive out of CD sectors.

    The lengths worth recognising on sight: **901,120** (Amiga DD), **1,802,240**
    (Amiga HD), **368,640** and **737,280** (PC 5.25-inch), **1,474,560** (PC
    1.44 MB), and any exact multiple of them. When one turns up, the disc is one
    level deeper than it looks and four things change at once:

    * **the census is inside the image, not in the ISO.** [Myth]'s asset
      directory is a table of `(offset, length)` longwords in **block 2** of each
      floppy image, which is exactly where a trackloader's bootblock reads it
      from. 28 chunks across three images, none of them a file.
    * **the bootblock is a document.** Its checksum tells you whether Kickstart
      would boot the disk (all three of Myth's validate; one declares `DOS\\0`
      and two declare type zero), and its text tells you who wrote it — Myth's
      say `(c) 1992 System 3 arcade software ltd` and `(c) 1991 Dave Colclough`,
      which is where the game's real year and its programmer come from.
    * **the unused blocks are evidence.** 6.36 % of Myth's on-disc bytes are
      outside every chunk-table entry and only 2 % of that is zero: a `SYS3` fill
      pattern, 8-bit PCM, and **a complete copy of Commodore's `ConClip 37.7`**
      with its `$VER:` string, which is the only `$VER:` on the whole disc. That
      is what was on the physical media before the game was written to it.
    * **the floppy-origin rule stops being an inference.** Section 5's rule is
      normally read off disk-swap prompts, volume names or device paths; here the
      floppies *are* the payload, and the rule is at [12 of 12].

    Cheap, and it happens before anything else: sort the file lengths and look
    for a round medium. (Sections 1, 5.)

39. **Date the master against the copyright year in the block it carries, not
    only against its own timestamps.** The CD32-era `.TM` block reads
    `Copyright (c) 1993 - Commodore Electronics Ltd.`, and [Prey CD32] ships the
    same bytes as a dated file, `/CD32.TM`, 1993-06-10. So **any CD32-era volume
    whose PVD predates mid-1993 and which carries that block is lying about its
    date**, and a `grep` for `Commodore Electronics` settles it.

    [Myth] is where this first paid, and it is the hard case: the PVD says
    1992-12-21 and the game genuinely is from 1992, so the date looked
    defensible until the banner was read. The same argument applies unchanged to
    [Banshee] and [Marvin], the two other discs stamped 1992-12-21.

    The general form is worth more than the instance: **a disc carries dated
    third-party material, and third-party material cannot be older than the
    volume that holds it.** Version strings in shipped Commodore commands,
    `$VER:` dates, library versions and trademark banners are all upper bounds
    on how old a master can be, and they are independent of whatever clock the
    build machine had. (Sections 1, 2, 3.)

## Contributing from a pipeline""")

# ------------------------------------------------------- new open items 35-37
rep("""    decoder.** The `PaCK` codec itself is still unread. (Section 5.)""",
"""    decoder.** The `PaCK` codec itself is still unread. (Section 5.)

35. **New — is the zero hole a reserved-space figure typed in megabytes?**
    Five discs leave a gap between the volume descriptors and the first file:
    [Prey CD32] 6,000 sectors, [Microcosm] 15,000, [HeroQuest II] 24,272,
    **[Gunship 2000] 51,200 = exactly 100 MiB** and **[Myth] 25,600 = exactly
    50.000000 MiB**. Two of the five are round binary numbers to the byte, on
    unrelated masters from unrelated publishers, both cut with ISOCD 1.04, both
    in front of the files.

    A round reservation is something asked for, not something a layout algorithm
    produces, and two of them make "somebody typed 100" and "somebody typed 50"
    the cheapest available explanation. **The test is a sixth front hole and its
    size in MiB**; a hole on an ISOCD 1.03 master would additionally say the
    parameter is not new to 1.04. (Sections 1, 10.)

36. **New — does the preparer field sometimes name a bureau rather than a
    person?** [Myth]'s reads `ROB NORTHEN COMPUTING, UK. TEL: + 44 428 707771
    FAX: + 44 428 707772` — a firm with contact details, a fourth shape for a
    field this document has read on sixteen discs as "the operator". Trailing run
    32, so the layout correlation is untouched.

    If CD32-era masters were routinely cut by contractors, the `D J Pocock`
    group stops being a puzzle: one name on five masters from five unrelated
    studios and five unrelated publishers, findable nowhere on any of them, is
    what a bureau operator looks like from inside the data. **The test is another
    disc naming a firm in that field, or a `D J Pocock` disc that names a firm
    anywhere else in its payload.**

    And there is a second, sharper question inside it. Rob Northen Computing
    wrote **RNC ProPack**, which is on six of the seventeen discs here — and the
    master it cut **does not use it**, packing with Bytekiller written by the
    game's own programmer instead. One negative, one for one. **On the second
    Rob-Northen-prepared disc, ask immediately whether it uses RNC ProPack**: two
    negatives would start to say the mastering step and the packing step never
    touch, which is exactly what open item 14 is trying to establish.
    (Sections 1, 5.)

37. **New — what is in the unclaimed blocks of a shipped floppy image?**
    [Myth] presses three 880 KiB disks whole, and **172,010 bytes — 6.36 % of
    its on-disc total — lie outside every entry of the images' own chunk
    tables**. Only 3,428 of those bytes are zero. The identified part is a
    `SYS3` fill pattern, a run of 8-bit PCM, and a complete copy of Commodore's
    `ConClip 37.7`; the unidentified part is **156,292 bytes of entropy 7.6-7.8
    in three runs at the tails of the three disks**, which is the same band as
    the disc's Bytekiller streams.

    The economical reading is a previous build's data left on the physical
    media, but no `DAVE` header validates anywhere in those runs and the
    headerless form of the stream can only be found by trying every candidate
    end, which was not run over 156 KB. **An exhaustive bare-stream end search
    over those three runs would settle it, and a stream that decodes with a zero
    checksum there would be a discarded asset from an earlier build of a shipped
    game** — which no disc in this set has produced yet. (Sections 3, 5.)""")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'cd32-platform-notes.md'
    s = io.open(path, encoding='utf-8').read()
    n = len(s)
    for i, (anchor, new) in enumerate(EDITS):
        c = s.count(anchor)
        if c != 1:
            raise SystemExit("EDIT %d: anchor found %d times, expected 1:\n  %r"
                             % (i, c, anchor[:90]))
        s = s.replace(anchor, new, 1)
        print("edit %d ok" % i)
    io.open(path, 'w', encoding='utf-8', newline='\n').write(s)
    print("wrote %s: %d -> %d chars" % (path, n, len(s)))


if __name__ == '__main__':
    main()
