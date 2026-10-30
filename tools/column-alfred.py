# -*- coding: utf-8 -*-
"""The Alfred Chicken (CD32) column for the section 10 baseline table.

The eighteenth disc, and the first read from physical media rather than from an
image file.
"""

TITLE = "**Alfred Chicken (1993)**"

CELLS = {
 "Publisher / studio":
   "**Twilight (developer) for Mindscape (label)** — and the **first disc in "
   "the set where the two are separable from the artwork**: the copyright and "
   "the trademark are Twilight's, Mindscape is the label only. PVD publisher "
   "field says `Mindscape`; the build is Twilight's by its RCS keywords",

 "Master cut":
   "**PVD 1993-12-06 17:54:10, and step 39 *confirms* it** — the first clean "
   "pass in the set. `.TM` says © 1993, and the shipped `c/setpatch 40.14 "
   "(7.10.93)` puts a hard floor at **1993-10-07**, sixty days earlier. "
   "`/alfred` was written **alone, 21 h 26 m after every other file**, and the "
   "image was cut 3 m 29 s later",

 "Tracks":
   "**10 — 1 data (`MODE1/2048`, *verified* by descrambling raw sectors and "
   "reading the header mode byte on all 902, not sampled) and 9 audio**",

 "Data track sectors":
   "**918 carrying data** (LBA 0–917) + **150 of silent pregap**; volume "
   "declares **691**, so a **227-sector overrun** — and the physical disc "
   "shows *why*: the data run is padded up to where track 2's pregap begins",

 "Audio":
   "**9 Red Book tracks, 92,445 sectors, 20 m 32 s** — peaks 11,458–22,442, "
   "**zero lead-in silence on all nine and zero pregap between them**, so the "
   "soundtrack was cut as one run and split. Reached via **`cd.device`** (2 "
   "`OpenDevice`). **No ISRC on any track** (TCVAL=0), no pre-emphasis, "
   "two-channel. Also raw 8-bit PCM inside both executables, no header, no name",

 "Share of a 333,000-sector CD":
   "**28.08 % pressed** (93,513 sectors to lead-out) — but the data track is "
   "**0.28 %**: **99.02 % of the physical disc is audio**",

 "Files / directories":
   "**30 / 4**, zero empty directories. **11 levels from 6 tile sets**, read "
   "from two parallel fixed-stride tables in `alfred`, plus a 12th entry "
   "(`cloud`) that exists only in the tile-bank table",

 "Bytes on disc / unpacked":
   "**1,261,776 / 1,636,635** — expansion **1.297×, the lowest of eleven**; "
   "used 1,610,416, slack **1.602 %**. **Breaks Guardian's floor by 43.9 %**, "
   "the first disc to do so in eighteen — because the content is in Red Book, "
   "not in the data track",

 "Compression":
   "**RNC ProPack method 1, real** — 11 streams, decoded by the unmodified "
   "Dragonstone decoder with the header CRC validating **11 of 11**. Seven are "
   "whole files, **four are embedded inside `alfred`**. **Nesting depth 0**, "
   "reached by decoding. 104,373 → 479,232 = 4.59× on the streams alone",

 "PVD system id":
   "`CDTV` + 28 spaces — wrong again: `lowlevel.library`, `freeanim.library` "
   "and `setpatch 40.14` all say CD32",

 "PVD application id":
   "**empty**",

 "Cue `CATALOG`":
   "**`0000000000000` — and for the first time in the set this was read from "
   "the disc**, not from someone's cue: subchannel Q MODE-2, **MCVAL=1**. The "
   "thirteen zeros are what the master carries, so the four discs showing them "
   "are not a dumper artefact",

 "Mastering tool":
   "ISOCD 1.04 (Pantaray)",

 "Preparer field":
   "**`Abersoft - ISOCD 1.04 by Pantaray, Inc. USA -` — the SECOND company** "
   "in the field after Rob Northen Computing. Not Pocock, and the final run is "
   "**32**, so `D J Pocock`→232 survives at **5 of 5 against 13 of 13** — and "
   "survives its first same-label test, since Mindscape's other disc "
   "(Liberation) *is* Pocock. `Abersoft` appears nowhere else on the disc",

 "Duplicate PVD":
   "yes, sectors 16 and 17 **byte-identical whole-sector**, terminator at 18",

 "Volume starts at LBA":
   "22 (root); **first file at 23**, no hole anywhere",

 "`.TM` block at":
   "sector 21, 2,048 B, reached through the `'TM'` tag at PVD byte 888, "
   "constant `0x0014`. No `.TM` file in the root",

 "`.TM` contents":
   "identical — all three SHA-1s match, making it **sixteen of the seventeen "
   "CD32-era discs** (Speris still the odd one)",

 "Unclaimed sectors in the volume":
   "**32, all zero, at the end** (LBA 659–690) — the ordinary final run; plus "
   "**227 sectors past the declared volume**, all zero but **genuine MODE1 "
   "with valid sync, matching header address and passing EDC**. First disc "
   "that could prove the overrun is the mastering and not the dumper",

 "Timestamps":
   "**all 33 records in 1993**, five calendar days. Fifteen files copied in a "
   "**9-second block** on 11-30; `/alfred` alone on 12-06 after **21 h 26 m** "
   "of nothing. PVD **+3 m 29 s** from the newest file, the tightest in the "
   "set; **root directory record −33 s**, normal, stored identically in three "
   "places. **Zero 1980 and zero 1978 timestamps** — the fourth such negative. "
   "And a dating instrument the set has not had: **expanded RCS `$Header:` "
   "keywords**, `Hard0:alfred/rcs/amiga.c 93/11/19 JJS` and "
   "`.../intro/rcs/amiga.c 92/09/29 JJS` — **fourteen months apart**",

 "SetPatch":
   "**`c/setpatch 40.14 (7.10.93)`**, beside `c/assign 37.4 (25.4.91)` and "
   "`c/execute 37.11 (14.5.91)` — three Commodore commands from two OS "
   "releases two and a half years apart, and the newest is what dates the master",

 "First stage":
   "`/alf`, 13,736 B, 2 hunks, 8 relocations (1.49/KB) — **a SAS/C 6.00 C "
   "program that is 46.9 % debug information**: `HEADDBGV01`, the full symbol "
   "table, `alf.c` and a line-number table, all pressed. What it does is run "
   "`intro` and then `alfred`",

 "Game executable":
   "`/alfred`, 816,616 B, 8 hunks, **7,231 relocations**. The whole-file "
   "16.46/KB is meaningless — **the 6,102 relocations of its 441,780-byte CODE "
   "hunk all sit in the first 24.2 %**, so it is ~107 KB of code at ~57/KB "
   "followed by ~335 KB of data in a CODE hunk. Also `/intro`, 255,376 B, "
   "**42.46/KB**, built from source checked out **fourteen months earlier**",

 "Libraries opened":
   "**8 `OpenLibrary` in each of `alfred` and `intro`, 3 in `alf`**; 2 "
   "`OpenDevice` each against exactly two named devices (`cd.device`, "
   "`input.device`)",

 "`freeanim.library`":
   "**named by both game executables but not shipped** — taken from CD32 ROM. "
   "(Liberation, the other Mindscape disc, ships its own copy in `c/`)",

 "Akiko":
   "**untouched — all four figures zero**: 0 loads of `$00B80000`, 0 of "
   "`$B80030`, 0 C2P port, 0 `$C0DE0000`. Predicted absent from the *mechanism* "
   "— the disc boots AmigaDOS, leaves Exec alive and reaches the CD through "
   "`cd.device`",

 "Colour":
   "**`intro` calls `LoadRGB4` *and* `LoadRGB32`, once each — the third disc "
   "in the set to call both**, and unlike Superfrog these are in a shipped game "
   "executable. `alfred` calls neither (4 × `LoadView`) and takes its colours "
   "from copper `MOVE`s built in code. **No palette is stored anywhere**",

 "Graphics":
   "planar, **no C2P: 163 constants as data, 0 as immediates** — the 11th "
   "planar-in-planar disc; `$AAAAAAAA` and `$55555555` absent in both roles, so "
   "not even Myth's MFM merge. **Zero stored copper lists** (4,052 candidate "
   "runs rejected) — built at run time. Screen mode *is* hardcoded: "
   "`BPLCON0 = $4200` (**BPU 4**) in `alfred`, `$5200` (**BPU 5**) in `intro`, "
   "`BPLCON3 = $1400` so AGA is really used. **Tiles 16×16×4, 128 B, "
   "row-interleaved; maps 32×32 byte indices** — derived from three independent "
   "measurements: every graphics piece an exact multiple of 128, max map index "
   "exactly (len/128)−1 on **7 of 7**, and BPU=4 from the register. Blitter: "
   "**no FILL bit, no `$CA` minterm**, every BLTSIZE computed",

 "Text encoding":
   "**7-bit ASCII, measured: 0 bytes above `0x7F` in any prose run**. Prose "
   "**0.607 % on disc, 0.468 % resident** — but **0 % of it is in any asset "
   "file**, 19.6 % belongs to Commodore's commands and 78.8 % to a debugger and "
   "the SAS/C runtime. **A FIFTH string model: there is no table, because there "
   "is no text** — the game's own title exists on the disc only as a 320×184 "
   "four-plane *picture*",

 "Languages":
   "1 (EN), and no localisation — nor anything to localise",

 "Music":
   "**Red Book only**: 9 tracks, 20 m 32 s. **0 tracker modules, 0 IFF 8SVX, 0 "
   "The Player, 0 IFF FORMs of any kind on the whole disc.** Sound effects are "
   "**raw 8-bit PCM inside the executables**, headerless and nameless, found "
   "only because a device-path scan false-positived on `TUKLD:` inside a waveform",

 "Save system":
   "**none**, confirmed two ways: 0 loads of `$B80030`, and "
   "`nonvolatile.library` is **neither shipped nor named by any game binary**. "
   "A third route to the same answer — Superfrog shipped it and opened it from "
   "nowhere, Myth had no `libs/` at all",

 "Cut content":
   "**`intro` ships a working Amiga hardware debugger** — 47 register "
   "description strings lifted verbatim from Commodore's `hardware/custom.i`, "
   "plus **`copdis`, a copper list disassembler** with a null guard and an "
   "`UNKNOWN_OPCODE` path; `alfred`, built 14 months later, has none of it. "
   "**`alfred.info`'s DefaultTool is the string `JUNK`** with zero ToolTypes. "
   "**`End Of All Vars!`** between the globals and the code. The shipped boot "
   "script tests for a developer's own volume **`JJSDISK:`** (the disc's only "
   "unresolvable reference, and deliberately guarded), `alfred` carries "
   "**`alf2:%s`**, and RCS stamped **`JJS`** and **`Hard0:`** into both "
   "executables. **57 tiles drawn, packed, pressed and never placed by any map** "
   "(72 of 563 across seven banks, 12.8 %). `frontend.pak` is **shipped twice** "
   "— byte-identical inside `alfred`",
}
