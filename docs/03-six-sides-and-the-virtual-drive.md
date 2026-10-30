# 03 — Six sides and the virtual drive: a 2,048-block directory on a 280-block floppy, and the file called `SYSTEM.RELOC` that is really a map

*Measure: `python tools/a2pascal.py IMAGE` (notes/a2pascal-dir.txt), `python tools/a2pascal.py --refuse SIDE_B…SIDE_E` (notes/a2pascal-refuse.txt), `python tools/wiz4virt.py SIDE_A … SIDE_E` (notes/wiz4virt.txt, notes/wiz4virt-extract.txt), `python tools/psystem.py _work/virtual.vol` (notes/psystem-virtual.txt), identity script (notes/side-identity.txt).*

## Geometry, and the one public fact this chapter leans on

An Apple II `.dsk` is 35 × 16 × 256 = 143,360 bytes in DOS 3.3 logical-sector
order. Apple Pascal addresses the same disk as 280 blocks of 512 bytes, block
*k* of a track being the DOS sector pair

```
(0,14) (13,12) (11,10) (9,8) (7,6) (5,4) (3,2) (1,15)
```

That interleave is public and was not derived. What it buys is checkable: on
side A it puts a valid volume header exactly at block 2, and on sides B–E it
puts code segments exactly on block boundaries — the 512-aligned matches in
the rest of this chapter would not exist under any other ordering.

## Side A: the directory, and the volume it describes

```
volume name       : WIZBOOT  (7 characters)
blocks declared   : 2048   <- the medium holds 280; declared/medium = 7.3143
files declared    : 21
dlastboot         : 0xAEBB -> 87-11-11
```

Twenty-one entries chain from block 6 to block 2,048 with **no gap and no free
block** — a volume that is full by construction. The first six files fit on
the floppy; the seventh straddles its end; the other fourteen begin past it:

```
  #  name             kind      first  next blocks   date
  1  SYSTEM.RELOC     datafile      6    10      4   87-10-16
  2  SYSTEM.INTERP    codefile     10    36     26   87-11-12
  3  200.CHARSET      datafile     36    44      8   87-09-26
  4  WERDNA.DATA      datafile     44    68     24   87-09-17
  5  KANA.KEYMAP      datafile     68    70      2   87-05-15
  6  SYSTEM.PASCAL    codefile     70   226    156   87-11-11
  7  200.MONSTERS     datafile    226   286     60   84-11-07   BEYOND MEDIUM by 6
  8  MAZE.INFO        infofile    286   293      7   84-11-07   BEYOND MEDIUM
  9  ASCII.KRN        datafile    293   411    118   87-11-11   BEYOND MEDIUM
 10  ASCII.HUFF       datafile    411   413      2   87-11-11   …
 11  SCENARIO.DATA    datafile    413   557    144   87-11-11
 12  ASCII.SECS       datafile    557   561      4   87-11-11
 13  ASCII30.TEXT     textfile    561   571     10   87-10-23
 14  PLAYER.INFO      datafile    571   576      5   87-11-11
 15  IS.APPLE         datafile    576   577      1   87-09-09
 16  LINES.24         datafile    577   578      1   87-09-09
 17  HAS.CACHE        datafile    578   579      1   87-09-09
 18  HAS.STROPS       datafile    579   580      1   87-09-09
 19  HAS.KRNSRCH      datafile    580   581      1   87-10-05
 20  WERSCRIPT.TEXT   textfile    581   589      8   87-10-15
 21  WERDNA.11.11.87  datafile    589  2048   1459   87-11-11   BEYOND MEDIUM by 1459
```

`dlastbyte` is 512 on all 21. The directory region (blocks 2..5, 78 slots)
holds 56 more records past `dnumfiles` — chapter [07](07-leftovers.md) reads
them as the development diary they are.

**And the content check fails on the floppy.** The `SYSTEM.PASCAL` segment
dictionary at block 70 is intact, but read naively against side A's blocks
only the first segment ends with its own procedure dictionary:

```
python tools/a2codefile.py _work/vol1/SYSTEM.PASCAL            (blocks 70..225 of side A as they lie)
segments 14   procedures 755   pointers inside their segment 213 of 755     tail-ok 2 of 14
```

So side A is not the first 280 blocks of `WIZBOOT` either. Sides B–E, for their
part, have no directory at all, and the reader refuses them for the right
reason (notes/a2pascal-refuse.txt):

