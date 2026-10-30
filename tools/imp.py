"""Imploder ('IMP!' / 'ATN!') data-file decruncher.

This is a faithful transcription of the 350-byte 68000 routine the game
carries at hunk offset 0x1E87C -- registers, in-place backwards buffer and
all -- rather than a reimplementation from a format description.  Doing it
that way is the point: the routine *is* the specification, and the two
constant tables it uses live in the last 38 bytes of every crunched file
instead of in the decruncher, so a file could in principle carry its own.
Every file on this disc carries the Imploder's defaults.

File layout:   'IMP!' | ULONG unpacked | ULONG packed | data | 38-byte tail
Tail layout:   ULONG initial literal run | UWORD initial bit buffer
               | 8 UWORD offset bases | 12 UBYTE bit widths | ULONG checksum
"""
import struct, sys


class Decruncher:
    def __init__(self, data):
        self.magic = data[:4]
        if self.magic not in (b'IMP!', b'ATN!'):
            raise ValueError('not an Imploder file: %r' % data[:4])
        self.orig, self.packed = struct.unpack_from('>II', data, 4)
        self.buf = bytearray(max(self.orig, len(data)))
        self.buf[:len(data)] = data
        self.checksum = struct.unpack_from('>I', data, len(data) - 4)[0]

    # --- the bit reader: d3 is an 8-bit buffer whose top bit is a sentinel,
    # --- refilled a byte at a time from the stream, which runs backwards.
    def _bit(self):
        r = (self.d3 * 2) & 0xFF
        c = self.d3 >> 7
        if r:
            self.d3, self.x = r, c
            return c
        self.a3 -= 1
        s = self.buf[self.a3] * 2 + c          # move.b -(a3),d3 ; addx.b d3,d3
        self.d3, self.x = s & 0xFF, s >> 8
        return self.x

    def _bits(self, n):
        v = 0
        for _ in range(n):
            v = v * 2 + self._bit()
        return v

    def run(self):
        b = self.buf
        a0, self.a3, a4 = 12, self.packed, self.orig
        a2 = self.packed
        for _ in range(3):                      # move.l (a2)+,-(a0)  x3
            a0 -= 4
            b[a0:a0+4] = b[a2:a2+4]
            a2 += 4
        assert a0 == 0
        d2 = struct.unpack_from('>I', b, a2)[0]; a2 += 4
        d3w = struct.unpack_from('>H', b, a2)[0]; a2 += 2
        self.d3 = d3w & 0xFF
        if not (d3w & 0x8000):                  # bmi / subq.l #1,a3
            self.a3 -= 1
        tab = bytes(b[a2:a2+28])
        base = struct.unpack('>8H', tab[:16])   # offset bases
        nbits = tab[16:28]                      # bit widths, three tiers of four
        LITBASE = (6, 10, 10, 18)
        LITBITS = (1, 1, 1, 1, 2, 3, 3, 4, 4, 5, 7, 14)

        while True:
            while d2:                            # literal run: stream -> output
                self.a3 -= 1; a4 -= 1
                b[a4] = b[self.a3]
                d2 -= 1
            if a4 <= 0:
                break
            # --- match length, and the class that sizes the two later fields
            if not self._bit():
                d4, cls = 1, 0
            elif not self._bit():
                d4, cls = 2, 1
            elif not self._bit():
                d4, cls = 3, 2
            elif not self._bit():
                d4, cls = 4, 3
            elif not self._bit():
                d4, cls = self._bits(3) + 5, 3
            else:
                self.a3 -= 1
                d4, cls = (b[self.a3] - 1) & 0xFF, 3    # an explicit byte
            # --- length of the literal run that follows
            if not self._bit():
                i, d5 = cls, 0
            elif not self._bit():
                i, d5 = cls + 4, 2
            else:
                i, d5 = cls + 8, LITBASE[cls]
            d2 = (self._bits(LITBITS[i]) + d5) & 0xFFFF
            # --- match offset, in one of three widths
            if not self._bit():
                j, off = cls, 0
            elif not self._bit():
                j, off = cls + 4, base[cls]
            else:
                j, off = cls + 8, base[cls + 4]
            src = a4 + off + self._bits(nbits[j]) + 1
            for _ in range(d4 + 1):
                src -= 1; a4 -= 1
                b[a4] = b[src]
            if a4 <= 0:
                break
        self.ok = (a4 == 0 and self.a3 == 0)
        return bytes(b[:self.orig])


def decrunch(data):
    return Decruncher(data).run()


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    dc = Decruncher(d)
    out = dc.run()
    sys.stderr.write('%s: %d -> %d, exact=%s\n' % (sys.argv[1], dc.packed, len(out), dc.ok))
    if len(sys.argv) > 2:
        open(sys.argv[2], 'wb').write(out)
