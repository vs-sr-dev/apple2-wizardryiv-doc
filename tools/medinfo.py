#!/usr/bin/env python3
"""Read an OctaMED MMD0/MMD1 module header: blocks, song length, tempo,
sample table and, where the expansion block carries them, instrument names.

Written for Myth, whose two modules are whole `DAVE` chunks rather than files,
so the module always starts at offset 0 of the piece it is given.

Usage: python3 tools/medinfo.py <file>... [--samples]
"""
import struct, sys, os


def u16(d, o):
    return struct.unpack_from('>H', d, o)[0]


def u32(d, o):
    return struct.unpack_from('>I', d, o)[0]


def i8(d, o):
    v = d[o]
    return v - 256 if v > 127 else v


def show(path, samples=False):
    d = open(path, 'rb').read()
    magic = d[:4]
    print("=== %s  %d bytes  magic %r ===" % (os.path.basename(path), len(d), magic))
    if magic not in (b'MMD0', b'MMD1'):
        print("  not an MMD0/MMD1 module")
        return
    modlen = u32(d, 4)
    songp = u32(d, 8)
    blockarr = u32(d, 16)
    smplarr = u32(d, 24)
    expdata = u32(d, 32)
    print("  declared module length   %d  (piece is %d, %s)" %
          (modlen, len(d), "exact" if modlen == len(d) else "DIFFERS"))
    print("  song at 0x%x  blockarr 0x%x  smplarr 0x%x  expdata 0x%x" %
          (songp, blockarr, smplarr, expdata))
    if songp == 0 or songp + 788 > len(d):
        print("  song pointer out of range")
        return
    s = songp
    numblocks = u16(d, s + 504)
    songlen = u16(d, s + 506)
    playseq = d[s + 508:s + 508 + 256]
    deftempo = u16(d, s + 764)
    playtransp = i8(d, s + 766)
    flags = d[s + 767]
    flags2 = d[s + 768]
    tempo2 = d[s + 769]
    trkvol = d[s + 770:s + 786]
    mastervol = d[s + 786]
    numsamples = d[s + 787]
    print("  blocks %d   song length %d   samples %d" % (numblocks, songlen, numsamples))
    print("  tempo %d  tempo2 %d  master volume %d  transpose %d" %
          (deftempo, tempo2, mastervol, playtransp))
    print("  flags 0x%02X (%s)  flags2 0x%02X (%d tracks)" %
          (flags, "8 channel" if flags & 0x40 else "4 channel",
           flags2, (flags2 & 0x0F) + 1))
    print("  play sequence (first %d): %s" %
          (min(songlen, 32), ' '.join(str(b) for b in playseq[:min(songlen, 32)])))
    print("  track volumes: %s" % ' '.join(str(b) for b in trkvol[:8]))
    # instrument names live in expdata->iinfo, 40 bytes per entry
    if expdata and expdata + 24 <= len(d):
        iinfo = u32(d, expdata + 4)
        iinfonum = u16(d, expdata + 8)
        iinfoentsz = u16(d, expdata + 10)
        if iinfo and iinfoentsz and iinfo + iinfonum * iinfoentsz <= len(d):
            print("  instrument names (%d x %d bytes at 0x%x):" %
                  (iinfonum, iinfoentsz, iinfo))
            named = 0
            for i in range(iinfonum):
                nm = d[iinfo + i * iinfoentsz:iinfo + i * iinfoentsz + 40]
                nm = nm.split(b'\0')[0].decode('latin-1').strip()
                if nm:
                    named += 1
                    print("    %2d  %s" % (i + 1, nm))
            print("    %d named of %d slots" % (named, iinfonum))
    if samples and smplarr:
        print("  samples:")
        tot = 0
        for i in range(numsamples):
            p = u32(d, smplarr + 4 * i)
            if p == 0:
                print("    %2d  (empty slot)" % (i + 1))
                continue
            if p + 6 > len(d):
                print("    %2d  pointer 0x%x out of range" % (i + 1, p))
                continue
            ln = u32(d, p)
            ty = u16(d, p + 4)
            tot += ln
            print("    %2d  0x%06x  %7d B  type %d%s" %
                  (i + 1, p, ln, ty, "  (synth/hybrid)" if ty else ""))
        print("    total sample bytes %d (%.1f%% of the module)" %
              (tot, 100.0 * tot / len(d)))


def main():
    samples = '--samples' in sys.argv
    for p in [x for x in sys.argv[1:] if not x.startswith('--')]:
        show(p, samples)
        print()


if __name__ == '__main__':
    main()
