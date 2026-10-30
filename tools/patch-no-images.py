#!/usr/bin/env python3
"""Drop inline PNG references from README.md and docs/07-graphics.md.

The other seventeen repositories in this set publish README.md, docs/, notes/,
tools/ and the .cue, and no image files, no extracted assets and no disc image.
This repository follows that convention: the renders are reproducible from the
disc with the tools that are published, and describing what they show is the
part that belongs in the documentation.

Anchors asserted unique; nothing is written if any is not.
"""
import io

# ---- README.md
P = 'README.md'
s = io.open(P, encoding='utf-8').read()

old = """![the title screen, decoded from frontend.pak](render/frontend-320x184.png)

This is the eighteenth disc"""
new = """This is the eighteenth disc"""
assert s.count(old) == 1, "README image anchor not unique"
s = s.replace(old, new, 1)

old = """`<name>.map` pairs the largest index in the 1,024-byte map is exactly
(length / 128) − 1. **Seven of seven.** Rendering settled the internal layout as
row-interleaved, and also refuted part of the arithmetic: seventeen of the
eighteen pieces are tile banks and the eighteenth, `frontend.pak`, is the
**320 × 184 title screen** above."""
new = """`<name>.map` pairs the largest index in the 1,024-byte map is exactly
(length / 128) − 1. **Seven of seven.** Rendering settled the internal layout as
row-interleaved, and also refuted part of the arithmetic: seventeen of the
eighteen pieces are tile banks and the eighteenth, `frontend.pak`, is the
**320 × 184 title screen** — the game's own name, drawn."""
assert s.count(old) == 1, "README geometry anchor not unique"
s = s.replace(old, new, 1)

old = """here: the repository contains the tools, the measurements and the renders. The
217 MB of Red Book audio is not published; per-track SHA-1s are, so the read is
reproducible from the disc."""
new = """here: the repository contains the tools, the measurements and the notes, and no
image files, extracted assets or disc image — the same convention as the other
seventeen repositories in this set. Every render described in the documentation
is reproducible from the disc with `tools/tilesheet.py` and `tools/planar.py`.
The 217 MB of Red Book audio is not published either; per-track SHA-1s are, so
the read is reproducible from the disc."""
assert s.count(old) == 1, "README scope anchor not unique"
s = s.replace(old, new, 1)
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print("patched %s" % P)

# ---- docs/07-graphics.md
P = 'docs/07-graphics.md'
s = io.open(P, encoding='utf-8').read()

old = """it is **29,440 = 160 × 184 exactly**, and it renders as the title screen:

![the title screen, decoded](../render/frontend-320x184.png)

So the corrected census"""
new = """it is **29,440 = 160 × 184 exactly**, and it renders as **the title screen**:
the character, and the words *ALFRED CHICKEN* with a `™`, drawn as artwork.

```
python3 tools/rnc.py extract/frontend.pak frontend.raw
python3 tools/planar.py frontend.raw title.png --w 320 --h 184 --planes 4 --interleaved
```

So the corrected census"""
assert s.count(old) == 1, "graphics image anchor not unique"
s = s.replace(old, new, 1)

old = """`render/babyp-tiles.png`, `woodp-tiles.png`, `scifip-tiles.png`: index renders
of three banks. `woodp` reads as clouds and timber, `babyp` as rounded blocks —
recognisable art, which settles the geometry question visually as well as
arithmetically. `render/chk-BABY.PAK+s0.png` and `render/chk-alfred+s775100.png`
confirm that the packed level archives and the streams embedded in `alfred` are
tile banks too: sprites and objects in the first, rock and platform texture in
the second."""
new = """Index renders of three banks, reproducible with

```
python3 tools/tilesheet.py extract/woodp.unpack woodp.png --across 16 --layout inter
```

`woodp` reads as clouds and timber, `babyp` as rounded blocks — recognisable art,
which settles the geometry question visually as well as arithmetically. The same
render applied to the unpacked `BABY.PAK` and to `alfred+s775100` confirms that
the packed level archives and the streams embedded in `alfred` are tile banks
too: sprites and objects in the first, rock and platform texture in the second."""
assert s.count(old) == 1, "graphics render anchor not unique"
s = s.replace(old, new, 1)

old = """`render/babyp-plane0.png` … `plane3.png`: four coherent monochrome images, none
a solid stencil, none a stream of noise. Four real bitplanes."""
new = """`tools/tilesheet.py extract/babyp.unpack babyp --planes` writes one monochrome
PNG per bitplane: **four coherent images, none a solid stencil, none a stream of
noise. Four real bitplanes.**"""
assert s.count(old) == 1, "graphics planes anchor not unique"
s = s.replace(old, new, 1)

old = """* the tile renders in `render/` are therefore **index renders on a neutral
  16-step grey ramp**, not colour renders, and are labelled as such. Any colour
  claim would be invention;"""
new = """* the tile renders `tools/tilesheet.py` produces are therefore **index renders
  on a neutral 16-step grey ramp**, not colour renders. Any colour claim would
  be invention;"""
assert s.count(old) == 1, "graphics ramp anchor not unique"
s = s.replace(old, new, 1)

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print("patched %s" % P)
