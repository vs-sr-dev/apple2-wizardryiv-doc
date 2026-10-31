# apple2-wizardryiv-doc

*Wizardry IV: The Return of Werdna* — Apple II, Sir-Tech, 1987 — read byte by
byte from six disk sides (6 × 143,360 bytes, six distinct hashes), in which
the boot side's directory describes **a one-megabyte development volume that
no floppy holds**, a file the p-System reserves for something else —
`SYSTEM.RELOC` — turns out to be **the map that spreads it over five sides**,
the game's text is Huffman-coded behind a dictionary written backwards from
the end of every block, and the sixth side is a separate volume named
**`BLANK`** that holds an animation test program and a file called **`BLAH`**.

**No product bytes are in this repository** — formats, hashes, figures, the
commands that reprint them, and short quotations. The images, the extracted
files, the renders and the decoded text are not published.

## The short card

| | |
|---|---|
| **what it is** | six Apple II 5.25" sides, A–F, TOSEC-named; A and F carry Apple Pascal directories, B–E carry none. The game runs on Sir-Tech's own 6502 p-machine (`WIZARDRY FOR THE APPLE II`), not on Apple Pascal. [01](docs/01-what-this-is.md) |
| **the virtual drive** | side A's directory: `WIZBOOT`, **2,048 blocks** on a 280-block medium, 21 files. `SYSTEM.RELOC` lists, per side, (virtual, physical, count) extents; read with it, sides A–E rebuild blocks 0..555, and **239 blocks carried by more than one side agree byte for byte — 239 of 239**. [03](docs/03-six-sides-and-the-virtual-drive.md) |
| **the ghosts** | ten directory entries are on no side: `WERSCRIPT.TEXT`, `ASCII30.TEXT`, `PLAYER.INFO`, … and a 747,008-byte `WERDNA.11.11.87`. Five are flags (`IS.APPLE`, `LINES.24`, `HAS.CACHE`, `HAS.STROPS`, `HAS.KRNSRCH`) that work by being listed. [03](docs/03-six-sides-and-the-virtual-drive.md) |
| **the program** | 14 segments, **592 of 592** procedure entry points inside their segment on the rebuilt volume (213 of 755 on the raw floppy). Against the IBM PC *Wizardry*: no `CASTLE`, `ROLLER`, `REWARDS`; new `DOCOPY`, `DOCACHE`; `SPECIALS` from 39 to 97 procedures. The loader still builds `KANA.KRN`, `KANJI.KRN`, `400.MONSTERS` file names. [04](docs/04-the-program-and-the-interpreters.md) |
| **three interpreters** | the shipped one (87-11-12) says *"A Serious Problem Has Occurred"*; side F's (87-11-04) says *"Unimplemented P-code %h"* and `S=%h P=%h I=%d PC=%x`; a third inside `BLAH` prints p-machine trace lines with `IPC`, `MP`, `NP`. [04](docs/04-the-program-and-the-interpreters.md) |
| **the text** | 256-leaf Huffman tree, LSB-first; lines byte-aligned and length-prefixed; per-block dictionary read backwards; a binary-search index. **424 messages, 3,175 lines, 0 closure failures**, bytes closed to 60,416. [05](docs/05-the-text.md) |
| **in the text** | *"NEC 9801 Pascal is (c)1985 by the Foretune co., ltd."* and a `1) English 2) Kana 3) Kanji` menu in the Apple release — one engine for two markets, the second being Japan; the Tolkien names (`Hobbit`, `Mordor` as *Master Charge*, `Thorin`, `Mythril`); the riddle answers stored in the clear behind a `$`, ten virtues mapped onto a body from crown to feet, closing on `$TREE OF LIFE`; all the endings; Lord Hawkwind of Skara Brae, *"the last member of the Softalk All-Stars"*, and the Dink who kills him; the developers in the locate spell (ADAMS *"grinning sardonically!"*, GREENBERG *"counting royalties in the tropics!"*); Monty Python, the White Rabbit, Karl *Maudlin*. [05](docs/05-the-text.md) |
| **the copy protection** | the Mordorcharge validation table is two "binary" messages: a count of 60 and 60 code/value pairs. **All 60 codes printed in *Computist* no. 51 (Jan. 1988) are its keys, and no others**; the magazine's third column equals the game's value + 8,449 (mod 9,000) on 20 of 20. [05](docs/05-the-text.md) |
| **the maps** | 15 level records in `SCENARIO.DATA`, wall arrays in the 1981 *Wizardry* layout; 12 agree with themselves at ≥ 0.966, three are one-way-wall levels (233 of 760 edges one-sided), one shipped twice. The pyramid, the Cube's sixteen rooms, the sealed 2 × 2 starting cell at the centre of the concentric level, whose only exit is a hidden door; and — identified by the owner, located here — **D, I, N, K** on four consecutive floors. [06](docs/06-the-data-files.md) |
| **the data** | a 512-glyph character set whose second half is the dungeon's wall fragments; monsters as 8 × 7 tile banks (composition open); eight empty save slots that still hold the monster names their testers summoned. [06](docs/06-the-data-files.md) |
| **leftovers** | 56 stale directory slots = an interpreter-rewrite diary, 35 files, 13 Aug – 11 Nov 1987 (`TEST1`, `TEST7`, `TEST14`, `VIRTDRIV.TEXT`, `RWTS2.TEXT`…); **a 6502 assembler listing of a disk formatter inside the monster pictures**; the Apple Pascal editor's messages inside `MAZE.INFO`; Pascal source of the square-type enumeration inside `KANA.KEYMAP`; a cache self-test shipped. [07](docs/07-leftovers.md) |
| **side F** | `BLANK`: `TESTANIM` (8 Dec 1987), `ANIM.DATA` (53 frames), an older interpreter, and `BLAH`. Stamped with the others, never mapped, never asked for. [07](docs/07-leftovers.md) |
| **dates** | directory 11 Nov 1987, interpreter 12 Nov, test program 8 Dec, every side stamped **22 Dec 1987** with its own eight-digit number. [03](docs/03-six-sides-and-the-virtual-drive.md), [07](docs/07-leftovers.md) |
| **coverage** | of 1,680 blocks: decoded and closed 29.40 %, identified but not decoded 70.60 %, not identified 0, residue 0. [01](docs/01-what-this-is.md) |
| **tools** | five readers written (`a2pascal`, `wiz4virt`, `a2codefile`, `wiz4krn`, `wiz4maze`) + `wiz4census`, 27 selftest checks, 0 failures; 806 inherited unchanged, of which `psystem.py`, written for the PC *Wizardry*, independently agreed on the rebuilt volume. [08](docs/08-tools-and-open-questions.md) |

