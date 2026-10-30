# 01 — What this is: six disk sides, one directory that describes a one-megabyte hard-disk volume, and the map that turns five of the sides back into it

*Measure: `sha1sum`/`md5sum` (notes/hashes.txt), `python tools/a2pascal.py IMAGE…` (notes/a2pascal-dir.txt), `python tools/wiz4virt.py SIDE_A … SIDE_E` (notes/wiz4virt.txt); the identity, census and coverage scripts printed in [02](02-the-technical-sheet.md) (notes/side-identity.txt, notes/census.txt, notes/coverage.txt).*

## The object

One ZIP from the owner's collection, `Wizardry-The-Return-of-Werdna---The-Fourth-Scenario_Apple-II_EN.zip`
(477,419 bytes), holding six inner ZIPs dated 2013-02-28, each holding one
TOSEC-named disk image whose modification time is **1996-12-25 00:32**:

| side | image (TOSEC name, shortened) | bytes | SHA-1 |
|---|---|---:|---|
| A | `…(Disk 1 of 6)[PASCAL].dsk` | 143,360 | `3fde308dd34866f726f9827c50644d904b165cb0` |
| B | `…(Disk 2 of 6).dsk` | 143,360 | `3c7d8be09b40204b3148a1b0c79f9e8e83b921af` |
| C | `…(Disk 3 of 6).dsk` | 143,360 | `ec6dd9d3f89ff2ff456bb3706178769d6a314ca3` |
| D | `…(Disk 4 of 6).dsk` | 143,360 | `12bad13f1a617e1ed34ab29564de517d1f8856ad` |
| E | `…(Disk 5 of 6).dsk` | 143,360 | `a10d2765df5d09d6de364a77702bfca67f42d285` |
| F | `…(Disk 6 of 6)[PASCAL].dsk` | 143,360 | `f9aa968f97609038da0f26629e6bd0bb21ed3475` |

Six distinct hashes, **860,160 bytes**. Each image is the standard Apple II
5.25" layout — 35 tracks × 16 sectors × 256 bytes in DOS 3.3 logical order —
and every figure in this repository reads it in Apple Pascal's 512-byte
blocks through the published sector interleave ([03](03-six-sides-and-the-virtual-drive.md)).
Nothing was run or emulated.

The letters A–F are the game's own: the interpreter asks for
`Please Insert SCENARIO Diskette %c` and `Please Restart From Diskette "A"`,
and byte 510 of block 1 on each side holds its number, 1 to 6, in the TOSEC
order. TOSEC tags two of the six `[PASCAL]`; those are the two that carry a
Pascal directory. The other four have none, and that is the first thing this
object has to explain.

## The story in one paragraph

Side A's directory describes a volume named `WIZBOOT` of **2,048 blocks — one
megabyte, 7.3 floppies** — holding 21 files, the last of which is a
747,008-byte file named `WERDNA.11.11.87`. No side holds that volume. Each of
sides A–E holds an *ordered, compacted subset* of its blocks, and the map of
which subset sits where is a 2,048-byte file whose name every account of the
p-System reserves for something else: **`SYSTEM.RELOC`**. Read with that map,
five sides rebuild a 556-block volume in which 239 blocks are carried by more
than one side and **all 239 copies agree byte for byte**; the program inside it
closes (14 segments, 592 procedures, 592 of 592 entry points inside their
segment); and the text file, Huffman-coded with a per-block dictionary written
backwards from the block's end, decodes to **424 messages, 3,175 lines, zero
closure failures**. Everything the directory lists past block 556 — the
script `WERSCRIPT.TEXT`, `ASCII30.TEXT`, `PLAYER.INFO`, five one-block flag
files and the megabyte-filler — is on no side at all. The sixth side is not in
the map either: it is a separate Pascal volume called **`BLANK`**, holding an
animation test program, its data, and a file called **`BLAH`**.

## The split

| what | blocks | bytes | share of 860,160 | chapter |
|---|---:|---:|---:|---|
| boot + identity blocks, A–F | 12 | 6,144 | 0.71 % | [03](03-six-sides-and-the-virtual-drive.md) |
| A–E blocks the map assigns to the virtual volume (excl. 0–1) | 1,293 | 662,016 | 76.96 % | [03](03-six-sides-and-the-virtual-drive.md)–[06](06-the-data-files.md) |
| A–E blocks the map leaves unused — **all zero** | 97 | 49,664 | 5.77 % | [03](03-six-sides-and-the-virtual-drive.md) |
| side F, Pascal volume `BLANK` (directory 4 + four files 274) | 278 | 142,336 | 16.55 % | [07](07-leftovers.md) |
| | **1,680** | **860,160** | **100.00 %** | residue 0 |

Per side (notes/census.txt): A uses 224 + 2 and leaves 54 free; B and C 276 + 2
and 2; D 263 + 2 and 15; E 254 + 2 and 24. Every one of the 97 free blocks is
zero, so no leftover lives *between* files on A–E; the leftovers this object
does have live *inside* files ([07](07-leftovers.md)).

