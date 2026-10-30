# 02 — The technical sheet: every figure, and the command that reprints it

`OBJ` is the object directory, `wizardry-iv-the-return-of-werdna/`, holding
the six `.dsk` images as extracted from the owner's ZIP. Commands run from the
repository root with Python 3; `wiz4maze.py --png` alone needs PIL. Outputs
in `notes/` are the outputs of these commands, unedited.

## Order of operations

```
# side A's and side F's Pascal volumes, as they lie on the floppies
python tools/a2pascal.py OBJ/*Disk\ 1*.dsk OBJ/*Disk\ 6*.dsk          > notes/a2pascal-dir.txt
python tools/a2pascal.py OBJ/*Disk\ 1*.dsk --extract _work/vol1
python tools/a2pascal.py OBJ/*Disk\ 6*.dsk --extract _work/vol6       (both: notes/a2pascal-extract.txt)
python tools/a2pascal.py --refuse OBJ/*Disk\ [2-5]*.dsk               > notes/a2pascal-refuse.txt
for i in 1 2 3 4 5 6: python tools/a2pascal.py OBJ/*Disk\ $i*.dsk --blocks _work/d$i.blk

# the virtual volume
python tools/wiz4virt.py OBJ/*Disk\ [1-5]*.dsk                         > notes/wiz4virt.txt
python tools/wiz4virt.py OBJ/*Disk\ [1-5]*.dsk --extract _work/virt   > notes/wiz4virt-extract.txt
python tools/wiz4virt.py OBJ/*Disk\ [1-5]*.dsk --volume _work/virtual.vol
python tools/psystem.py _work/virtual.vol                              > notes/psystem-virtual.txt

# the program
python tools/a2codefile.py _work/virt/SYSTEM.PASCAL --strings         > notes/a2codefile-system-pascal.txt
python tools/a2codefile.py _work/vol1/SYSTEM.PASCAL                   > notes/a2codefile-raw-floppy.txt
python tools/a2codefile.py _work/vol6/SYSTEM.PASCAL --strings         > notes/a2codefile-testanim.txt
(BLAH bytes 0..2047 to _work/blah-code.bin)
python tools/a2codefile.py _work/blah-code.bin --strings              > notes/a2codefile-blah.txt

# the text, the maps, the censuses
python tools/wiz4krn.py _work/virt/ASCII.HUFF _work/virt/ASCII.KRN --audit   > notes/wiz4krn-audit.txt
python tools/wiz4maze.py _work/virt/SCENARIO.DATA                             > notes/wiz4maze-census.txt
python tools/wiz4maze.py _work/virt/SCENARIO.DATA --ascii B --crop 9 17 3 12  > notes/wiz4maze-dink.txt  (B = 101 103 105 107)
python tools/wiz4maze.py _work/virt/SCENARIO.DATA --sealed; --ascii 119 --crop 5 15 5 15; --ascii 105 --crop 4 12 13 20   > notes/wiz4maze-start.txt
python tools/wiz4census.py identity|stale|coverage|census OBJ   > notes/side-identity.txt, stale-directory.txt, coverage.txt, census.txt
python tools/wiz4census.py krn|interp|data|slack _work          > notes/krn-census.txt, interp-strings.txt, data-files.txt, slack-text.txt
for t in a2pascal a2codefile wiz4virt wiz4krn wiz4maze: python tools/$t.py --selftest   > notes/selftests.txt
```

`notes/mordorcharge.txt` comes from `_work/mordorcharge.py`, which carries a
table transcribed from *Computist* no. 51 and is therefore not published.

## The figures

