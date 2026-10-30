# 07 — Leftovers: a development diary in a directory, an assembler listing inside the monster pictures, the Pascal editor inside the maze table, eight save games that remember their testers, and a sixth side called `BLANK`

*Measure: notes/stale-directory.txt, notes/a2pascal-dir.txt (side F), notes/data-files.txt, notes/interp-strings.txt, notes/a2codefile-testanim.txt, notes/a2codefile-blah.txt; the slack census script in [02](02-the-technical-sheet.md).*

Nothing in this chapter is needed to play the game. All of it shipped.

## 1. The development diary, in side A's directory

The directory region has 78 slots; the header and 21 live entries use 22. The
other 56 are not empty. Apple Pascal does not clear a slot when a file is
removed — the entries below it move up and the old last record stays where
it was — so the slots past `dnumfiles` are layers of the directory as it
stood on the development machine (notes/stale-directory.txt). They hold
**35 distinct file names, dated 13 August to 11 November 1987**, at block
numbers up to 1,971 — positions that exist only on the 2,048-block volume:

| date (1987) | files |
|---|---|
| 08-13 | `SHOWDICT.TEXT`, `SHOWDICT.CODE` |
| 11-05 | `IPROC.TEXT`, `OLDEINTERP.CODE`, `NEWEBOOT.CODE`, `IMACRO.TEXT` |
| 11-06 | `NEWEINTERP.CODE`, `UNIT13.TEXT`, `NEWBOOT.CODE`, `NEWTEST` |
| 11-07 | `ILOCALS.TEXT` |
| 11-09 | `INTERP1.CODE`, `TEST1`, `WIZGRAPH.TEXT`, `MONSTGRAPH.TEXT`, `NEWBOOT.TEXT`, `ILOCAT.TEXT`, `ISTANDARD.TEXT` |
| 11-10 | `IINIT.TEXT`, `IINIT.CODE`, `INTERP7.CODE`, `TEST7`, `NEWMESSG.TEXT` |
| 11-11 | `INTERP.CODE`, `ITABLES.TEXT`, `VIRTDRIV.TEXT`, `OTHERDISK.TEXT`, `OLDTABLES.TEXT`, `MESSAGES.TEXT`, `MESSAGES.CODE`, `RWTS2.TEXT`, `TEST14`, `INITGRAPH.TEXT`, `IEQUATE.TEXT`, and a length-0 copy of `WERDNA.11.11.87` |

The sizes say what the names suggest. **`TEST1`, `TEST7`, `TEST14`, `NEWTEST`,
`INTERP1.CODE`, `INTERP7.CODE` and `OLDEINTERP.CODE` are 26 blocks each, and
`INTERP.CODE`, `NEWEINTERP.CODE` 27** — the size of the shipped `SYSTEM.INTERP` (26): these
are numbered builds of the interpreter, made one week before the directory was
frozen. The `I`-prefixed `.TEXT` files are its source modules (procedures,
macros, locals, standard procedures, initialisation, tables, equates), `VIRTDRIV`
and `OTHERDISK` are presumably the virtual drive of [03](03-six-sides-and-the-virtual-drive.md),
`RWTS2` a disk routine, `WIZGRAPH`/`MONSTGRAPH`/`INITGRAPH` the graphics,
`MESSAGES`/`NEWMESSG` the interpreter's messages of [04](04-the-program-and-the-interpreters.md),
and `NEWEBOOT`/`NEWBOOT` the boot block. `SHOWDICT` — three months older than
the rest — reads as a tool to show a codefile's segment dictionary.

Two layers of the same list are visible (slots 46–55 and 59–66 repeat
`OLDTABLES` … `IEQUATE` with different block numbers), and slots 56–58 and
67–77 hold fourteen copies of the `IEQUATE.TEXT` record with its length byte
set to 0. Every stale entry dated 11-06 or later lies inside blocks
589..2,047 — **the span the live directory gives to one file named
`WERDNA.11.11.87`**; the six older ones (`SHOWDICT` ×2, `IPROC`, `OLDEINTERP`,
`NEWEBOOT`, `IMACRO`) lie at 418..588, where `SCENARIO.DATA` and the ghost
files now are. Whoever froze the volume deleted the development files and
covered most of the space they had used with a single date-named file.

## 2. The ghosts in the live directory

