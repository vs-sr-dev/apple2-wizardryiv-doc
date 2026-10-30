# 04 — The program and the interpreters: fourteen segments that close only on the virtual volume, a Japanese-capable loader, a cache self-test left in, and three builds of the p-machine

*Measure: `python tools/a2codefile.py _work/virt/SYSTEM.PASCAL --strings` (notes/a2codefile-system-pascal.txt), the same on side A's raw blocks (notes/a2codefile-raw-floppy.txt), on side F's `SYSTEM.PASCAL` (notes/a2codefile-testanim.txt) and on `BLAH` blocks 0–3 (notes/a2codefile-blah.txt); interpreter strings (notes/interp-strings.txt).*

## Engine

There is no third-party engine in these bytes. The program is UCSD Pascal
p-code in an Apple Pascal codefile, and the machine that runs it is Sir-Tech's
own: `SYSTEM.INTERP`, 13,312 bytes of 6502 that boots from its own boot block,
names itself `WIZARDRY FOR THE APPLE II`, and replaces the Apple Pascal
operating system entirely — there is no `SYSTEM.APPLE` and no
`SYSTEM.LIBRARY` on any side, and the only Apple code on the set is the stock
boot block of sides B–E that can never find what it looks for
([03](03-six-sides-and-the-virtual-drive.md)). The development directory
names the interpreter's own sources ([07](07-leftovers.md)): `IPROC`,
`IMACRO`, `ILOCALS`, `ILOCAT`, `ISTANDARD`, `IINIT`, `ITABLES`, `IEQUATE`,
`VIRTDRIV`, `OTHERDISK`, `RWTS2` — procedure calls, macros, locals, standard
procedures, initialisation, tables, equates, the virtual drive, the other
disk, and a replacement for DOS's sector-level routine.

## `SYSTEM.PASCAL`: the container, read on the right volume

On the volume `SYSTEM.RELOC` rebuilds:

```
slot  name      block   bytes  seg#  mtype ver  procs  inside  tail-ok
  0   WIZARDRY     1    7270     1     2    2     88      88   yes
  1   COMBAT      16     992     7     2    2     10      10   yes
  2   CUTIL       18    6970     8     2    2     51      51   yes
  3   CASTASPE    32    5116     9     2    2     36      36   yes
  4   SWINGASW    42    3302    10     2    2     27      27   yes
  5   CINIT       49    6878    11     2    2     42      42   yes
  6   KANJIREA    63    4174    12     2    2     28      28   yes
  7   UTILITIE    72    5528    13     2    2     32      32   yes
  8   SHOPS       83    3042    14     2    2     19      19   yes
  9   SPECIALS    89   11316    15     2    2     97      97   yes
 10   CAMP       112    9418    16     2    2     73      73   yes
 11   RUNNER     139    8680    17     2    2     61      61   yes
 12   DOCOPY     131    1952    18     2    2     13      13   yes
 13   DOCACHE    135    1838    19     2    2     15      15   yes
segments 14   code bytes 76476   procedures 592   pointers inside their segment 592 of 592
```

Against side A's blocks as they lie, the same dictionary gives 213 of 755
(notes/a2codefile-raw-floppy.txt): the two figures are the whole argument of
[03](03-six-sides-and-the-virtual-drive.md) in one line each.

**The slot order is not the file order.** `RUNNER` is slot 11 but its code is
last, at block 139, after `DOCOPY` (131) and `DOCACHE` (135), which are slots
12 and 13. Slots are assigned by the compiler; the code order is the order the
segments were laid into the file — so `RUNNER` was placed after the two segments
numbered after it, which is what a segment rebuilt and re-linked last looks
like. That is a reading of an ordering, not a measurement of a history.

Segment numbers are 1 and 7..19: 2..6 are reserved to the p-System, as on the
PC volume. Every `seginfo` carries version 2 and machine type 2; side F's
`TESTANIM` carries version 6.

### Against the IBM PC *Wizardry* (pc-wizardry-doc, chapter 07)

| PC *Proving Grounds* (1987) | Apple *Return of Werdna* | |
|---|---|---|
| `WIZARDRY` 82 procs | `WIZARDRY` 88 | outer block |
| `COMBAT` `CUTIL` `CASTASPE` `SWINGASW` `CINIT` | same five | combat, unchanged in name |
| `KANJIREA` 50 procs | `KANJIREA` 28 | the loader |
| `UTILITIE` `SHOPS` `SPECIALS` `CAMP` `RUNNER` | same five | |
| `CASTLE` `ROLLER` `REWARDS` `GAMEUTIL` | **absent** | no town hub, no character roller — Werdna is not rolled |
| — | **`DOCOPY` `DOCACHE`** | new: the disk copier and the cache |
| 16 segments, 659 procs | 14 segments, 592 procs | |

`SPECIALS` grows from 39 to **97** procedures, the largest segment by far
(11,316 bytes): *Werdna*'s special squares — riddles, pools, altars, the
Cosmic Cube — are code, and they are on all four dungeon sides.

## What the p-code says in its constants

The `A6` (load-string-constant) census finds few strings, because the text
lives in `ASCII.KRN` ([05](05-the-text.md)). What it does find:

**`KANJIREA` — a loader that still speaks Japanese.**

