# 06 — The data files: a character set that is also the dungeon, monsters in 8 × 7 tiles, eight empty save slots that remember their test games, and a scenario header in the shape of 1981

*Measure: renders and structure scripts on `_work/virt/*` (renders kept in `_work/render`, not published); census figures in notes/census.txt and notes/data-files.txt.*

All files here are read from the virtual volume of [03](03-six-sides-and-the-virtual-drive.md).
Where a structure was measured but not decoded, the chapter says so.

## `200.CHARSET` — 4,096 bytes, 512 glyphs, rendered

Eight bytes a glyph, one byte a row, seven pixels a byte with bit 0 leftmost
— the Apple II hi-res convention. Rendered at 32 glyphs a row, the file
splits into three parts with nothing left over:

| glyphs | what the render shows |
|---|---|
| 0..127 | the text font: box-drawing corners and edges, a few small icons, arrows ↑ → ↓, a checker block and a left-pointing triangle, then `!` … `~` in ASCII order — and **glyph 126, `~`, drawn as a RETURN arrow**, which is why the text says *Press ~* ([05](05-the-text.md)) |
| 128..255 | **all 128 empty** |
| 256..511 | **diagonal, vertical and horizontal wall fragments in perspective** — the pieces of the first-person maze view; one of the 256 is empty |

So the dungeon is drawn in characters. The empty second quarter has the size
of an inverse or alternate font. 146 glyphs in all are blank: 17 in the text
font, 128, 1.

## `200.MONSTERS` — 30,720 bytes of tiles, ten blocks never shipped

The same eight-byte, seven-pixel cell: rendered as rows of cells, every
block shows coherent fragments — eyes, claws, hatching, robes — and rendered
as one 70 × 51 bitmap, it shows noise. **The file is a bank of 3,840 tiles**,
64 to a block, of which 903 are blank and 257 consist entirely of printable
ASCII — those 257 are where [07](07-leftovers.md)'s assembly listing lives.
Text lying in whole tiles inside a picture file is what unused tile slots
filled from a dirty buffer look like, and it means each picture uses fewer
than 64 tiles of its block.

**How a picture is composed from its tiles is not resolved.** No run of 60
or more bytes below 64 — the shape a tile map would have — exists in
`SCENARIO.DATA`, `MAZE.INFO`, `WERDNA.DATA`, `SYSTEM.PASCAL`, the tile file
or `KANA.KEYMAP`. The map is either computed, packed below a byte, or inside
the p-code.

Ten of the sixty blocks (virtual 245, 250, 251, 270, 271, 279, 280, 283, 284,
285) are carried by no side. If one block is one monster's picture, ten
pictures were laid out on the master volume and never shipped.

## `MAZE.INFO` — the one `infofile`, 3,584 bytes

The only file on the volume with Pascal kind 4. It opens with **62 four-byte
records**, `(byte, byte, word)`, whose words ascend from 0 to 2,942 and whose
byte pairs stay inside 0..27 × 0..17:

```
(16,8,0) (18,8,15) (14,7,32) (19,7,61) (10,3,92) (21,3,179) (2,0,272) (25,0,421)
(16,8,576) (18,8,591) (14,7,608) …  (17,17,2929) (0,0,2942)
```

The pairs come in couples that widen — 16/18, 14/19, 10/21, 2/25 — and the
sequence restarts at 576 with the same coordinates: that is the shape of left/right wall positions at successive
depths, in character cells, for a view about 28 cells wide and 18 high,
indexing into glyph runs. That is a reading of the shape; the drawing code was
not traced. `MAZE.INFO` is on sides B–E only — the dungeon sides.

Its slack is chapter [07](07-leftovers.md)'s: at `0xF8`..`0x1F5` and
`0xDBB`..`0xDE8` it holds messages of the **Apple Pascal screen editor** —
*"* already exists. Delete before S(ave? -->"*, *"Y(es to delete old file
before saving new one."*, *"pattern not in the file."*, *"No old pattern."*

## `WERDNA.DATA` — 12,288 bytes: eight save slots and two scenario headers

```
0x0000..0x0FFF   8 slots × 512    the save games ("Save to which Save Game (1-8)")
0x1000..0x17FF   2,048            a scenario header
0x1800..0x1FFF   2,048            a second scenario header
```

