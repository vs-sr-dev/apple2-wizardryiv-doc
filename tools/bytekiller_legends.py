"""`.Pak` decruncher -- a transcription of the 201-byte routine at hunk offset
0x703E of `Legends`, registers and backwards in-place buffer and all.

File layout:  ULONG offset-to-trailer | packed data | ULONG crc | ULONG unpacked
The first field is always filesize-4, so it points at the last longword, which
is the unpacked size.  Between the packed data and that size sits a longword
the routine steps over without reading: the cruncher's checksum, never checked.

The bitstream is read backwards a longword at a time, top bit first, with a
sentinel bit marking the end of each longword; output is written backwards too,
into the same buffer, from `unpacked size` down to zero.  This is the Bytekiller
token set: literal runs of 1-8 and 9-264 bytes, and matches of 2, 3, 4 and
1-256 bytes at offsets of 8, 9, 10 and 12 bits.
"""
import struct, sys


class Bits:
    """d0 as the routine keeps it: a longword whose high sentinel bit says how
    many real bits are left, refilled from a stream that runs backwards."""
    def __init__(self, data, pos):
        self.d, self.pos = data, pos
        self.reg = self._long()

    def _long(self):
        self.pos -= 4
        if self.pos < 0:
            raise EOFError('bitstream ran off the front of the file')
        return struct.unpack_from('>I', self.d, self.pos)[0]

    def bit(self):
        c = self.reg & 1                 # lsr.l #1,d0
        self.reg >>= 1
        if self.reg == 0:                # bne.b -- the sentinel has come out
            v = self._long()             # move.l -(a0),d0
            self.reg = (v >> 1) | (c << 31)   # roxr.l #1,d0
            c = v & 1
        return c

    def code(self, n):
        v = 0
        for _ in range(n):
            v = (v << 1) | self.bit()
        return v


def unpack(data):
    """data is the whole .Pak file, prefix included."""
    off = struct.unpack_from('>I', data, 0)[0]
    end = 4 + off                                   # == len(data) on every file
    unpacked, crc = struct.unpack_from('>II', data, end - 8)[1], \
                    struct.unpack_from('>I',  data, end - 8)[0]
    body = data[4:end]
    out = bytearray(unpacked)
    out[:len(body)] = body
    bs = Bits(out, end - 4 - 8)                     # skip size and crc
    o = unpacked
    while o > 0:
        if not bs.bit():
            if bs.bit():                            # 2 bytes at an 8-bit offset
                o = _copy(out, o, 2, bs.code(8))
            else:                                   # 1-8 literal bytes
                for _ in range(bs.code(3) + 1):
                    o -= 1
                    out[o] = bs.code(8)
        else:
            c = bs.code(2)
            if c == 3:                              # 9-264 literal bytes
                for _ in range(bs.code(8) + 9):
                    o -= 1
                    out[o] = bs.code(8)
            elif c < 2:                             # 3 or 4 bytes, 9/10-bit off
                o = _copy(out, o, c + 3, bs.code(c + 9))
            else:                                   # 1-256 bytes, 12-bit offset
                n = bs.code(8) + 1
                o = _copy(out, o, n, bs.code(12))
    return bytes(out), crc, unpacked


def _copy(out, o, n, dist):
    for _ in range(n):
        o -= 1
        out[o] = out[o + dist]
    return o


if __name__ == '__main__':
    for p in sys.argv[1:]:
        d = open(p, 'rb').read()
        try:
            u, crc, n = unpack(d)
        except Exception as e:
            print('%-28s FAILED %s' % (p, e)); continue
        print('%-28s %8d -> %8d  %5.1f%%  crc=%08X' %
              (p, len(d), n, 100.0 * len(d) / n, crc))
        if len(sys.argv) == 2:
            open(p + '.bin', 'wb').write(u)
