#!/usr/bin/env python3
"""Parse the chunk directory that Myth's floppy images keep in block 2.

Block 2 of each image (byte offset 0x400) is a table of (offset, length)
longword pairs, terminated by a zero offset.  Every entry is validated
against the image: the offset must be inside the image, 512-aligned, the
length non-zero, and offset+length must not run past the end.

The script then builds a coverage map of the whole 901,120-byte image so the
regions the table does *not* claim can be read separately -- which is where
this disc's leftovers are.

Usage: python3 tools/mythdir.py <image> [--dump DIR]
"""
import sys, os, struct, hashlib, argparse

SIZE = 901120
BS = 512


def parse(d, base=0x400, limit=0x800):
    ents, off = [], base
    while off + 8 <= limit:
        o, n = struct.unpack_from(">II", d, off)
        if o == 0 and n == 0:
            break
        ents.append((off, o, n))
        off += 8
    return ents


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('image')
    ap.add_argument('--dump')
    a = ap.parse_args()
    d = open(a.image, 'rb').read()
    ents = parse(d)
    print("%s  %d bytes" % (os.path.basename(a.image), len(d)))
    print("%-4s %-9s %-9s %-9s %-7s %s" %
          ("#", "offset", "length", "end", "aligned", "status"))
    claimed = bytearray(len(d))
    good = 0
    for i, (tbl, o, n) in enumerate(ents):
        end = o + n
        ok = (o < len(d)) and (end <= len(d)) and n > 0
        if ok:
            good += 1
            for k in range(o, end):
                claimed[k] = 1
        print("%-4d 0x%06x  0x%06x  0x%06x  %-7s %s" %
              (i, o, n, end, "yes" if o % BS == 0 else "NO",
               "ok" if ok else "OUT OF RANGE"))
        if a.dump and ok:
            os.makedirs(a.dump, exist_ok=True)
            p = os.path.join(a.dump, "%s.%02d" % (os.path.basename(a.image), i))
            open(p, 'wb').write(d[o:end])
    print()
    print("entries %d, valid %d" % (len(ents), good))
    nc = sum(claimed)
    print("claimed by table  %7d B  %.2f%%" % (nc, 100.0 * nc / len(d)))
    print("unclaimed         %7d B  %.2f%%" % (len(d) - nc,
                                               100.0 * (len(d) - nc) / len(d)))
    runs, i = [], 0
    while i < len(d):
        if not claimed[i]:
            j = i
            while j < len(d) and not claimed[j]:
                j += 1
            runs.append((i, j))
            i = j
        else:
            i += 1
    print()
    print("unclaimed runs:")
    for s, e in runs:
        seg = d[s:e]
        z = "all zero" if not any(seg) else ""
        print("  0x%06x..0x%06x  %7d B  blocks %4d..%-4d  %s" %
              (s, e, e - s, s // BS, (e - 1) // BS, z))


if __name__ == '__main__':
    main()