Each slot opens with the Pascal string `WERDNA` (length 6). At `+0xDC`,
`+0xEC`, `+0xFC` sit three 16-byte string fields — the summoned monster
groups, by their content — and **all three have length 0 in all eight
slots**. Behind the zero length, the bytes are not cleared:

| slots | field 1 | field 2 | field 3 |
|---|---|---|---|
| 0, 1 (identical) | `ENTELECHY FUFF` | `FLACKECHY FUFF` | `LYCURGUSY FUFF` |
| 2, 3 | `GAS CLOUDSSTSS` | `LVL 1 PRIESTSF` | `ZOMBIESSY FUFF` |
| 4..7 | `BLACK DRAGON` | `ENTELECHY FUFF` | `LYCURGUSY FUFF` |

Each is a shorter name written over a longer one: `FLACK` over
`ENTELECHY FUFF` leaves `FLACKECHY FUFF`; `LYCURGUS` leaves `LYCURGUSY FUFF`.
`Entelechy Fuff`, `Flack`, `Lycurgus` and the rest are monster names of this
game ([05](05-the-text.md), monster-name block). **The shipped save file is
eight blank games that still remember the monsters their testers summoned.**

The two headers at `0x1000` and `0x1800` both begin with
`THE RETURN OF WERDNA` and differ from each other and from the real
`SCENARIO.DATA` header (1,095 of 2,048 bytes differ from the latter). Their
race and class tables carry the same stale tails as the real one.

## `SCENARIO.DATA` — 73,728 bytes: the header, and the levels

The header has the layout the original *Wizardry* scenarios use:

```
+0     STRING[40]   \x14 "THE RETURN OF WERDNA" + 20 stale bytes
+42    words        1 0 1 1 31 6 48 10 1 1 1 15 120 0 120 500 0 1 2 1024 33 168 21 99 …
then   STRING[9] ×  NO RACE  HUMAN  ELF  DWARF  GNOME  HOBBIT
                    FIGHTER  MAGE  PRIEST  THIEF  BISHOP  SAMURAI  LORD  NINJA
                    OK  AFRAID  ASLEEP  P-LYZE  STONED  DEAD  ASHES  LOST
                    UNALIGN  GOOD  NEUTRAL  EVIL
```

**Races, classes, statuses, alignments: the 1981 set, unchanged**, in a game
whose player character is one evil mage and whose party is monsters. The
fixed-length fields keep what was in memory behind each name:
`MAGE` + `.LIBR`, `ASLEEP` + `IBR`, `NINJA` + `ed)`, `NEUTRAL` + `b` —
`.LIBR` reads as the tail of `SYSTEM.LIBRARY`. The word block after the title
is the table of contents of record kinds and counts; it was not mapped field by
field. Apart from the level maps below, the records beyond the header are
identified, not decoded.

The first two blocks of `SCENARIO.DATA` (virtual 413–414) are on side A; the
rest is spread over B–E by level; the last block is on no side.

### The level maps — fifteen records, read and drawn

*Measure: `python tools/wiz4maze.py _work/virt/SCENARIO.DATA` (notes/wiz4maze-census.txt), `--ascii BLOCK --crop 9 17 3 12` (notes/wiz4maze-dink.txt), `--png` (render kept in `_work`).*

A level record starts on an odd block of the file, 99 to 127, one every
1,024 bytes. It opens with the four wall arrays of the original *Wizardry*
maze record, in its order — west, south, east, north — 120 bytes each: 20
columns of 6 bytes, a column being 20 two-bit values packed least significant
first and a zero sixth byte (0 open, 1 wall, 2 door, 3 hidden door). At +480
follows a 1-bit-per-square grid (20 columns × 4 bytes) and at +560 a
4-bit-per-square grid (20 columns × 10 bytes). x runs 0..19 west to east, y
0..19 south to north.

**The closure is the map agreeing with itself**: the east wall of (x, y)
must be the west wall of (x+1, y), the north wall the next square's south
wall. The search that found the records maximised exactly that, and the
census prints it:

