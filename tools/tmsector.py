#!/usr/bin/env python3
"""Find the 'TM' tag in the PVD application-use area, follow the pointer, and
hash what is there in the three pieces section 2 of the platform notes uses.

    python tools/tmsector.py <image.iso> [-o dump.bin]
"""
import sys, struct, hashlib

SECTOR = 2048

def main():
    data = open(sys.argv[1], 'rb').read()
    pvd = data[16 * SECTOR:17 * SECTOR]
    au = pvd[883:1395]
    i = au.find(b'TM')
    if i < 0:
        raise SystemExit("no 'TM' tag in the application-use area")
    const = struct.unpack_from('>H', au, i + 2)[0]
    length = struct.unpack_from('>I', au, i + 4)[0]
    lba = struct.unpack_from('>I', au, i + 8)[0]
    print("application-use area: %s" % au[:24].hex(' '))
    print("'TM' tag at PVD offset %d, constant %d, length %d, LBA %d" %
          (883 + i, const, length, lba))
    blob = data[lba * SECTOR: lba * SECTOR + length]
    print("whole block   SHA-1 %s  (%d bytes)" % (hashlib.sha1(blob).hexdigest(), len(blob)))
    if length == 2048:
        print("banner        SHA-1 %s" % hashlib.sha1(blob[:0x44C]).hexdigest())
        print("object file   SHA-1 %s" % hashlib.sha1(blob[0x44C:0x7B8]).hexdigest())
    if '-o' in sys.argv:
        open(sys.argv[sys.argv.index('-o') + 1], 'wb').write(blob)

if __name__ == '__main__':
    main()
