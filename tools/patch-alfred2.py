#!/usr/bin/env python3
"""Add step 40 and open questions 38-40 for the eighteenth disc, and correct in
place the one rule Alfred Chicken did NOT confirm.

Anchors asserted unique; nothing is written if any is not.
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


# ---------------------------------------------------------------- step 40
STEP40 = """    on how old a master can be, and they are independent of whatever clock the
    build machine had. (Sections 1, 2, 3.)

40. **If the disc is physical, read it twice by two different paths and compare
    them — and make every sector prove its own identity.** [Alfred Chicken] is
    the first disc in this set read from plastic rather than from an image file,
    and neither obvious path could read all of it.

    `ReadFile` on `\\\\.\\E:` returns the *logical volume*, so it stops at the
    declared volume size — 227 sectors short of the end of this disc's data
    track — and it was the only path on this drive that could read LBA 0..15.
    Raw `IOCTL_CDROM_RAW_READ` transfers with TrackMode `CDDA` reach every
    sector, but that mode returns the bytes **as they physically sit on the
    disc**, which on a data track means **scrambled** (ECMA-130 annex B: the
    12-byte sync in the clear, everything from byte 12 XORed with a 15-bit LFSR
    whose first output bytes are `01 80 00 60`). Descrambling is a dozen lines
    and it gives back the real sector: header, 2,048 bytes of user data, EDC and
    ECC.

    Three things follow, and all three are free once the descrambling is done:

    * **the sector mode can be verified instead of assumed.** Every `.cue` in
      this set says `MODE1/2048` and no disc had ever been checked. The
      descrambled header's fourth byte is the mode; on this disc it reads 1 on
      all 902 sectors read that way, not sampled;
    * **every sector proves its own address.** The MODE1 header contains its own
      MSF. On this drive, two consecutive dumps of the same 918 sectors returned
      two *different* wrong answers — sixteen all-zero sectors at LBA 0..15 in
      one run, LBA 0..4 carrying the headers of LBA 241..245 in the next. The
      drive returns stale or misplaced data on the first transfer after a seek.
      **A dumper that writes 2,048 bytes per sector without looking cannot see
      this at all.** Check sync, header address and EDC on every sector and
      re-read the failures; after that the read was stable with zero retries and
      zero errors;
    * **the two paths can be cross-checked where they overlap.** Here that was
      LBA 16..690, 675 sectors, and they agreed byte for byte — a guarantee no
      image in this set had before. Refuse to write the image if they disagree.

    Also read, once, and none of it available from a file: the TOC
    (`IOCTL_CDROM_READ_TOC_EX`), the **MCN** and the per-track **ISRC**
    (`IOCTL_CDROM_READ_Q_CHANNEL`, formats `0x02` and `0x03`), pre-emphasis and
    channel-count bits from CONTROL, and the real pregaps. And **measure the
    drive's read offset** by searching for the sync pattern rather than
    hardcoding it — on this drive it is −24 bytes, six samples, and it is a
    property of the drive, not of the disc. Say so, so that nothing downstream
    mistakes it for one. (Sections 1, 10.)
"""

sub("""    on how old a master can be, and they are independent of whatever clock the
    build machine had. (Sections 1, 2, 3.)
""", STEP40, "step 40 added")


# --------------------------------------------- the overrun, settled in place
sub("""3. **Walk the directory and build a sector map.** List what is *not* claimed
   by any file. On this format that is where the trademark block turns up.
   Build it against the *declared* volume size, not the image size.""",
    """3. **Walk the directory and build a sector map.** List what is *not* claimed
   by any file. On this format that is where the trademark block turns up.
   Build it against the *declared* volume size, not the image size.

   **And the overrun past the declared volume is the mastering, not the
   dumper — [Alfred Chicken] settled this from the plastic.** Fifteen of the
   first seventeen images run 32..232 sectors past their declared volume and
   from a file it is undecidable. On this disc the declared volume is 691
   sectors, the disc physically carries **918** sectors of MODE1 data — every
   one with a valid sync pattern, a header address matching the sector asked
   for and a passing EDC — the extra 227 are all zero, and **they stop exactly
   where the next track's pregap begins**. So the data run is padded up to the
   following track, which explains the whole 32..232 range without invoking a
   dumper artefact anywhere.""",
    "overrun settled in step 3")


# ------------------------------------- compression <-> floppy: an undetermined case
sub("      floppies *are* the payload, and the rule is at [12 of 12].",
    """      floppies *are* the payload, and the rule is at [12 of 12].

    **[Alfred Chicken] is the first UNDETERMINED case, and it stays at
    [12 of 12] rather than becoming 13.** The disc compresses — seven RNC
    ProPack streams as files, four more inside the executable — but **it points
    at no floppy ancestor at all**: zero `DF0:`–`DF3:`, zero `CD0:`, no
    disk-change prompt, no installer, no `.bak`, and no file of a removable-media
    length. What it does name is three volumes that belong to the machine it was
    *built* on: `JJSDISK:` (tested for and branched around in the shipped boot
    script), `alf2:` (in a format string), and `Hard0:` (in an RCS keyword).

    That is a memory of a **development** machine, not of a shipping medium, and
    the honest reading is that the antecedent holds and the consequent is not
    checkable from the disc. Counting it as a thirteenth confirmation would be
    incrementing rather than measuring. **The rule needs a case like this
    written down, because it is the shape a real counterexample would have.**""",
    "compression<->floppy: undetermined case recorded, rule stays at 12 of 12")


# ------------------------------------------------- open questions 38, 39, 40
NEW_Q = """    end, which was not run over 156 KB. **An exhaustive bare-stream end search
    over those three runs would settle it, and a stream that decodes with a zero
    checksum there would be a discarded asset from an earlier build of a shipped
    game** — which no disc in this set has produced yet. (Sections 3, 5.)

