#!/usr/bin/env python3
"""Correct two claims in docs/07-graphics.md that a later measurement refuted.

Both errors came from the same mistake: reading "zero stored copper lists" as
"the engine stores no display state at all".  It stores none in a copper list;
it writes BPLCON0, BPLCON2 and BPLCON3 as immediates straight into the custom
registers, and `intro` calls both palette functions.

  1. "Not one LoadRGB4 (-192) and not one LoadRGB32 (-882) call either" is
     wrong.  `intro` calls **both, once each** -- which makes this the third
     disc in the set to call both, after Gunship and Superfrog.
  2. "no stored ... BPLCON0" is wrong.  There are three BPLCON0 immediates, and
     they carry the bitplane count, which is a third independent confirmation
     of the four-plane geometry.

Anchors asserted unique.
"""
import io

P = 'docs/07-graphics.md'
s = io.open(P, encoding='utf-8').read()

old = """The engine therefore **builds its copper lists at run time**, which is the Fire &
Ice answer. Consequences, stated rather than worked around:

* there is **no stored palette anywhere on this disc**. Not one `LoadRGB4`
  (−192) and not one `LoadRGB32` (−882) call either, so the palette question has
  no answer here at all — the colours come from copper `MOVE`s built in code;
* the tile renders `tools/tilesheet.py` produces are therefore **index renders
  on a neutral 16-step grey ramp**, not colour renders. Any colour claim would
  be invention;
* the bitmap width cannot be read from a copper `BPLxMOD` because there is no
  copper list to read it from."""

new = """The engine therefore **builds its copper lists at run time**, which is the Fire &
Ice answer. But "no stored copper list" is not "no stored display state", and
conflating the two is an error this document made and this section corrects:
the display registers are written as **immediates straight into the custom chip**,
and the palette functions *are* called.

### The display registers, written as immediates

| file | offset | register | value | reading |
|---|---|---|---|---|
| `alfred` | 0x0551C0 | BPLCON0 | `$4200` | **BPU = 4** |
| `alfred` | 0x055262 | BPLCON0 | `$4200` | **BPU = 4** |
| `alfred` | 0x0551C6 | BPLCON2 | `$003F` | |
| `alfred` | 0x055268 | BPLCON2 | `$0038` | |
| `alfred` | 0x0551CC | BPLCON3 | `$1400` | an **AGA** register, written with PF2OF set |
| `intro` | 0x03862C | BPLCON0 | `$5200` | **BPU = 5** |
| `intro` | 0x038632 | BPLCON2 | `$0063` | |

The bitplane count is computed with the full formula, `BPU = ((v >> 12) & 7) |
(((v >> 4) & 1) << 3)`, because bit 4 is BPU3 and a scan reading only bits 14–12
misreads eight-plane screens as zero-plane ones — three such cases exist in the
set.

**`alfred` runs a four-bitplane display and `intro` a five-bitplane one.** The
four is a **third independent confirmation** of the tile geometry derived below,
arriving from the hardware register rather than from a file length or a map
index. The two executables differ here as they differ everywhere else.

`BPLCON3 = $1400` in `alfred` is an AGA-only register carrying a real value, so
this is not an ECS-style display on AGA silicon the way Universe and Myth were.
EHB does not arise: it needs six planes and neither screen has them.

### The palette

* **`intro` calls `LoadRGB4` once and `LoadRGB32` once.** That makes this the
  **third disc in the set to call both**, after Gunship and Superfrog — and
  unlike Superfrog, where both calls were in a manual viewer and no game engine
  used either, here they are in a shipped game executable.
* **`alfred` calls neither**, and calls `LoadView` four times. Its colours come
  from copper `MOVE`s built in code.

So the palette question has two different answers on one disc, one per
executable, and no palette is stored anywhere as data.

Two consequences that do stand:

* the tile renders `tools/tilesheet.py` produces are **index renders on a
  neutral 16-step grey ramp**, not colour renders, because no palette is stored
  with the tiles. Any colour claim would be invention;
* the bitmap width cannot be read from a copper `BPLxMOD`, because there is no
  stored copper list to read it from."""

assert s.count(old) == 1, "copper consequences anchor not unique"
s = s.replace(old, new, 1)

old2 = """That is the Myth shape and it is a property of the engine, not a failed check:
**this engine computes its blitter control words rather than storing them.** Six
of 165 blitter writes carry a literal, and the six that do describe two trivial
blits — a copier and a clearer. How it draws its sprites is not statically
readable, and saying so is the honest result."""

new2 = """That is the Myth shape and it is a property of the engine, not a failed check:
**this engine computes its blitter control words rather than storing them.** Six
of 165 blitter writes carry a literal, and the six that do describe two trivial
blits — a copier and a clearer. How it draws its sprites is not statically
readable, and saying so is the honest result.

Note the contrast with the display registers above, which *are* written as
immediates. The engine is not uniformly dynamic: it hardcodes the screen mode
and computes the drawing. That distinction only appears if both are measured,
and this document initially got it wrong by generalising from the copper lists."""

assert s.count(old2) == 1, "blitter conclusion anchor not unique"
s = s.replace(old2, new2, 1)

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print("patched %s" % P)