```
REFUSED: dfirstblk is 34985, not 0      [sides B, C, D, E]
```

What they do have is code: the same nine `SYSTEM.PASCAL` segments, packed
contiguously from block 2 to block 118, byte-identical on all four — found by
looking for 512-aligned positions where a segment of the dictionary's length
ends with its own segment number and a procedure count whose self-relative
pointers all land inside it.

## The arithmetic that gave the scheme away

Placing each segment where it was found against where the dictionary says it
is, the offsets are not one constant but a running total of *what is missing*:

| segment | virtual block | found on | physical | offset | what precedes it on that side and not in the volume |
|---|---:|---|---:|---:|---|
| `WIZARDRY` | 71 | A | 71 | 0 | — |
| `KANJIREA` | 133 | A | 86 | −47 | `COMBAT`…`CINIT` (2+14+10+7+14 = 47) |
| `CAMP` | 182 | A | 112 | −70 | + `SPECIALS` (23) |
| `COMBAT` | 86 | B–E | 2 | −84 | virtual 2..85 (84) |
| `UTILITIE` | 142 | B–E | 49 | −93 | + `KANJIREA` (9) |
| `SPECIALS` | 159 | B–E | 60 | −99 | + `SHOPS` (6) |
| `RUNNER` | 209 | B–E | 102 | −107 | + `DOCOPY`, `DOCACHE` (4+4) |

Every side holds an **ordered, compacted subset of the virtual blocks**. The
subsets had to be written down somewhere. A search of all six sides for the
word pairs this table implies — (0, 86), (133, 159), (86, 47) and their
neighbours — found (0, 86) followed by (133, 86, 26) at block 6 of side A: the
first block of `SYSTEM.RELOC`.

## `SYSTEM.RELOC`: the map

2,048 bytes of 16-bit little-endian words (`tools/wiz4virt.py`):

```
word 0                  2      (constant; not resolved)
side 1, 12 extents      (0,0,86) (133,86,26) (182,112,27) (225,139,16) (246,155,4) (293,159,7)
                        (301,166,39) (353,205,4) (371,209,1) (404,210,3) (408,213,7) (550,220,6)
side 2, 17 extents      (0,0,2) (86,2,47) (142,49,11) (159,60,42) (209,102,27) …
side 3, 24 extents      …
side 4, 25 extents      …
side 5, 28 extents      …
0                       end of list, at word 329 (byte 658)
```

Each triple is (virtual first block, physical first block, count). Three
checks before anything is assembled, all passed on all five sides:

* the extents of each side tile its physical blocks from 0 with **no gap and
  no overlap** — side A ends at 226, B and C at 278, D at 265, E at 256;
* no side exceeds 280;
* the virtual extents of each side ascend and do not overlap.

Then the test the map cannot pass by construction — **every virtual block that
more than one side carries is compared byte for byte**:

```
virtual blocks held : 546 distinct (0..555)
held by >1 side     : 239   byte-identical: 239   CONFLICTS: 0
```

Two hundred and thirty-nine blocks, written to as many as five different
sides, agree to the byte. That is the closure. The rebuilt volume is then
read by `tools/psystem.py`, written for the IBM PC *Wizardry* in an earlier
session and not modified for this one, which agrees on every field:
`WIZBOOT`, 21 files, chain ok, 2,048 declared, 556 present
(notes/psystem-virtual.txt).

Bytes 658..2,047 of `SYSTEM.RELOC` are not zero: after a run of zeros they
hold `FF FF 00 00` repeated, with occasional phase shifts — fill, not table
(notes/wiz4virt.txt prints where the list ends).

### What the map puts where

| side | carries (virtual) | i.e. |
|---|---|---|
| A | 0..85, 133..158, 182..208, and scattered pieces of 225..414, 550..555 | boot, directory, map, interpreter, character set, save file, the "town" segments (`WIZARDRY`, `KANJIREA`, `UTILITIE`, `SHOPS`, `CAMP`, `DOCOPY`, `DOCACHE`), **the whole Huffman tree**, the first two blocks of `SCENARIO.DATA` |
| B–E | 86..132, 142..152, 159..200, 209..227 on all four (`RUNNER` is 209..225), then each its own selection of 228..555 | the nine "dungeon" segments (`COMBAT`, `CUTIL`, `CASTASPE`, `SWINGASW`, `CINIT`, `UTILITIE`, `SPECIALS`, `CAMP`, `RUNNER`), `MAZE.INFO`, and the monster tiles, text and scenario records that side's levels need |

