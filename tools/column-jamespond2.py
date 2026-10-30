# -*- coding: utf-8 -*-
"""The James Pond 2: Codename RoboCod (CD32) column for the section 10 table.

The nineteenth disc: Millennium Interactive, mastered 1993-08-17. A 195 MiB
data track of which 65.55 % is a hole of exactly 128.000000 MiB and 93.90 % of
the file bytes are CDXL video, over a 1.03 MB game.
"""

TITLE = "**James Pond 2: RoboCod (1993)**"

CELLS = {
 "Publisher / studio":
   "**`Millennium Interactive Ltd`** in the PVD publisher field — a label new "
   "to this set — and **no developer is named anywhere on the disc**: not in "
   "any descriptor field, not in a `$VER:`, not in either credit list. Only "
   "*people*: `Chris Sorrell` (original design, programming, graphics), "
   "`Dean Ashton` (the A1200/CD32 and AGA conversion, and the preparer field), "
   "`Richard Joseph` (music), `Steve Bak` (maps), `Steve Loughran` (the book "
   "reader) and `Wayne D. Lutz` (the CDXL player, by `$VER:`). The studio has "
   "to be recovered from a **comment in the boot script**, which is a first",

 "Master cut":
   "**PVD 1993-08-17 10:12:55**, 5 h 14 m 49 s after the newest file it "
   "indexes — an ordinary, healthy gap. Root directory record 1993-08-15 "
   "16:47:26, *earlier* than two files, because AmigaDOS directory times "
   "follow their own contents and the two late files live in `/C` and `/S`, "
   "whose records carry their exact times. `.TM` says © 1993 and nothing "
   "contradicts it. **And the boot script's own prose dates check out**: "
   "\"Sunday 15th August 1993, at 10:05am\" (it was a Sunday; three "
   "directories rebuilt 36–45 min later), \"Friday 13th\" (it was; "
   "`Intro.cdxl` stamped that evening), \"1:30am 14.07.93\" (four files "
   "stamped 00:03–01:18 that morning)",

 "Tracks":
   "**8 — 1 data (`MODE1/2048`) + 7 audio**, with `PREGAP 00:02:00` on "
   "track 02 and no other pregap declared",

 "Data track sectors":
   "**100,125 in the image — 205,056,000 bytes, an exact multiple of the "
   "sector size**, only the second such image in the set after Superfrog. "
   "Declared volume **99,975**, so a **150-sector overrun**, all zero — and "
   "150 is *numerically identical* to the declared track-2 pregap, which an "
   "image cannot disambiguate (open question)",

 "Audio":
   "**966.000 s exactly, 72,450 sectors, 16:06**, 7 tracks. Every track a "
   "whole number of *sectors*; **4 of 7 a whole number of seconds** (180, "
   "230, 90, 71) and the two longest are the two roundest — so the round ones "
   "were **cut to a length** and the ragged ones taken as they came, the "
   "opposite of the prediction. Lead-in 0.16–0.51 s on all seven, trailing "
   "1.56–1.84 s on six and **exactly zero on track 8**. Peaks 21,236–32,767, "
   "two at full scale. **All seven reachable**",

 "Share of a 333,000-sector CD":
   "**51.87 %** — 172,725 sectors (100,125 data + 150 pregap + 72,450 audio). "
   "Data 30.07 %, audio 21.76 %. Half the disc unused **and** 65.55 % of the "
   "used data track empty",

 "Files / directories":
   "**135 / 6** (`/C`, `/CDXL`, `/Devs`, `/Libs`, `/Pages`, `/S`), of which "
   "**115 are electronic-book pages** and **3 are CDXL streams**. The game is "
   "**three files**",

 "Bytes on disc / unpacked":
   "whole tree **70,262,959** — but **93.90 % of it is CDXL video** and "
   "4.38 % is the manual, so the disc total is meaningless for the band. The "
   "**game is 1,033,508 on disc / 1,258,076 resident** (1,211,470 on disc if "
   "the whole boot chain counts), and `RoboCod` alone is **959,956 / "
   "1,185,496**. **Breaks Alfred Chicken's floor by 18.1 % on disc and 23.1 % "
   "resident**, the second time in two discs. Expansion **1.217×, the lowest "
   "measured** — and structurally so, because it is a `BSS` declaration and "
   "not a decompression",

 "Compression":
   "**none.** Thirteen container magics over all **205,056,000** raw bytes "
   "return **0**; no file's first longword equals its size or size−4; **1 of "
   "135** above 6.7 entropy and it is an 11-hunk executable with a 256-colour "
   "title screen in it. The 115 manual pages use IFF **`ByteRun1`** (ratio "
   "0.404, 7.36 MB → 2.98 MB), which is a format feature and not a packer. "
   "**And there is a mechanism**: all three of the game's hunks are `CHIP`, "
   "1,185,496 bytes of a 2 MB budget, so there is no room for a decrunch "
   "buffer even if there were a reason",

 "PVD system id":
   "`CDTV`",

 "PVD application id":
   "**`RoboCod_CD32`** — the title *and the console*, a shape no other disc "
   "here uses; volume identifier `RoboCod_CD`, so the master spells the game "
   "two different ways in two adjacent fields",

 "Cue `CATALOG`":
   "**`0000000000000`** — the **fifth** disc in the set with the thirteen "
   "zeros. Not confirmable from an image, which carries no subchannel; "
   "transfers by provenance from [Alfred Chicken]'s physical read",

 "Mastering tool":
   "ISOCD 1.04 (Pantaray)",

 "Preparer field":
   "**`Dean Ashton - ISOCD 1.04 by Pantaray, Inc. USA -`** — a **sixth named "
   "individual**, and *not Pocock leaves 32* is now **14 of 14**. It is also "
   "the **first disc where the man in that field identifies himself on the "
   "disc, in the first person**: the boot script's 44-line comment is signed "
   "`by the master of the kludged code, Dean Ashton`. And he is the "
   "**conversion programmer**, credited by both credit screens — so the field "
   "can record a studio's own programmer, a **sixth owner-type** after "
   "operator, bureau, company, contractor and menu author",

 "Duplicate PVD":
   "yes, sectors 16 and 17, **byte-identical in all 2,048 bytes**; terminator "
   "at 18",

 "Volume starts at LBA":
   "19 (path tables 19 and 20, `.TM` 21, root directory 22) — **but the first "
   "file is at 65,559**, because LBA 23–65,558 is a hole",

 "`.TM` block at":
   "sector 21, 2,048 bytes, from the pointer rather than the constant: `TM` "
   "tag at app-use offset 5 (absolute 888), constant `0x0014`, length "
   "`0x00000800`, LBA `0x00000015`",

 "`.TM` contents":
   "**identical** — all three SHA-1s match "
   "(`c5ffcef2…` / `8d841151…` / `690aae24…`). **Seventeen CD32-era discs "
   "with the Commodore banner and one with the CDTV driver.** No `.TM` file "
   "in the root",

 "Unclaimed sectors in the volume":
   "**32, all zero, at LBA 99,943–99,974** — the non-`Pocock` value, on a new "
   "name. **Plus a 65,536-sector hole at LBA 23–65,558** — "
   "**134,217,728 bytes = 128.000000 MiB, 2^16 sectors, every byte verified "
   "zero** — which is **65.55 %** of the declared volume and the **third "
   "*round* hole** in the set after 50.000000 MiB and 100 MiB. With the CDXL "
   "padding, the trailing run and the overrun, **69.75 % of the data track is "
   "zero**",

 "Timestamps":
   "**two epochs, and the disc is otherwise clean.** One file in the 1978 "
   "AmigaDOS epoch (`C/SetPatch`, 1978-02-01 15:00:02, falsified by its own "
   "`$VER: setpatch 40.2 (17.2.93)`); everything else real, 1993-06-07 to "
   "1993-08-17, a legible ten-week build log. **No 1980 MS-DOS epoch** — "
   "on a disc whose largest asset was demonstrably converted from PC-side "
   "16-bit TARGA captures, which is a real negative for that candidate epoch. "
   "The directory records are a **second** build log agreeing with the first",

 "SetPatch":
   "**40.2 (17.2.93)**, `b308c42d7193ba8ec99b8813910d8099e121e17d`, stamped "
   "1978-02-01. Neither the version nor the bytes match [Alfred Chicken]'s "
   "40.14 (7.10.93)",

 "First stage":
   "the **boot script itself**, which is a shell-level main loop — `Lab "
   "select` / `RoboSelect` / three `if` blocks on an `ENV:` variable / `Skip "
   "select BACK`, forever — and then `RoboLoader`: 1 hunk, 93 relocations, 45 "
   "library calls, whose whole job is to blank the screen and start the game. "
   "The game's own prologue is the requirements list: `ExecBase->AttnFlags` "
   "tested for 68040/030/020 into three flag bytes read back with **one "
   "`tst.l`** (exit code 100 otherwise), five `OpenLibrary` at **V39**, and "
   "`GfxBase->ChipRevBits0 & $0C == $0C` — **both AGA chips or refuse to "
   "run**, in four instructions",

 "Game executable":
   "`RoboCod`, **3 hunks, every one `CHIP`**: 324,632 `CODE` + 613,612 `DATA` "
   "+ 247,252 `BSS` = **1,185,496 resident**. 5,399 relocations "
   "(**16.63/KB of code**), of which 133 in the 600 KB data hunk and **all of "
   "them in its first 528 bytes**. 69 library calls. **No `HUNK_SYMBOL`, no "
   "`HUNK_DEBUG`** — and a string in the file says "
   "`I'm not stupid enough to leave debug symbols in`, which is true. "
   "**Everything is in this one file**: 86 levels, all art, all sound, a "
   "12-byte-per-level table of 86 records, 16 small jump tables (73 branches)",

 "Libraries opened":
   "**five by the game at V39** — `dos`, `intuition`, `graphics`, `lowlevel`, "
   "`nonvolatile` (the last allowed to fail) — plus `cd.device` **twice** and "
   "`input.device`. Across the five programs: **ten libraries and five "
   "devices**, including `gadtools`, `asl`, `iffparse`, `utility`, "
   "`console.device`, `audio.device` and `cdtv.device`. **AmigaDOS is alive "
   "from the first instruction to the last in every one of them** — the "
   "credit line `A1200/CD32 OS-Friendly conversion` is measurable, and the "
   "mechanism is two named interrupt servers, `ROBO_VERTB_Server` and "
   "`ROBO_COPER_Server`, hung off Exec's own chains",

 "`freeanim.library`":
   "opened by **`C/FreeAnimation`, a purpose-built 120-byte wrapper** whose "
   "entire program is `OpenLibrary(\"freeanim.library\", 0)` followed "
   "immediately by `CloseLibrary` — opening it *is* the effect — carrying its "
   "own `$VER: FreeAnimation 1.0 (7.6.93)`. **Third disc** to reach it, and "
   "not byte-identical to the `C/FreeAnim` that Liberation and Universe share",

 "Akiko":
   "**untouched — 0 / 0 / 0**: zero `$00B80000` pointer loads across **all "
   "eight** address registers, zero `$B80030`, zero C2P port "
   "`$B80038`/`$B8003C`, in all five programs. C2P merge constants **122 as "
   "data, 0 as immediates**. The drive is reached through `cd.device` and the "
   "save EEPROM through `nonvolatile.library`, so even the two non-graphics "
   "uses go through Commodore's layers",

 "Colour":
   "**24-bit, on a 32-colour screen.** The one stored copper list writes "
   "`COLOR00`..`COLOR31` **twice**, with `BPLCON3` `$0000` then `$0200` "
   "between the passes — AGA `LOCT` pairs — so 32 simultaneous colours chosen "
   "from 16.7 million. **Neither `LoadRGB4` nor `LoadRGB32` is called**: the "
   "palette reaches the hardware only from the copper. Elsewhere on the disc: "
   "the CDXL streams carry a **fresh 32-colour palette in every one of 2,530 "
   "chunks** (a frame-by-frame quantiser) while the 115 manual pages share "
   "**one** byte-identical 256-colour `CMAP` (an artist), and `ident.cdxl` is "
   "**HAM6** — 6 planes with a 16-colour palette, identified from the header "
   "arithmetic rather than by rendering",

 "Graphics":
   "interleaved planar, **5 bitplanes** (`BPLCON0 $5201`, `BPU3` clear) with a "
   "**4-plane region** (`$4201`); `DDF $30/$C8` = 320 px, `DIW` rows 44–252. "
   "`BPL1PT`..`BPL5PT` re-pointed **five times** down the screen, 8 sprites, "
   "and **14 copper `WAIT`s making two seven-line `COLOR01`/`COLOR02` ramps** "
   "at rows 109–115 and 228–234. **One** stored copper list (820 B) out of "
   "6,122 candidate runs rejected. Blitter: **`BLTCON1 = $0000` on every "
   "readable write** — no fill, no line, no descending — minterms `$F0` and "
   "`$FC` only and **no `$CA` anywhere**, so not even an ordinary masked bob. "
   "Video: 320 × 100 × 5 scan-doubled, and 250 × 200 × 6 HAM6",

 "Text encoding":
   "**none — a sixth string model, and the mirror of [Alfred Chicken]'s.** "
   "**10,875 bytes** of ASCII prose on a 195 MiB volume (0.0155 % of the file "
   "bytes), and the **largest single contributor is the boot script** at "
   "1,878 bytes because 44 of its lines are a comment. The disc's 2.93 MB "
   "manual contains **no characters at all**: it is 115 IFF ILBM pictures of "
   "typeset text, so string count, encoding and accent handling all return "
   "zero and the localisation has to be measured **in pixels**",

 "Languages":
   "**3 for the manual, 1 for the game** — the first disc here where those "
   "differ. `uk` 37 pages, `fr` 38, `gr` 40 (German runs 8.1 % long); **one "
   "page of 115 byte-identical across all three**, and it is the largest and "
   "inkiest, i.e. the only illustration with no text; mean **12.94 % of "
   "pixels differ** between the English and French copies of the same page. "
   "Chapter indices byte-identical for EN and FR, shifted by one page for DE. "
   "A Deluxe Paint **`DPPS`** chunk on 17 pages — 10 EN, 7 FR, **0 DE** — "
   "names the paint package and splits the artwork production. The **game** "
   "has no language selection at all",

 "Music":
   "**7 Red Book tracks and every one of them reachable**, from **byte 11 of "
   "an 86-record, 12-byte-per-level table**, where **bit 7 of the music id "
   "chooses Red Book or Paula** — and all 86 choose Red Book. Tracks 3–8 used "
   "15/14/19/9/24/5 times, track 2 from a constant in the front end. **The "
   "TOC is never read**: exactly three CD commands on the disc — "
   "`CD_PLAYTRACK` (37) and `CD_PAUSE` (40) twice, pause and resume — and no "
   "`CD_INFO`, `CD_TOCMSF`, `CD_TOCLSN` or `CD_GETNUMTRACKS`, with a bare "
   "**250-frame countdown** re-issuing the play. **No ProTracker, OctaMED or "
   "The Player module, no IFF `8SVX`, no PCM file**: effects are raw inside "
   "the chip data hunk. Separately, the CDXL player runs **1,122 B/frame of "
   "8-bit mono on two Paula channels** with the period corrected from buffer "
   "drift every interrupt",

 "Save system":
   "**CD32 serial EEPROM through `nonvolatile.library`** — project "
   "`RoboCod Data`, item `High Score`, at hunk `$7fc` and `$809`. No password "
   "system anywhere. Where [Universe] bit-bangs the same hardware through "
   "Akiko's I²C port because it has no Exec left, this disc calls Commodore's "
   "library: the two ends of the same abstraction stack",

 "Cut content":
   "**none identified**, and all three menu branches are reachable — the "
   "`FI5H` token that looked unreachable from the boot script alone is in "
   "`RoboSelect`, and page 1 of the book shows `FI5H FILE` is its **title**. "
   "Two things are shipped and not reached: an in-game level selector "
   "(`ROBOCOD MAP SELECT!`, `CURR. SECTION`, `SECTION NUMBER?`) whose "
   "reachability is open, and an **`ExtDebug.port`** message port in the book "
   "reader — the second shipped debugger hook in the set after [Banshee]'s "
   "`DebugDisk:`, and the first inside a binary rather than in a script",
}