Of the 21 live entries, ten have no blocks on any side
([03](03-six-sides-and-the-virtual-drive.md)). Five are flags that work by
existing. The other five are a development volume's files that a player's
volume did not need: **`WERSCRIPT.TEXT`** (4,096 bytes, 87-10-15 — a text
file named for Werdna's script), `ASCII30.TEXT` (87-10-23), `ASCII.SECS`,
`PLAYER.INFO` and `WERDNA.11.11.87` itself. Their names shipped; their
contents did not. `ASCII.SECS` sits immediately after `ASCII.HUFF` and before
the flags, which is where an older index of the text's sections would sit;
the shipped program does not use it, because the index is now block 116 of
`ASCII.KRN` ([05](05-the-text.md)).

## 3. An assembler listing inside the monster pictures

`200.MONSTERS` is a bank of 8-byte tiles ([06](06-the-data-files.md)), and
the slots no picture uses were written from a dirty buffer. 257 of its 3,840
tiles are entirely printable text, and the text is **a 6502 assembler
listing** — address column, object bytes, source — from virtual blocks 234 to
282 (notes/data-files.txt and the slack census in [02](02-the-technical-sheet.md)):

```
009A|                               .LIST
009A|                       ;----------------------------------------------
009A| 0020                  FormatCount     .equ    20
009A|                       ;****** WRITE ROUTINES ************************
00B3| 20 ****
00D0| A9 FF
0100| 4A
0114| 88
```

and, in shorter fragments: `; Read4`, `Read44Byte`, `WriteB9`, `cycles`,
`Sector`, `; Moto[r]`, `lda disk+mo[tor]`, `; Set out[put]`, `; Is pr[otected]`,
`lda #0D`, `sta %1`, `sta %2`, `iny`, `sub ; Subt[ract]`, `; Push word on`,
`; (6 + 15)`, `:= Op1`, `S in this file`. Bracketed letters are where the
fragment is cut by a tile boundary. A `FormatCount`, write routines, 4-and-4
byte reads, motor control and a write-protect test: **this is the source
of a disk formatter and writer** — what *Make Scenario Diskette* needs
(*"Formatting blank Diskette..."*, [05](05-the-text.md)), and what the stale
`RWTS2.TEXT` would contain. The `sta %1`/`sta %2` and `sub ; Subt` lines,
macro parameters and a subtract, belong to the interpreter's own macros
(`IMACRO`). It is not enough to reassemble anything; it is enough to say what
was on the developer's screen when the pictures were saved.

## 4. Pascal source in `KANA.KEYMAP`, and the Pascal editor in `MAZE.INFO`

At `0x1AC` of `KANA.KEYMAP`, in the UCSD text-file format (`DLE` plus an
indent byte, then the line):

```
[SP]ECIAL,
                 STAIRS,
                 PIT,
                 CHUTE,
                 TURNRANDOM,
                 SDARKNESS,
                 STELEPORT,
                 DAMAGE,
```

— part of the enumerated type of special squares. From outside these bytes:
the circulated source of *Proving Grounds* names its square types `NORMAL,
STAIRS, PIT, CHUTE, SPINNER, DARK, TRANSFER, OUCHY, BUTTONZ, ROCKWATE, FIZZLE,
SCNMSG, ENCOUNTE`. This fragment has the same second, third and fourth, and
then **`TURNRANDOM`, `SDARKNESS`, `STELEPORT`, `DAMAGE`** — the same ideas
renamed (spinner, darkness, teleport, ouch), *Werdna*'s own list.

In `MAZE.INFO`'s slack, at `0xF8`..`0x1F5` and `0xDBB`..`0xDE8`, are strings
of the **Apple Pascal screen editor**:

```
… the editor.
* already exists. Delete before S(ave?  -->
2    Y(es to delete old file before saving new one.
1    N(o  to delete old file after saving new one.
…ttern not in the file.
No old pattern.
```

The file was written from memory the editor had been using.

## 5. Stale bytes behind short names

* **`WERDNA.DATA`**: eight save slots with three empty group-name strings each,
  and behind the zero length `ENTELECHY FUFF`, `FLACKECHY FUFF`,
  `LYCURGUSY FUFF`, `GAS CLOUDSSTSS`, `LVL 1 PRIESTSF`, `ZOMBIESSY FUFF`,
  `BLACK DRAGON` — the monsters someone summoned while testing
  ([06](06-the-data-files.md)).
* **`SCENARIO.DATA`**, header, behind the class and status names:
  `MAGE` + `.LIBR`, `ASLEEP` + `IBR` — the tail of `SYSTEM.LIBRARY`, a file
  the shipped game does not have — and twenty stale bytes behind the title.
* **`200.MONSTERS`** block 0, tile 30: `ROTECTED` (the tail of a word ending
  in *-protected*), and at the end of the block 6502 code (`A2 00 BD F9 08 F0
  07 91 0E C8 C8 E8 D0 F4 60`: `LDX #0`, `LDA $08F9,X`, `BEQ`, `STA ($0E),Y`,
  `INY`, `INY`, `INX`, `BNE`, `RTS` — a loop that copies a zero-terminated
  string from `$08F9` into every second byte of a buffer).
* **`ASCII.KRN`** block 117: 512 bytes the index never addresses, which do not
  decode as lines under the shipped tree — residue of an earlier text file or
  an earlier tree.
* **`SYSTEM.RELOC`** after its 329 words: a `FF FF 00 00` fill pattern.

## 6. Debugging code that shipped

The `DOCACHE` segment's **"Testing Cache against Disk" / "Cache <> Disk at
block"** check ([04](04-the-program-and-the-interpreters.md)), and the
interpreter's diagnostic dump, kept as five unlabelled numbers after
*"A Serious Problem Has Occurred"*.

## 7. Side F: a volume called `BLANK`

The sixth side is stamped `12/22/87` `00000051`, side 6, by the same process
as the other five, and boots the same Wizardry boot block. It is not in
`SYSTEM.RELOC`: **the game never asks for it**. Its directory:

```
volume name       : BLANK
blocks declared   : 280
dlastboot         : 84-11-07
  1  ANIM.DATA        datafile      6   210    204   104448   84-11-07
  2  SYSTEM.PASCAL    codefile    210   214      4     2048   87-12-08
  3  SYSTEM.INTERP    codefile    214   240     26    13312   87-11-04
  4  BLAH             datafile    240   280     40    20480   87-11-04
stale slot 5          BLAH        240   280                   87-11-04
```

A volume named *blank*, full to the last block, holding:

* **`SYSTEM.PASCAL`** = `TESTANIM`, a one-segment animation test player, dated
  **8 December 1987** — after the game was frozen — which loads `ANIM.DATA` and
  probes `HAS.CACHE` and `DISK.280` ([04](04-the-program-and-the-interpreters.md));
* **`ANIM.DATA`**, 53 frames behind a `(block, offset)` index, dated with the
  same `84-11-07` the volume's last boot carries (and that `200.MONSTERS` and
  `MAZE.INFO` carry on side A) — the date an Apple Pascal system keeps when
  nobody sets the clock;
