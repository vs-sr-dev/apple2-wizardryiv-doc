#!/usr/bin/env python3
"""Render one electronic-book page so a human can read it.

This repository ships measurements and the code that reproduces them, and no
images. Two questions about the book cannot be answered by measurement at all
— which language `gr` is, and what the book is called — because the pages
contain no characters: they are 320 x 200 eight-bitplane pictures of typeset
text. So the answer to those two is "render one and look", and this is the
renderer rather than the render.

The page is unpacked with the same code the measurements use
(tools/pagediff.py), so a picture produced here and a percentage quoted in
docs/09-text-and-the-ebook.md come from one decoder.

The vertical scale of 1.2 is the 44:52 pixel aspect in the BMHD, so the output
looks like the display rather than like the file.

Usage:  python tools/render.py extract/Pages/ebook.uk.0001 [out.png]
"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pagediff import unpack, chunks


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(src) + '.png'
    from PIL import Image
    d = open(src, 'rb').read()
    ch, order = chunks(d)
    w, h, planes, px = unpack(d)
    cmap = ch[b'CMAP']
    im = Image.frombytes('P', (w, h), bytes(px))
    im.putpalette(cmap[:768])
    im = im.convert('RGB').resize((w * 2, int(h * 2 * 1.2)), Image.LANCZOS)
    im.save(out)
    print("%s : %d x %d, %d planes, %d-byte CMAP, chunks %s -> %s"
          % (os.path.basename(src), w, h, planes, len(cmap), ' '.join(order), out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