The 1,293 mapped blocks are **544 distinct virtual blocks** (blocks 0–1 of
every side are local and not counted), because the map places some blocks on
several sides: 305 on one side only, 27 on two, 9 on three, 108 on four, 95 on
all five.

## The virtual volume, file by file

| file | virtual blocks | on sides | read here as | depth |
|---|---|---|---|---|
| `SYSTEM.RELOC` | 6..9 | A | the side map | **decoded, closed** ([03](03-six-sides-and-the-virtual-drive.md)) |
| `SYSTEM.INTERP` | 10..35 | A | the custom 6502 p-machine | strings and build comparison ([04](04-the-program-and-the-interpreters.md)) |
| `200.CHARSET` | 36..43 | A | 512 glyphs of 8 × 7 | **rendered** ([06](06-the-data-files.md)) |
| `WERDNA.DATA` | 44..67 | A | 8 save slots + 2 scenario headers | structure ([06](06-the-data-files.md)) |
| `KANA.KEYMAP` | 68..69 | A | Pascal source in its slack | fragment read ([07](07-leftovers.md)) |
| `SYSTEM.PASCAL` | 70..225 | A–E | 14-segment codefile | **container closed**, constants listed ([04](04-the-program-and-the-interpreters.md)) |
| `200.MONSTERS` | 226..285 | A–E | 8 × 7 tile banks; 10 blocks unmapped | tiles identified, composition open ([06](06-the-data-files.md)) |
| `MAZE.INFO` | 286..292 | B–E | 4-byte records | structure only ([06](06-the-data-files.md)) |
| `ASCII.KRN` | 293..410 | A–E | all the game's text | **decoded, closed** ([05](05-the-text.md)) |
| `ASCII.HUFF` | 411..412 | A | the Huffman tree | **decoded** ([05](05-the-text.md)) |
| `SCENARIO.DATA` | 413..556 | A–E | header + records; last block unmapped | header, and **15 level maps drawn** ([06](06-the-data-files.md)) |
| nine more files | 557..2047 | **none** | ghosts of the development volume | [03](03-six-sides-and-the-virtual-drive.md), [07](07-leftovers.md) |

## What it says in the clear, before anything is decoded

* **Its authors**, in the decoded text: *"The Return of WERDNA / The Fourth
  Wizardry Scenario / Andrew Greenberg, Robert Woodhead & Roe R. Adams,III."*
  and *"Wizardry is (c)1979-1987 by Andrew Greenberg, Inc., and Robert
  Woodhead, Inc."* ([05](05-the-text.md)).
* **Its engine**: not Apple Pascal's. The interpreter calls itself
  `WIZARDRY FOR THE APPLE II`, needs 64 K (`WIZARDRY REQUIRES 64 K-BYTES
  MEMORY` in the boot block), and was rewritten in the last week before the
  directory was frozen — 35 development files on the hard-disk volume, dated
  1987-08-13 to 1987-11-11, are still named in the directory's unused slots
  ([07](07-leftovers.md)).
* **Its other platform**: the text file carries *"NEC 9801 Pascal is (c)1985
  by the Foretune co., ltd."*, a language menu `1) English 2) Kana 3) Kanji`,
  and a warning that kanji character names *"will look like tofu on machines
  without the kanji rom"* — in the American Apple II release
  ([05](05-the-text.md)).
* **Its date of manufacture**: every side's block 1 ends with
  `12/22/87` and an eight-digit number ([03](03-six-sides-and-the-virtual-drive.md)).

## Coverage

Every one of the 1,680 physical blocks was assigned a class by the map and
the two directories (notes/coverage.txt), and the classes count *media*
blocks, so a block carried by four sides counts four times:

| class | blocks | bytes | share |
|---|---:|---:|---:|
| **decoded and closed** — boot + identity 12, directories 8, `SYSTEM.RELOC` 4, codefile dictionary 1, `TESTANIM` codefiles 8, character set 8, text + tree 346, all-zero 107 (97 unmapped on A–E, 10 at the tail of `BLAH`) | 494 | 252,928 | **29.40 %** |
| **identified, not decoded** — p-code inside closed segments 537, `SCENARIO.DATA` 214, `ANIM.DATA` 204, monster tiles 99, interpreter 6502 code (three builds) 78, `MAZE.INFO` 28, `WERDNA.DATA` 24, `KANA.KEYMAP` 2 | 1,186 | 607,232 | **70.60 %** |
| not identified | 0 | 0 | 0.00 % |

Residue 0. The level maps' wall arrays (15 records × 480 bytes, read in
[06](06-the-data-files.md)) were decoded after this table was drawn and are
still counted in the `SCENARIO.DATA` row. "Identified" means the bytes are located inside a structure whose
bounds are measured and whose kind is known; it does not mean read. The
largest single item in that row, the p-code, is identified only to the
procedure: no instruction was disassembled.
