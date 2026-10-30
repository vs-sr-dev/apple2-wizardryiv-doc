#!/usr/bin/env python3
"""Correct docs/07-graphics.md after rendering falsified part of it.

What happened.  The geometry section claimed "eighteen of eighteen divide
exactly by 128" and presented that as the evidence for a 16x16x4 tile format.
Divisibility by 128 is *necessary* for that format but it is not *sufficient*:
rendering the eighteen pieces shows that seventeen are tile banks and one --
`frontend.pak`, and therefore also its byte-identical copy inside `alfred` --
is not a tile bank at all.  It is a 320x184 four-bitplane screen: the title
screen, 160 bytes per row x 184 rows = 29,440 bytes exactly.

That is the checklist's own rule arriving on my own measurement: an arithmetic
fit is a candidate, and the render is what decides.  The correction strengthens
the four-plane conclusion rather than weakening it, because the title screen
confirms four planes by an entirely independent route.

Anchors asserted unique; nothing is written if any is not.
"""
import io

P = 'docs/07-graphics.md'
s = io.open(P, encoding='utf-8').read()

old = """**Eighteen of eighteen divide exactly by 128. Five of eighteen leave a remainder
on 160.** 128 = 16 × 16 pixels ÷ 8 bits × **4 planes**. Four planes is the only
count consistent with every piece."""

new = """**Eighteen of eighteen divide exactly by 128. Five of eighteen leave a remainder
on 160.** 128 = 16 × 16 pixels ÷ 8 bits × **4 planes**. Four planes is the only
count consistent with every piece.

**But divisibility by 128 is necessary, not sufficient, and rendering proved
it.** Of the eighteen, **seventeen render as coherent tile art and one does
not**: `frontend.pak+s0` (and therefore its byte-identical copy inside `alfred`
at offset 760,060) is noise at the tile geometry. Read instead as a single
screen — 320 pixels wide, 4 bitplanes, row-interleaved, 160 bytes per row —
it is **29,440 = 160 × 184 exactly**, and it renders as the title screen:

![the title screen, decoded](../render/frontend-320x184.png)

So the corrected census is **seventeen tile banks and one 320 × 184 screen**,
and the arithmetic alone would have filed the screen as 230 tiles. The render is
what decides, which is the rule this pipeline applies to inherited tools and
applies here to its own measurement.

The screen also confirms the plane count by a completely independent route: at
four planes it consumes the file exactly and produces a legible image; at any
other count it does neither."""

assert s.count(old) == 1, "128-divisibility anchor not unique"
s = s.replace(old, new, 1)

old2 = """`render/babyp-tiles.png`, `woodp-tiles.png`, `scifip-tiles.png`: index renders
of three banks. `woodp` reads as clouds and timber, `babyp` as rounded blocks —
recognisable art, which settles the geometry question visually as well as
arithmetically."""

new2 = """`render/babyp-tiles.png`, `woodp-tiles.png`, `scifip-tiles.png`: index renders
of three banks. `woodp` reads as clouds and timber, `babyp` as rounded blocks —
recognisable art, which settles the geometry question visually as well as
arithmetically. `render/chk-BABY.PAK+s0.png` and `render/chk-alfred+s775100.png`
confirm that the packed level archives and the streams embedded in `alfred` are
tile banks too: sprites and objects in the first, rock and platform texture in
the second.

### The title screen, and the title verified from the disc

`frontend.pak` decodes to the game's title screen: the character, and the words
**ALFRED CHICKEN** with a `™` after them, drawn as artwork.

This is the first place on the disc where the game states its own name in a form
a human reads. It matters for a reason the brief is explicit about: the title
was told to me by the person who handed me the disc, and that is a claim, not a
source. The PVD calls the volume `Alfred` — six characters, one word. The
artwork on the label says `ALFRED CHICKEN`, but artwork is the carrier, not the
data. **This is the disc's own copy of its title, in its own bytes**, and it
agrees.

It also answers where a platformer with almost no text keeps its words: it
draws them. See `docs/09-text-and-strings.md`."""

assert s.count(old2) == 1, "render paragraph anchor not unique"
s = s.replace(old2, new2, 1)

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print("patched %s" % P)