```
block   E/W     N/S    walls
   99   0.997   0.997    557   LEVEL          113   0.995   0.997    548   LEVEL
  101   1.000   0.989    669   LEVEL          115   1.000   1.000     86   LEVEL
  103   1.000   1.000    586   LEVEL          117   1.000   0.997   1112   LEVEL
  105   0.995   0.992    745   LEVEL          119   0.995   0.992    498   LEVEL
  107   0.721   0.666    575   one-sided      121   0.976   0.966    689   LEVEL
  109   0.997   0.995    331   LEVEL          123   0.997   1.000    197   LEVEL
  111   0.958   0.926    872   one-sided      125   0.995   0.995     73   LEVEL
                                              127   0.721   0.668    566   one-sided
```

A random block scores about 0.4. Twelve records agree at 0.966 or better.
Three are dense maps that agree less, and they are the interesting ones:
**107 has 233 of its 760 interior wall edges present on one side only** —
*Wizardry*'s one-way walls, used wholesale — and **127 is a second copy of
107 differing in 20 bytes of 1,024** (9 of them in the walls): two versions
of one level, both shipped. 111 is the grid of sixteen identical rooms that
the text calls the Cosmic Cube's (*"Welcome to The Cosmic Cube!"*).

Drawn, the shapes the text describes are there: the stepped pyramid of the
Ziggurat (113, whose 1-bit grid fills the same triangle), rooms around a
courtyard (99), nested squares (119), an almost empty level (115, 86 wall
values), a level of stacked corridors (117).

**D, I, N, K.** The owner, mapping these levels from outside knowledge,
reports that four of them spell the name of the monster that kills Hawkwind
([05](05-the-text.md)) — on levels at blocks 101, 103, 105, 107, slightly
south-east of the centre. The crops `x 9..16, y 3..11` of those four records
are in notes/wiz4maze-dink.txt. In 103 the **I** is unambiguous in the
walls — a three-square bar at y 10, a stem down x 12–13, a bar at y 5; in 101
the **D** is the closed rectangle at x 12–14, y 7–9 with its corridor; the
**N** of 105 and the **K** of 107 read as corridors once the word is known.
The identification is the owner's; the coordinates and the bytes are this
repository's. The letters sit on four *consecutive* level records, which is
what one word laid across four floors of a dungeon should look like in the
file.

**The first puzzle: a cell with no door** (notes/wiz4maze-start.txt). A
search of all fifteen records for a 2 × 2 room whose interior is open and
whose eight outer edges are walls except for **hidden doors** (wall value 3)
finds exactly two. One is at the **exact centre** of the level at block 119
— the level of concentric rings, whose guardians the text calls the Inner,
Middle and Outer Way — at x 9–10, y 9–10: seven outer edges are walls and the
eighth, north of (9, 10), is a hidden door. Of its four squares only (10, 10)
has a non-zero value in the 4-bit grid (13). The other is at x 7–8, y 16–17 of
block 105, with one hidden door to the west.

From outside these bytes, the owner's account of how the game begins: Werdna
wakes in a closed 2 × 2 room, and the only way out is to summon monsters at
the pentagram, include priests, enter a fight, and wait for one of them —
whose actions the player does not control — to cast `MILWA`, the light spell
that shows hidden doors (it is in the spell table, message 5,000); and the
puzzle was obscure enough that, by testimony, Sir-Tech shipped its solution in
a sealed envelope in the box. The bytes cannot show an envelope. They do show
a sealed cell at the centre of a level whose only exit is a door that does not
exist until it is lit.

## `KANA.KEYMAP` — 1,024 bytes

On the IBM PC *Wizardry* this file held 44 ascending Shift-JIS codes. Here it
holds binary words and, at `0x1AC`, a fragment of the game's **Pascal
source** in UCSD text-file form ([07](07-leftovers.md)). No Shift-JIS run was
found; the name survives the purpose, or the purpose was never Apple's.

## On side F: `ANIM.DATA`

104,448 bytes, 204 blocks, dated `84-11-07`. It opens with an index of
`(block, offset)` pairs — `(1,0) (2,501) (4,293) (5,112) (5,347) (6,142) …
(198,12) (203,65535)` — **53 variable-length frames** and an end marker, the
frames packed back to back across block boundaries. None of its 204 blocks
equals any block of the game volume. The frame encoding was not decoded; its
byte entropy (5.08 bits) is that of a simple run or delta coding, not of raw
hi-res pages. Chapter [07](07-leftovers.md) is the rest of side F.