## The chapters

| # | chapter | what it settles |
|---|---|---|
| [01](docs/01-what-this-is.md) | what this is | six sides, the split, the virtual volume file by file, coverage |
| [02](docs/02-the-technical-sheet.md) | the technical sheet | every figure and the command that reprints it |
| [03](docs/03-six-sides-and-the-virtual-drive.md) | six sides and the virtual drive | the 2,048-block directory, the arithmetic that exposed the packing, `SYSTEM.RELOC`, 239 of 239, the ghosts, boot and identity blocks |
| [04](docs/04-the-program-and-the-interpreters.md) | the program and the interpreters | 14 segments against the PC's 16, the Japanese-capable loader, the cache self-test, three interpreter builds |
| [05](docs/05-the-text.md) | the text | the tree, the backwards dictionary, 424 messages, the riddles' answers, the endings, Hawkwind, the developers, Mordorcharge |
| [06](docs/06-the-data-files.md) | the data files | the character set, the tiles, `MAZE.INFO`, the save slots, the scenario header, the level maps and D-I-N-K |
| [07](docs/07-leftovers.md) | leftovers | the directory diary, source in the slack, stale names, side F, the calendar |
| [08](docs/08-tools-and-open-questions.md) | tools and open questions | five readers, the inherited one that agreed, and what is still shut |

`notes/` holds the output of every command cited; `tools/` the box.

## Outside sources, marked as such

Three things in this repository come from outside the bytes, all supplied by
the owner and labelled where used: that the Dink's stab is a step to the
Grandmaster ending; that four level maps spell D-I-N-K (then located in the
bytes); and the *Computist* no. 51 table and the *Mordor Charge Valid Card
List* page (then compared with the bytes). Chapter 07 also cites the
circulated *Proving Grounds* source for one enumeration, marked as outside.

## Its index

Primary index: [apple2-gamelist-doc](https://github.com/vs-sr-dev/apple2-gamelist-doc),
created when the second Apple II title,
[apple2-theoregontrail-doc](https://github.com/vs-sr-dev/apple2-theoregontrail-doc),
arrived. This repository's row moved there from the single-title table of the
[profile README](https://github.com/vs-sr-dev/vs-sr-dev), where it was listed
while it was the only Apple II title. It is also cross-linked from
[pc-gamelist-doc](https://github.com/vs-sr-dev/pc-gamelist-doc), whose `Saga`
column reads *Wizardry* on the PC row, and is not listed there as a PC title:
the prefix names the target machine. A third or fourth *Wizardry* would make
the series an index of its own.

## Its neighbours

This is the collection's first Apple II object and its **second *Wizardry***:
[pc-wizardry-doc](https://github.com/vs-sr-dev/pc-wizardry-doc) measured the
IBM PC *Proving Grounds* (1987), a p-System volume also named `WIZBOOT`
whose program probed for `IS.APPLE` and `SYSTEM.RELOC` and found neither.
Here both exist, and the second is the reason the volume does. That
repository left its *Saga* cell empty until a second member of the series was
measured; this is one.
