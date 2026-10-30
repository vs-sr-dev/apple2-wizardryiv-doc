"""Decode Prey's frame files: 160 x 128, four *separated* bitplanes, 10240
bytes per frame, no header anywhere.

Every animation family on the disc uses the same frame -- PREYDOOR/AIRnnn,
DRSnnn, TAKEOFF*, PREYDATA/BDLnnn, PREYLOCS/RFnnnnnn, LOCAnnn, ENDn.  The
file is a fixed-size buffer, so len(file) // 10240 is the number of *slots*,
not the number of real frames; the tail is whatever the converter's buffer
happened to hold.  --sheet renders every slot so you can see where the real
frames stop.

    python tools/frames.py <file> [--sheet out.png] [--cols 8] [--scale 2]
"""
import argparse, os, sys
import numpy as np
from PIL import Image

W, H, PLANES = 160, 128, 4
BPR = W // 8
FRAME = BPR * H * PLANES          # 10240


def frames(data):
    """Yield each 10240-byte slot as an (H, W) array of 4-bit indices."""
    for i in range(len(data) // FRAME):
        blk = np.frombuffer(data, dtype=np.uint8, count=FRAME,
                            offset=i * FRAME).reshape(PLANES, H, BPR)
        bits = np.unpackbits(blk, axis=2)
        img = np.zeros((H, W), np.uint8)
        for p in range(PLANES):
            img |= bits[p] << p
        yield img


def looks_like_a_bitmap(raw):
    """Uncleared buffer tails are noise; a real plane has byte runs.

    Measured on the raw plane bytes, not on the decoded pixel indices: a
    rendered frame is dithered and noisy at pixel level either way, while
    the *bytes* of a real bitplane repeat and the bytes of stale buffer do
    not.  Real frames on this disc score 0.25..0.95, stale slots 0.02..0.06.
    """
    f = np.frombuffer(raw, dtype=np.uint8)
    return float((f[:-1] == f[1:]).mean()) > 0.20


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('path')
    ap.add_argument('--sheet')
    ap.add_argument('--cols', type=int, default=8)
    ap.add_argument('--scale', type=int, default=2)
    a = ap.parse_args()

    data = open(a.path, 'rb').read()
    fs = list(frames(data))
    real = [i for i in range(len(fs))
            if looks_like_a_bitmap(data[i * FRAME:(i + 1) * FRAME])]
    print('%s: %d bytes = %d slots of %d + %d spare'
          % (os.path.basename(a.path), len(data), len(fs), FRAME, len(data) % FRAME))
    print('  slots that look like bitmaps: %d (highest %s)'
          % (len(real), max(real) if real else '-'))

    if a.sheet:
        cols = a.cols
        rows = (len(fs) + cols - 1) // cols
        sh = np.zeros((rows * H, cols * W), np.uint8)
        for i, f in enumerate(fs):
            sh[(i // cols) * H:(i // cols) * H + H,
               (i % cols) * W:(i % cols) * W + W] = f * 17     # 4 bits -> 8
        im = Image.fromarray(sh)
        if a.scale != 1:
            im = im.resize((im.width * a.scale // 2, im.height * a.scale // 2),
                           Image.NEAREST)
        im.save(a.sheet)
        print('  wrote', a.sheet)


if __name__ == '__main__':
    main()
