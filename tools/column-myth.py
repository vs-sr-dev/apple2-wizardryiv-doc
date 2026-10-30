# -*- coding: utf-8 -*-
"""The Myth (CD32) column for the section 10 baseline table."""

TITLE = "**Myth — History in the Making (1992/1993)**"

CELLS = {
 "Publisher / studio":
   "**System 3 Arcade Software, UK — developer and publisher in one**, and a "
   "label new to this set. Verified from the PVD field, the `MYTH.A` bootblock "
   "and the credit screen, plus a 320×256 logo picture",

 "Master cut":
   "**PVD says 1992-12-21 17:10:58 — and the disc falsifies it.** The `.TM` "
   "block it carries reads `Copyright © 1993 - Commodore Electronics Ltd.`, "
   "and the loader needs a 68020 and Akiko. Third disc with the 1992-12-21 "
   "epoch, and the first one proven wrong from inside the image",

 "Tracks":
   "1 data (`MODE1/2048`), **no audio track** — the fourth such disc",

 "Data track sectors":
   "**27,361 exactly** (26,987 declared) — second consecutive image that is an "
   "exact multiple of 2,048, and a **374-sector overrun**, the largest in the set",

 "Audio":
   "0 s Red Book; **2 OctaMED `MMD0` modules** (156,006 and 48,782 B, 88.8 % of "
   "them samples) and **2 IFF 8SVX inside an executable** (`wing1` 2,796 Hz, "
   "`FLASH2` 8,860 Hz, `ANNO` `Audio Master` and `Audio Master II`)",

 "Share of a 333,000-sector CD":
   "8.22 % pressed — but **0.41 % of content**: 94.86 % of the declared volume "
   "is a hole",

 "Files / directories":
   "**5 / 2** — the smallest tree in the set. Three of the five files are "
   "**901,120 B each: one 880 KiB Amiga floppy image, exactly**",

 "Bytes on disc / unpacked":
   "2,722,021 / **3,726,007** — expansion **1.369×, the lowest of ten "
   "measured**; used 3,723,675, slack **0.063 %**. On disc it sits **21.0 % "
   "above Guardian's floor**, so the floor survives a second disc predicted to "
   "break it",

 "Compression":
   "**Bytekiller — the eighth cruncher, under a magic nobody had seen: "
   "`DAVE`**, the programmer's first name. 23 streams (22 with the container "
   "header, 1 bare), 2,526,172 → 3,530,158, 71.6 %. **Nesting depth 0**, and "
   "the checksum Legends' copy had removed is still here, so every stream "
   "validates three ways",

 "PVD system id":
   "`CDTV` + 28 spaces — and this is a **CD32** disc: Akiko, `freeanim.library` "
   "and `movec cacr` all say so",

 "PVD application id":
   "**empty**",

 "Cue `CATALOG`":
   "`5020573000264` — a real EAN-13",

 "Mastering tool":
   "ISOCD 1.04 (Pantaray)",

 "Preparer field":
   "**`ROB NORTHEN COMPUTING, UK. TEL: + 44 428 707771 FAX: + 44 428 707772 - "
   "...` — a FOURTH pattern: a company with contact details**, not a person "
   "and not empty. The firm is the author of **RNC ProPack**, the set's "
   "commonest cruncher — and this master does not use it",

 "Duplicate PVD":
   "yes, sectors 16 and 17, terminator at 18",

 "Volume starts at LBA":
   "19 — **but the first file is at 25,624, behind a hole of exactly 50 MiB**",

 "`.TM` block at":
   "sector 21, 2,048 B, reached through the `'TM'` tag at PVD byte 888. **No "
   "`.TM` file in the root**",

 "`.TM` contents":
   "identical — all three SHA-1s match, making it **fifteen of the sixteen "
   "CD32-era discs**",

 "Unclaimed sectors in the volume":
   "**32, all zero, at the end** — *and* **25,600 in front of the files, "
   "exactly 50.000000 MiB, 94.86 % of the declared volume**; plus a **374**-sector "
   "overrun past the volume, the largest so far",

 "Timestamps":
   "**all eight records 1992-12-21**, in two clusters: the three floppy images "
   "and the boot script in 2 m 53 s at 15:12–15:15, then **1 h 44 m 34 s of "
   "nothing**, then `/myth` alone at 16:59:25. PVD **+11 m 33 s**; **root "
   "directory record −1 s** from the newest file, which is step 37's second "
   "and first *normal* reading",

 "SetPatch":
   "**none — no `c/` directory at all**, and no `libs/`, `devs/` or `fonts/`",

 "First stage":
   "`/myth`, 18,656 B, 1 hunk, **0 relocations** — fully self-relocating. "
   "**3 library calls** (`OpenLibrary`, `CloseLibrary`, `Disable`), **0 "
   "`OpenDevice`**, **Akiko direct**. Contains **four media back ends** (DOS, "
   "floppy with MFM decode, hard disk with `RigidDiskBlock` parsing, CD) and a "
   "**hand-written `LoadSeg`**",

 "Game executable":
   "`MYTH.A+s3c00`, 126,700 B, 5 hunks, **2,950 relocations** (35.5/KB); a "
   "second program `MYTH.C+s79548`, 75,336 B, 177 relocations (29.6/KB), draws "
   "the ending",

 "Libraries opened":
   "**1, and its result is discarded**: `freeanim.library` is opened and closed "
   "without being tested",

 "`freeanim.library`":
   "**opened and immediately closed, result never read** — a CD32 probe whose "
   "answer nothing uses",

 "Akiko":
   "**driven directly** — 1 pointer load of `$00B80000` (third disc in "
   "seventeen, first outside Core Design), displacements `$04 $08 $10 $14 $18 "
   "$19 $1A $1D $1F $20 $24`. **0** `$B80030`, **0** C2P port, **0** "
   "`$C0DE0000`",

 "Colour":
   "`FMODE = 0` (written five times) and `BPLCON3 = 0`, both by the loader and "
   "by nothing else; ECS-style output on AGA silicon. **`LoadRGB4` and "
   "`LoadRGB32` both called zero times** — every colour comes from a copper "
   "`MOVE` or an IFF `CMAP`",

 "Graphics":
   "interleaved planar, **5 planes / 320×100 window** and **4 planes / "
   "320×200**, from the modulos `$A0` and `$78`. **16 of 32 colour registers "
   "are `$0000`** in the five-plane list. **3 copper lists** accepted from 16 "
   "loose and 4,448 rejected runs. Blitter: no FILL bit in any readable "
   "`BLTCON1`, no `$CA` minterm, 13 of 16 `BLTCON0`s register-loaded",

 "Text encoding":
   "**7-bit ASCII, measured: 0 bytes above `0x7F` in 3,893 bytes of display "
   "text**. Prose **0.068 % on disc, 0.054 % resident**. A **fourth string "
   "model**: a relocated longword page index over `[flag][col][row]TEXT` record "
   "chains, 71 records, 28 pages, **0 empty slots**",

 "Languages":
   "1 (EN), and no localisation of any kind",

 "Music":
   "**2 OctaMED `MMD0` modules** — 20 blocks/21-entry sequence and 4 blocks/"
   "3-entry sequence; **2 of 18 instrument slots empty**, **0 of 18 named** "
   "(the `iinfo` entry size is 2 bytes). 0 ProTracker, 0 The Player",

 "Save system":
   "**none** — no `$B80030`, no `nonvolatile.library` shipped or opened. The "
   "only persistent-looking structure is a five-name default high-score table in "
   "RAM",

 "Cut content":
   "**`THE SERIAL NO IS` / `GGGGGGGG I THINK`**, a live page of the credit "
   "table; `SNUFFLECAKE`; a pad combination that writes `COL!` into `$C0` and is "
   "never read back; **Commodore's `ConClip 37.7` pressed onto the disc** in "
   "unused floppy blocks (the disc's only `$VER:`); `SYS3` ×896 as a fill "
   "pattern; a `SPAM` memory probe with one branch patched out; "
   "`\\myth\\source\\screens\\ScreenA.lbm`; bootblocks dated **29/8/2004**; and "
   "the sequel `DAWN OF STEEL` named in the ending",
}
