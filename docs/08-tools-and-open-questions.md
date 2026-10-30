# 08 — Tools and open questions: five readers and a census script written, one inherited reader that agreed without being touched, and what is still shut

*Measure: `python tools/<tool>.py --selftest` for the five (notes/selftests.txt); `python tools/a2pascal.py --refuse` (notes/a2pascal-refuse.txt); `python tools/psystem.py _work/virtual.vol` (notes/psystem-virtual.txt).*

## The box

`tools/` holds 812 Python files: the 806 inherited from cd32-powerdrive-doc,
unchanged, five readers written here, and `wiz4census.py`, which prints the
census notes ([02](02-the-technical-sheet.md)). No inherited file was modified. One was
used: `psystem.py`, written for the IBM PC *Wizardry* volume, read the
virtual volume rebuilt here and agreed on all 21 entries, the chain, the
declared size and the dates ([03](03-six-sides-and-the-virtual-drive.md)).
That is the closest this repository has to an independent check of its own
assembly: the reader was not written for this object and was not adapted to it.

## The five written

| tool | what it reads | closure | refusal | selftest |
|---|---|---|---|---|
| `a2pascal.py` | a 140 K Apple II image in DOS order; Apple Pascal blocks through the published interleave; the volume header, the entries, the name-field tails, the stale slots; `--extract`, `--blocks` | chain from block 6 to `deovblk` with gaps reported; entries past the medium reported, not refused | wrong length, `dfirstblk` ≠ 0, `dlastblk` ≠ 6, name length 0 or > 7, `deovblk` < 6 or not a multiple of 8, > 77 files, an entry out of range — shown on sides B–E (`dfirstblk is 34985`) | 6 checks |
| `wiz4virt.py` | side numbers from block 1; the side map from `SYSTEM.RELOC`; the virtual volume; its files | extents tile each side from 0, no side over 280, virtual extents ascend; **every block carried by more than one side compared: 239 of 239 identical** | a side record out of range; an extent gap or overlap; a set without side 1 | 6 checks |
| `a2codefile.py` | an Apple Pascal codefile: segment dictionary, procedure dictionaries, `A6` string constants | every self-relative entry pointer inside its segment and the tail's segment number equal to the dictionary's — **592 of 592, 14 of 14** on the virtual volume, 213 of 755 on the raw floppy | not whole blocks; no segment; a segment past the file | 5 checks |
| `wiz4krn.py` | `ASCII.HUFF` and `ASCII.KRN`: the tree, the backward per-block dictionary, the index, every message | every line decodes to exactly its stated size, lines tile, end before the dictionary, numbers ascend and meet the index — **424 messages, 3,175 lines, 0 failures**; bytes close to 60,416 | a tree not 1,024 bytes, non-zero tail, ≠ 256 leaves, a symbol twice, depth > 255; a KRN without its index or sentinel | 6 checks |
| `wiz4maze.py` | level records in `SCENARIO.DATA`: four 2-bit wall arrays, the 1-bit and 4-bit grids; census, ASCII, PNG | east/west and north/south wall agreement per record — 12 records ≥ 0.966, 3 dense records listed separately as one-sided | (a census, not a parser: it labels instead of refusing) | 4 checks |

Three defects were caught by these tools' own checks during the session and
are worth recording because each looked like a finding first:

1. `a2pascal.py` first refused side A for `deovblk` ≠ 280. The 2,048-block
   volume is the object's, not a corruption; the check was loosened to report
   the ratio instead (7.3143) — and then to report entries past the medium
   rather than refuse them.
2. `wiz4krn.py`'s first audit stopped on block 17: a dictionary byte of 128.
   That is the two-byte delta; the parse was wrong, not the file.
3. A first pass of the maze search assumed records on even blocks and drew
   noise; the wall-agreement score is what moved it one block.

And one in this author's prose, caught before commit: chapter 01 first
carried coverage totals estimated instead of counted (43.21 % decoded). They
were replaced by the classification in notes/coverage.txt, which says 29.40 %.

## Open questions

| question | where it stands |
|---|---|
| How a monster picture is composed from its 64-tile block | no tile map found in five files; computed or inside the p-code ([06](06-the-data-files.md)) |
| The Mordorcharge arithmetic for columns 1 and 2, and the booklet's example codes | table found, all 60 keys matched, column 3 exact; the combining routine not traced ([05](05-the-text.md)) |
| `ASCII.KRN` block 0's second word, 234 | not resolved |
| `SYSTEM.RELOC` word 0, 2 | not resolved |
| The six side serials (40, 129, 262, 252, 71, 51) | per-side counter or per-copy serial; one dump cannot tell ([03](03-six-sides-and-the-virtual-drive.md)) |
| The 28 messages of 10-byte binary records (29,996…30,915) | five words, many ending `FF FF`; coordinates by their ranges; not mapped |
| `MAZE.INFO`'s 62 records | read as view-cell positions; drawing code not traced |
| `ANIM.DATA`'s 53 frames, and what they animate | index read, frames not decoded; no block matches the game |
| Why the Huffman tree gives NUL a 1-bit code | built on something other than this text, or more |
| `ASCII.KRN` block 117 | not text under the shipped tree |
| The four letters D-I-N-K | identified by the owner, located in the bytes (levels 101, 103, 105, 107); no letter recognition was automated |
| p-code | no instruction disassembled; every reading of program behaviour above comes from constants, names and sizes |

## What was not done

Nothing was emulated. The interpreters were compared by strings and byte
counts, not disassembled. The monster tiles, the character set and the level
maps were rendered for reading and the renders are not published. The game's
text is not published; it is quoted.