38. **New — how many audio tracks does a game actually reach, against how many
    the disc has?** [Alfred Chicken] is the first disc where the denominator is
    measured rather than inherited: nine audio tracks, read from the TOC. The
    numerator is not statically readable. The game opens `cd.device` (two
    `OpenDevice` against exactly two named devices) but writes **no**
    `CD_PLAYTRACK`, `CD_TOCLSN`, `CD_TOCMSF` or `CD_PLAYMSF` as an immediate
    into `io_Command` anywhere — the commands are assembled at run time, exactly
    as its blitter control words and copper lists are.

    A candidate was found and rejected, and the rejection is the useful part: an
    ascending word run `0001 0002 … 001F` sitting immediately after an `rts`. A
    nine-entry slice of it looks exactly like a track table; it runs to 31 and
    keeps going. **A dynamic trace would settle this and static reading will
    not.** The four known answers to *how* a game reaches its tracks (read the
    TOC and filter on CONTROL; name tracks as constants; bypass the OS through
    Akiko; use `cd.device`) do not include "and it reaches this many of them".
    (Sections 1, 8.)

39. **New — is a version-control keyword a better dating instrument than a
    `$VER:`, and how often does one survive into a shipped binary?**
    [Alfred Chicken] carries two expanded RCS `$Header:` keywords, one in each
    game executable:

    ```
    $Header: Hard0:alfred/rcs/amiga.c,v 1.1 93/11/19 16:40:55 JJS Exp $
    $Header: Hard0:alfred/intro/intro/rcs/amiga.c,v 1.1 92/09/29 17:57:54 JJS Exp $
    ```

    A `$VER:` is typed by a person and can say anything; **an RCS keyword is
    stamped by the version control system at check-out**, so it records a real
    event, and it carries four fields where a `$VER:` carries two — a
    filesystem path, a revision, a timestamp **and a user name**. Here it gave
    the build machine's disk, the project layout, the developer's initials, and
    the fact that the two executables are builds of one code base **fourteen
    months apart** — which is what explains why one ships a hardware debugger
    and the other does not.

    No other disc in this set has been checked for RCS or SCCS keywords, because
    until now there was no step that looked for them. `tools/idstrings.py` in
    [Alfred Chicken]'s repository searches for `$Header:`, `$Id:`, `$Revision:`,
    `$Date:`, `$Author:`, `$Log:` and `@(#)` alongside `$VER:`. **Running it
    over the other seventeen images costs nothing and may date several of them
    independently of their PVDs.** (Sections 5, 9.)

40. **New — when a disc has no text at all, what is the string-table model?**
    Four models were known: an offset table into flat strings ([Universe]),
    everything inline in code ([Gunship 2000]), separate text files parsed at run
    time ([Superfrog]), and a relocated page index over position-prefixed record
    chains ([Myth]). **[Alfred Chicken] is a fifth: there is no table, because
    there is no text.**

    Zero prose bytes in every asset file on the disc — 148,157 bytes of level
    archives, tile banks, maps and an icon, and not one byte of it. The 0.607 %
    of the disc that is prose belongs to Commodore's shipped commands (19.6 %),
    a SAS/C runtime and a debugger (78.8 %). **The game's own title exists on
    the disc exactly once in a form a human reads, and it is a 320×184
    four-bitplane picture.**

    The three string-table traps this document lists — length not stored,
    entries repeating and pointing backwards, a zero entry being a kept empty
    slot — **do not apply when there is no table**, and saying so is the result
    rather than a failed check. The measure that *did* apply was the empty-slot
    count, moved onto the thing this disc does have: **72 of 563 tiles across
    seven banks are shipped and never placed by any map**, 12.8 %, with one bank
    throwing away 36.1 %. (Sections 9, 6.)
"""

sub("""    end, which was not run over 156 KB. **An exhaustive bare-stream end search
    over those three runs would settle it, and a stream that decodes with a zero
    checksum there would be a discarded asset from an earlier build of a shipped
    game** — which no disc in this set has produced yet. (Sections 3, 5.)
""", NEW_Q, "open questions 38, 39, 40 added")

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print("patched %s" % P)
for e in edits:
    print("  - %s" % e)