```
HUFF   .CHARSET   200   .MONSTERS   200   200   400   200   400
ASCII.KRN   IS.TITLE   200.TITLE   400.TITLE
ASCII.KRN   KANA.KRN   KANJI.KRN   SCENARIO.DATA   SCENARIO.DATA   KANA.KEYMAP
```

The file names are assembled from a resolution prefix and a suffix:
`200.CHARSET`/`400.CHARSET`, `200.MONSTERS`/`400.MONSTERS`,
`200.TITLE`/`400.TITLE` — 200-line and 400-line displays, the second being
the NEC PC-9801's. The message file is chosen from three languages,
`ASCII.KRN`, `KANA.KRN`, `KANJI.KRN`, and the decoded text still has the menu
for it ([05](05-the-text.md)). Of all these names, the Apple volume carries
`200.CHARSET`, `200.MONSTERS`, `ASCII.KRN`, `SCENARIO.DATA` and
`KANA.KEYMAP`. `IS.TITLE` is another probe-by-filename flag, and it is absent:
the Apple version has no title picture to show.

**`DOCACHE` — the cache, and its self-test.**

```
PRESS RETURN
Testing Cache against Disk
Cache <> Disk at block
SYSTEM.PASCAL  CASTASPE  SWINGASW  CINIT  CUTIL  COMBAT  RUNNER  CAMP
ASCII.KRN  KANA.KRN  KANJI.KRN  UTILITIE  SPECIALS  SHOPS  KANJIREA
200.MONSTERS  400.MONSTERS
```

The list is what gets copied into extra memory (the text's *"Now loading
program segments into extra memory. This improves the performance of the
program."*), and the first three strings are **a verification routine that
compares the cache with the disk block by block and reports the first block
that differs** — a developer's check, shipped in the product and reachable
only through whatever calls it.

**`SPECIALS` — `SPCL IND ERR`**, and `RUNNER` — `IND ERR`: index-error
guards on the special-square tables. **`CAMP` and `RUNNER`** each carry a
sixteen-character constant, `>!$#&*<?BCPCODG@` and `CBA123456789MLBC`, which
read as key or symbol lookup tables; they are listed, not resolved. `CAMP`
also carries `TREBOR`, `SHOPS` carries `WERDNA` and `WERDNA.DATA`, and
`**ERR**` occurs 22 times across nine segments.

## The interpreters: three builds, one message region

Three 26-block 6502 interpreters are on the set — the shipped one on side A
(dated 87-11-12), one on side F (87-11-04), and one inside side F's `BLAH`
(blocks 4..29 of that file, no date of its own). Byte differences:
A–F 10,608, A–`BLAH` 10,733, F–`BLAH` 5,129. All three place their message
strings in the same region, from `0x2F00`, and that region is where they
differ most legibly:

| `BLAH` | side F, 87-11-04 | side A, 87-11-12, shipped |
|---|---|---|
| `S#%h %x P#%h %x I=%d IPC=%x MP=%x` | — | — |
| `SP %b %x %x %x %x %x %x` | — | — |
| `NI %h %h %h %c #%h S%h/P%h Pc%h NP=%x` | — | — |
| `Execution Error %h` | `Execution Error %h` | `A Serious Problem Has Occurred` |
| `System I/O Error %h` | `System I/O Error %h` | `A Problem Has Occurred While Reading` |
| `Unimplemented P-code %h` | `Unimplemented P-code %h` | — |
| `S=%h P=%h I=%d PC=%x` | `S=%h P=%h I=%d PC=%x` | **`Note: %h %h %h %h %h`** |
| `Unit %h Block %d` | `Unit %h Block %d` | `The Diskette In Drive %h` |
| `Please Insert Diskette %c` | same | `Please Insert SCENARIO Diskette %c` |
| `Diskette %c Block %d` | same | `Diskette "%c"` |
| `Bad Address Field` / `Bad Data Field` | same | — |
| — | — | `Please Restart From Diskette "A"` |

Read top to bottom, it is the interpreter going from a debugging p-machine —
with trace lines labelled `IPC`, `MP` and `NP`, which are the names of the
UCSD p-machine's interpreter program counter, mark-stack pointer and heap
pointer — to one that tells the player only
that *a serious problem has occurred*. **The shipped build kept the numbers
and dropped their labels**: `S=%h P=%h I=%d PC=%x` became
`Note: %h %h %h %h %h`, a register dump the player is meant to read out to
Sir-Tech over the phone. That last clause is an inference from the strings;
the code that formats it was not traced.

The tail strings `SYSTEM.PASCAL`, `WIZARDRY FOR THE APPLE II`,
`ERROR: SYSTEM.PASCAL NOT FOUND`, `TYPE <RETURN> TO RESTART` are identical in
all three, at the same offsets.

## `TESTANIM`: two builds of a test program

Side F's `SYSTEM.PASCAL` is not *Wizardry*: it is a one-segment codefile named
**`TESTANIM`**, 1,134 bytes, 14 procedures, 14 of 14 inside, dated
**87-12-08** — four weeks *after* the game directory's date and two weeks
before the duplication stamp. `BLAH` blocks 0–3 hold another `TESTANIM`,
1,188 bytes, 14 procedures, 14 of 14 inside. Both carry the same three
constants:

```
ANIM.DATA    HAS.CACHE    DISK.280
```

— its data file, the cache flag the game also probes, and a probe name the
game does not use. Chapter [07](07-leftovers.md) is the rest of side F.