| figure | value | command / note |
|---|---|---|
| images | 6 × 143,360 = 860,160 bytes, 6 distinct SHA-1 | notes/hashes.txt |
| image mtime / inner ZIP date | 1996-12-25 00:32 / 2013-02-28 | `unzip -l` |
| side A volume | `WIZBOOT`, 2,048 blocks declared (7.3143 × 280), 21 files, last boot 87-11-11 | a2pascal-dir |
| side A files beyond the medium | 14 of 21 begin past block 280; `200.MONSTERS` straddles it | a2pascal-dir |
| stale directory slots | 56 past `dnumfiles`, 35 distinct names, 87-08-13 … 87-11-11 | stale-directory |
| sides B–E refused | `dfirstblk is 34985` ×4 | a2pascal-refuse |
| raw-floppy `SYSTEM.PASCAL` | 213 of 755 pointers, 2 of 14 tails | a2codefile-raw-floppy |
| `SYSTEM.RELOC` | word 0 = 2; 5 sides, 12/17/24/25/28 extents; list ends word 329 | wiz4virt |
| side usage | A 226, B 278, C 278, D 265, E 256 of 280 | wiz4virt |
| virtual blocks | 546 held (0..555), 544 excluding 0–1; carriers 305/27/9/108/95 | wiz4virt, census |
| multiply-carried blocks | **239 of 239 byte-identical, 0 conflicts** | wiz4virt |
| unmapped inside files | `200.MONSTERS` 10 blocks, `SCENARIO.DATA` 1 | wiz4virt-extract |
| files on no side | 10 (557..2,047 = 1,491 blocks, 72.80 % of the declared volume) | wiz4virt |
| unused blocks A–E | 97, all zero | coverage |
| `SYSTEM.PASCAL` (virtual) | 14 segments, 76,476 code bytes, **592 of 592** pointers, 14 of 14 tails | a2codefile-system-pascal |
| `**ERR**` constants | 22 in 9 segments | a2codefile-system-pascal |
| interpreters | 3 builds × 13,312 bytes; A–F 10,608, A–BLAH 10,733, F–BLAH 5,129 bytes differ | interp-strings |
| `TESTANIM` | 1,134 bytes / 14 procs (F), 1,188 / 14 (BLAH) | a2codefile-testanim, -blah |
| Huffman tree | 256 leaves, depth 1..18; NUL 1 bit, space 5 bits | wiz4krn `--codes`, krn-census |
| text | 116 text blocks, **424 messages, 3,175 lines, 0 failures**, numbers 1..30,915 | wiz4krn-audit |
| text bytes | 53,820 + 4,048 + 1,520 + 4 = 59,392; + 1,024 = 60,416 | wiz4krn-audit |
| characters | 61,501; NUL 791 (1.29 %); 7.0 bits a character | krn-census, wiz4krn-audit |
| line markers | `^` 296, `@` 85, `#` 27, `*` 26, `$` 19 | krn-census |
| monster / item / spell lines | 480 / 234 / 51 | krn-census |
| Mordorcharge table | 60 pairs; 60 of 60 *Computist* codes; column 3 exact 20 of 20 | mordorcharge |
| level records | 15 (12 consistent ≥ 0.966; 107, 111, 127 one-sided); 107 vs 127: 20 bytes differ | wiz4maze-census |
| one-sided edges, level 107 | 233 of 760 | wiz4maze (chapter 06) |
| level 119 special-event grid vs the owner's map of level 10 | 14 of 14 squares agree, 0 extra either way; both pentagrams = 13 | wiz4maze-level119-specials (script in `_work`) |
| sealed 2 × 2 rooms | 2: block 119 x 9–10 y 9–10 (centre, hidden door north), block 105 x 7–8 y 16–17 | wiz4maze-start |
| character set | 512 glyphs, 146 blank (17 / 128 / 1) | data-files |
| monster tiles | 3,840, 903 blank, 257 all-printable | data-files |
| `MAZE.INFO` | 62 records, words 0..2,942 | data-files |
| `WERDNA.DATA` | 8 slots, 3 empty name fields each, stale names behind them | data-files |
| `ANIM.DATA` | 54 index entries = 53 frames + end marker | data-files |
| identity stamps | `12/22/87` + 40 / 129 / 262 / 252 / 71 / 51, byte 510 = side | side-identity |
| coverage | decoded 494 blocks (29.40 %), identified 1,186 (70.60 %), residue 0 | coverage |
| selftests | 5 tools, 27 checks, 0 failures | selftests |