* **`SYSTEM.INTERP`**, the 87-11-04 interpreter with the developer's error
  messages;
* **`BLAH`**: an older `TESTANIM` (1,188 bytes against 1,134), **a third
  interpreter build with the p-machine trace formats** (`S#%h %x P#%h %x I=%d
  IPC=%x MP=%x`, `NI %h %h %h %c #%h S%h/P%h Pc%h NP=%x`), and ten zero blocks.

Read together: the sixth side of the set was a working disk for an
animation player, built with the game's own interpreter and boot, and it was
duplicated as it stood. What `ANIM.DATA` animates is not decoded; its
frames do not match any block of the game.

## 8. The calendar

| date | where |
|---|---|
| 84-11-07 | `200.MONSTERS`, `MAZE.INFO` (A); `ANIM.DATA` and the last boot of `BLANK` (F) — the unset-clock date |
| 87-05-15 | `KANA.KEYMAP` |
| 87-08-13 | `SHOWDICT` (stale) |
| 87-09-09 | the four flag files |
| 87-09-17 … 10-23 | `WERDNA.DATA`, `200.CHARSET`, `HAS.KRNSRCH`, `WERSCRIPT.TEXT`, `SYSTEM.RELOC`, `ASCII30.TEXT` |
| 87-11-04 | side F's interpreter and `BLAH` |
| 87-11-05 … 11-11 | the interpreter rewrite (stale entries) |
| 87-11-11 | `SYSTEM.PASCAL`, the text, the scenario, the volume's last boot, `WERDNA.11.11.87` |
| 87-11-12 | `SYSTEM.INTERP` — one day after the volume's last boot |
| 87-12-08 | `TESTANIM` on side F |
| 87-12-22 | every side's identity stamp |
| 96-12-25 | the six image files' modification time in this dump |
| 2013-02-28 | the inner ZIPs |

The shipped interpreter is dated a day after the directory that lists it
was last booted: it was written to the volume by another system, or with the
clock a day ahead. Either way it is the last thing to change before the
masters were made.
