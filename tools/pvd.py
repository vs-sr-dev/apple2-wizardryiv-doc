#!/usr/bin/env python3
"""Dump every volume descriptor of an ISO 9660 data track, field by field.

Nothing here is specific to this disc. It prints the descriptor set from
sector 16 until the terminator, decodes the ISOCD application-use area
(the `FS` and `TM` tags), and reports the declared volume size against the
image size so the overrun past the volume is a measurement rather than an
assumption.

Usage:  python tools/pvd.py <track1.iso>
"""
import sys, os

SEC = 2048


def u16le(b, o):
    return int.from_bytes(b[o:o + 2], 'little')


def u32le(b, o):
    return int.from_bytes(b[o:o + 4], 'little')


def u32be(b, o):
    return int.from_bytes(b[o:o + 4], 'big')


def u16be(b, o):
    return int.from_bytes(b[o:o + 2], 'big')


def txt(b, a, n):
    return b[a:a + n].decode('latin-1').rstrip('\x00 ')


def strdate(b, o):
    s = b[o:o + 17]
    if s[:16].strip(b'0 \x00') == b'':
        return None
    t = s[:16].decode('latin-1')
    tz = s[16] - 256 if s[16] > 127 else s[16]
    return "%s-%s-%s %s:%s:%s.%s  tz=%+d (%+.1f h)" % (
        t[0:4], t[4:6], t[6:8], t[8:10], t[10:12], t[12:14], t[14:16],
        tz, tz * 0.25)


def dirdate(b, o):
    y, mo, d, h, mi, s, tz = b[o:o + 7]
    if y == 0 and mo == 0:
        return None
    tz = tz - 256 if tz > 127 else tz
    return "%04d-%02d-%02d %02d:%02d:%02d  tz=%+d" % (1900 + y, mo, d, h, mi, s, tz)


def appuse(a):
    """ISOCD writes tagged records into the 512-byte application-use area."""
    out = []
    i = a.find(b'TM')
    if i >= 0:
        # 'TM', a two-byte constant (0x0014 on every disc measured so far),
        # a 32-bit big-endian length, then a 32-bit big-endian LBA.
        out.append(('TM', i, u16be(a, i + 2), u32be(a, i + 4), u32be(a, i + 8)))
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    size = os.path.getsize(path)
    f = open(path, 'rb')
    print("image           : %s" % os.path.basename(path))
    print("image bytes     : %d" % size)
    print("image sectors   : %d%s" % (size // SEC,
          "" if size % SEC == 0 else "  (+%d bytes remainder)" % (size % SEC)))
    print()

    vols = []
    for lba in range(16, 64):
        f.seek(lba * SEC)
        s = f.read(SEC)
        if len(s) < SEC or s[1:6] != b'CD001':
            break
        t = s[0]
        print("--- sector %d : descriptor type %d ---" % (lba, t))
        if t == 255:
            print("  volume descriptor set terminator")
            print()
            break
        if t not in (1, 2):
            print("  (not a primary/supplementary descriptor; skipped)")
            print()
            continue
        vols.append((lba, s))
        print("  system identifier      : %r" % txt(s, 8, 32))
        print("  volume identifier      : %r" % txt(s, 40, 32))
        print("  volume space size      : %d sectors (LE) / %d (BE)"
              % (u32le(s, 80), u32be(s, 84)))
        print("  volume set size        : %d" % u16le(s, 120))
        print("  volume sequence number : %d" % u16le(s, 124))
        print("  logical block size     : %d" % u16le(s, 128))
        print("  path table size        : %d bytes" % u32le(s, 132))
        print("  L path table LBA       : %d   (opt %d)" % (u32le(s, 140), u32le(s, 144)))
        print("  M path table LBA       : %d   (opt %d)" % (u32be(s, 148), u32be(s, 152)))
        print("  root dir record        : LBA %d, %d bytes, %s"
              % (u32le(s, 156 + 2), u32le(s, 156 + 10), dirdate(s, 156 + 18)))
        print("  volume set identifier  : %r" % txt(s, 190, 128))
        print("  publisher identifier   : %r" % txt(s, 318, 128))
        print("  data preparer          : %r" % txt(s, 446, 128))
        print("  application identifier : %r" % txt(s, 574, 128))
        print("  copyright file         : %r" % txt(s, 702, 37))
        print("  abstract file          : %r" % txt(s, 739, 37))
        print("  bibliographic file     : %r" % txt(s, 776, 37))
        print("  creation date          : %s" % strdate(s, 813))
        print("  modification date      : %s" % strdate(s, 830))
        print("  expiration date        : %s" % strdate(s, 847))
        print("  effective date         : %s" % strdate(s, 864))
        print("  file structure version : %d" % s[881])
        app = s[883:883 + 512]
        nz = len(app.rstrip(b'\x00'))
        print("  application use        : %d non-zero-tail bytes" % nz)
        print("    hex: %s" % app[:32].hex(' '))
        for tag, off, const, ln, lba2 in appuse(app):
            print("    tag %r at app-use offset %d (abs %d): constant 0x%04x,"
                  " length %d bytes (%.3f sectors), LBA %d"
                  % (tag, off, 883 + off, const, ln, ln / SEC, lba2))
        print()

    if vols:
        decl = u32le(vols[0][1], 80)
        img = size // SEC
        print("declared volume : %d sectors" % decl)
        print("image           : %d sectors" % img)
        print("OVERRUN         : %d sectors past the declared volume" % (img - decl))
        if len(vols) > 1:
            a, b = vols[0][1], vols[1][1]
            diff = [i for i in range(SEC) if a[i] != b[i]]
            print("duplicate PVDs  : %d, differing in %d of %d bytes%s"
                  % (len(vols), len(diff), SEC,
                     (" at offsets %s" % diff[:20]) if diff else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
