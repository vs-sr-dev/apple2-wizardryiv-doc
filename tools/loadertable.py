#!/usr/bin/env python3
"""Dump the loader's file table out of `bans.exe`.

The table is a run of variable-length records in the data area of hunk 0:

    +0  unpacked size of the file, 4 bytes big-endian
    +4  floppy disk number, 1 byte (2, 3, 4 ... and 1 for the cut-scene set)
    +5  one flag byte, 0x01 throughout
    +6  the path, NUL-terminated, padded to an even offset

The path is always `bansheeN:<name>`, and `bansheeN:` is one of the four
volume names the boot script assigns to `CD0:` -- so the table is the
four-floppy layout of the A1200 release, carried onto the compact disc
unchanged.

A thirty-eighth name follows the last record with **no record header at
all** and under a different volume-name convention.  See
`docs/11-leftovers.md`.

    python3 tools/loadertable.py <bans.exe> [start] [end]
"""
import sys, struct


def main():
    path = sys.argv[1]
    start = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x280e
    end = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x2bca
    d = open(path, 'rb').read()
    o = start
    n = 0
    total = 0
    print("%-4s %-8s %-10s %-4s %-5s %s" % ("#", "offset", "size", "disk", "flag", "path"))
    while o < end:
        if d[o + 6] == 0 or not (32 <= d[o + 6] < 127):
            break
        size = struct.unpack_from('>I', d, o)[0]
        disk = d[o + 4]
        flag = d[o + 5]
        e = d.index(b'\x00', o + 6)
        name = d[o + 6:e].decode('latin-1')
        n += 1
        total += size
        print("%-4d 0x%06x %-10d %-4d 0x%02x  %s" % (n, o, size, disk, flag, name))
        o = e + 1
        if o & 1:
            o += 1
    print()
    print("%d records, %d bytes of buffer in total" % (n, total))
    tail = d[end:end + 32].split(b'\x00')[0]
    if tail:
        print("trailing name at 0x%06x, with NO record header: %r"
              % (end, tail.decode('latin-1')))


main()
