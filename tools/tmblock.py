"""Dump the CDTV/CD32 trademark block by following the pointer, not the map.

The block belongs to no file: no directory record covers it, and the only
reference to it anywhere on the disc is a tagged field in the primary volume
descriptor's application-use area.  Read the 'TM' tag, take the length and
the LBA that follow it, and dump exactly that -- the position is not fixed
and neither is the size.
"""
import sys, struct, hashlib

d = open(sys.argv[1], 'rb').read()
au = d[16*2048 + 883 : 16*2048 + 883 + 512]
i = au.index(b'TM')
length = struct.unpack_from('>I', au, i + 4)[0]
lba    = struct.unpack_from('>I', au, i + 8)[0]
print('application-use area: %s' % au[:20].hex(' '))
print("'TM' tag at +%d, length %d bytes (%.1f sectors), LBA %d"
      % (i, length, length / 2048, lba))
blk = d[lba*2048 : lba*2048 + length]
print('SHA-1 %s' % hashlib.sha1(blk).hexdigest())
print('non-zero bytes %d of %d' % (sum(1 for b in blk if b), len(blk)))
print('--- first 240 bytes, printable ---')
sys.stdout.reconfigure(encoding='utf-8')
print(''.join(chr(c) if 32 <= c < 127 else ('\n' if c == 0 else '.')
              for c in blk[:240]))
if len(sys.argv) > 2:
    open(sys.argv[2], 'wb').write(blk)
