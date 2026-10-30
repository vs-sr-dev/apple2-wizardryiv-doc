#!/usr/bin/env python3
"""CDXL stream geometry, validated by arithmetic rather than by trusting fields.

The 32-byte CDXL chunk header is read as:

    0  u8  type          1 = standard
    1  u8  info
    2  u32 chunkSize     bytes of this chunk, header included
    6  u32 currentChunk
    10 u32 previousChunk
    14 u16 width
    16 u16 height
    18 u16 planes
    20 u16 paletteSize   bytes
    22 u16 audioSize      bytes
    24 8 bytes, zero

The check that the reading is right is that

    chunkSize - 32 - paletteSize - audioSize == planes * height * ceil(width/16)*2

comes out exactly, and that the file length is an exact multiple of chunkSize.
Both hold on all three streams on this disc, so the frame count is exact and the
stream is seekable by multiplication.

Usage:  python3 tools/cdxl.py <file> [<file> ...] [--frames N]
"""
import sys, struct, os, argparse


def rowbytes(w):
    return ((w + 15) // 16) * 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--frames", type=int, default=3)
    ap.add_argument("--rate", type=float, default=150.0,
                    help="sectors/second the startup-sequence asks for (xlspeed)")
    a = ap.parse_args()

    for p in a.files:
        d = open(p, "rb").read()
        t, info = d[0], d[1]
        cs, cur, prev = struct.unpack_from(">III", d, 2)
        w, h, planes, pal, aud = struct.unpack_from(">HHHHH", d, 14)
        rest = struct.unpack_from(">8s", d, 24)[0]
        video = cs - 32 - pal - aud
        expect = planes * h * rowbytes(w)
        nframes = len(d) / cs if cs else 0
        print("=== %s : %d bytes ===" % (os.path.basename(p), len(d)))
        print("  type %d  info %d  chunkSize %d  currentChunk %d  previousChunk %d"
              % (t, info, cs, cur, prev))
        print("  %dx%d, %d planes, palette %d bytes (%d colours), audio %d bytes/frame"
              % (w, h, planes, pal, pal // 2, aud))
        print("  bytes/row %d, video payload %d, planes*h*rowbytes = %d  -> %s"
              % (rowbytes(w), video, expect, "EXACT" if video == expect else "MISMATCH"))
        print("  reserved tail %s" % ("zero" if rest == b"\0" * 8 else rest.hex()))
        print("  file / chunkSize = %.4f  -> %s"
              % (nframes, "%d whole frames" % nframes if len(d) % cs == 0 else "NOT a whole number"))
        if cs:
            fps = a.rate * 2048.0 / cs
            print("  at xlspeed %g (sectors/s): %.2f frames/s, %.1f s of video, audio %.0f Hz"
                  % (a.rate, fps, (len(d) / cs) / fps, aud * fps))
        # walk a few chunks and confirm the size is constant
        sizes = []
        o = 0
        for i in range(a.frames):
            if o + 32 > len(d):
                break
            s = struct.unpack_from(">I", d, o + 2)[0]
            cc, pc = struct.unpack_from(">II", d, o + 6)
            sizes.append((o, s, cc, pc))
            o += s
        for o, s, cc, pc in sizes:
            print("    chunk at %9d size %d currentChunk %d previousChunk %d" % (o, s, cc, pc))
        # constant-size check over the whole file
        o = 0
        n = 0
        const = True
        while o + 32 <= len(d):
            s = struct.unpack_from(">I", d, o + 2)[0]
            if s != cs:
                const = False
                break
            o += s
            n += 1
        print("  walked %d chunks, all chunkSize %d: %s, ends at %d of %d"
              % (n, cs, const, o, len(d)))
        print()


if __name__ == "__main__":
    main()
