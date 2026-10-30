#!/usr/bin/env python3
"""buildimage.py -- assemble the data-track image from two independent reads,
and cross-check them where they overlap.

The disc is read by two paths that share nothing but the drive:

  A. ReadFile on \\\\.\\E: -- the logical volume Windows mounts.  The firmware
     descrambles, corrects with ECC and hands over 2048 bytes.  This path is
     reliable but stops at the end of the declared volume, which on this disc is
     LBA 690.  It is the only path that reads LBA 0..15.
  B. raw CDDA transfers, descrambled here (tools/rawsectors.py).  This path
     reaches every sector of the data track including the 227 past the declared
     volume, and every sector proves its own identity through its header and
     EDC.  On this drive it cannot read LBA 0..15.

Neither path covers the whole track.  Together they do, and where they overlap
(LBA 16..690, 675 sectors) they can be compared -- which is a cross-check no
single dumper performs, because a dumper has only one path.

Usage: buildimage.py readfile.bin raw_16_917.bin out.iso
"""
import sys, hashlib

SEC = 2048
RAW_FIRST = 16          # first sector present in the raw dump
VOLUME_END = 691        # first sector past the end of the ReadFile-readable area


def main():
    rf = open(sys.argv[1], 'rb').read()
    rw = open(sys.argv[2], 'rb').read()
    out = sys.argv[3]

    n_rf = len(rf) // SEC
    n_rw = len(rw) // SEC
    print("ReadFile image: %d sectors (usable 0..%d)" % (n_rf, VOLUME_END - 1))
    print("raw image:      %d sectors (%d..%d)" % (n_rw, RAW_FIRST, RAW_FIRST + n_rw - 1))

    # ---- cross-check the overlap
    lo, hi = RAW_FIRST, VOLUME_END          # [lo, hi)
    a = rf[lo * SEC:hi * SEC]
    b = rw[(lo - RAW_FIRST) * SEC:(hi - RAW_FIRST) * SEC]
    assert len(a) == len(b), (len(a), len(b))
    if a == b:
        print("OVERLAP %d..%d (%d sectors): the two paths AGREE byte for byte"
              % (lo, hi - 1, hi - lo))
    else:
        diff = [i // SEC + lo for i in range(len(a)) if a[i] != b[i]]
        secs = sorted(set(diff))
        print("OVERLAP DISAGREES in %d sectors: %s" % (len(secs), secs[:40]))
        raise SystemExit("refusing to build an image from two paths that disagree")

    # ---- assemble
    img = rf[:RAW_FIRST * SEC] + rw
    open(out, 'wb').write(img)
    print("\nwrote %s" % out)
    print("  %d sectors, %d bytes" % (len(img) // SEC, len(img)))
    print("  LBA 0..%d   from ReadFile (the only path that reads them)" % (RAW_FIRST - 1))
    print("  LBA %d..%d from raw descrambled transfers, each sector verified "
          "on sync, header address and EDC" % (RAW_FIRST, len(img) // SEC - 1))
    print("  sha1 %s" % hashlib.sha1(img).hexdigest())
    print("  md5  %s" % hashlib.md5(img).hexdigest())


if __name__ == '__main__':
    main()