`UTILITIE` and `CAMP` are on every side. The text tree `ASCII.HUFF` (virtual
411–412) is on side A only, which is consistent with its being read once at
boot and kept in memory; `MAZE.INFO` is on B–E only.

### Ten blocks of `200.MONSTERS` and one of `SCENARIO.DATA` are on no side

Virtual 245, 250, 251, 270, 271, 279, 280, 283, 284, 285 (inside
`200.MONSTERS`) and 556 (the last block of `SCENARIO.DATA`) are carried by no
side. The extractor zero-fills them and says so (notes/wiz4virt-extract.txt).
Nothing in the shipped program can read them, so they are, as far as these
bytes can tell, unused slots in the volume.

## The ghosts: nine files that exist only as directory entries

Everything from virtual block 557 onwards — 1,491 blocks, 72.8 % of the
declared volume — is on **no side**:

```
ASCII.SECS  ASCII30.TEXT  PLAYER.INFO  IS.APPLE  LINES.24  HAS.CACHE
HAS.STROPS  HAS.KRNSRCH  WERSCRIPT.TEXT  WERDNA.11.11.87
```

Five of them do not need content to work. The outer segment `WIZARDRY`
carries their names as string constants, in one run (notes/a2codefile-system-pascal.txt):

```
+06691  IS.APPLE   +06711  LINES.24   +06733  HAS.CACHE   +06755  HAS.STROPS
+06777  SYSTEM.RELOC   +06803  HAS.KRNSRCH   +06827  MAZE.INFO   +06861  SYSTEM.RELOC
```

— the same probe-by-filename table the IBM PC *Wizardry* carries, where a
file's *presence in the directory* is the boolean. On the PC disk, `IS.APPLE`
was absent and the program learned it was not on an Apple; here all five
flags are present in the directory, so the program learns it **is** on an
Apple, with 24 lines, a cache, string operations, and the kernel search the
text index needs ([05](05-the-text.md)). Their blocks are never read, so the
map never placed them. `SYSTEM.RELOC` is in the same table twice — on the PC
volume it was a name the program asked for and did not find; here it is the
file that makes the volume exist.

The other ghosts are files the shipped program does not use: `WERSCRIPT.TEXT`
(an 8-block text file — *Werdna script*, by its name, and its content is not
on these sides), `ASCII30.TEXT`, `ASCII.SECS`, `PLAYER.INFO`, and the
1,459-block `WERDNA.11.11.87`, whose span covers every block the stale
development entries of [07](07-leftovers.md) once occupied.

## Boot blocks and identity blocks

Blocks 0–1 are local to each side and outside the map's comparison.

**Sides A and F** carry a Wizardry boot (`SYSTEM.INTERP`,
`WIZARDRY REQUIRES 64 K-BYTES MEMORY`, `CAN NOT RUN THE PROGRAM!`,
`PLEASE RESTART FROM ANOTHER DISKETTE`). The two are identical except for
three bytes, which are the next point.

**Sides B–E** carry, with block 0 byte-identical on all four, a stock Apple Pascal boot:
`MUST BOOT FROM SLOT 4, 5 OR 6`, `NO FILE SYSTEM.APPLE`,
`COPYRIGHT APPLE COMPUTER, INC., 1984, 1985 C.LEUNG`. It looks for a file on
a directory these sides do not have — so it can never succeed, which is
harmless: the player is never asked to boot them.

**Every side's block 1 ends with an identity stamp** (bytes 480–495 ASCII,
byte 510 the side number):

| side | stamp | byte 510 |
|---|---|---:|
| A | `12/22/87` `00000040` | 1 |
| B | `12/22/87` `00000129` | 2 |
| C | `12/22/87` `00000262` | 3 |
| D | `12/22/87` `00000252` | 4 |
| E | `12/22/87` `00000071` | 5 |
| F | `12/22/87` `00000051` | 6 |

The date is common; the eight-digit numbers are all different. A per-copy
serial written by the duplication process would differ between *sets* but
match within one; a per-side counter would differ as these do. This object
cannot tell which, or whether the six images came from one boxed copy — TOSEC
sets are often assembled. What it can tell is the date: **22 December 1987**,
six weeks after the directory's `11/11/87` and the file named for that day.
`wiz4virt.py` reads byte 510 to know which side it was handed, and refuses
any input set without side 1.
