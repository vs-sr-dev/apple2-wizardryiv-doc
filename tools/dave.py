#!/usr/bin/env python3
"""Decode Myth's `DAVE` container: an 8-byte header over a Bytekiller stream.

Container
    +0  'DAVE'
    +4  u32 big-endian, the unpacked length
    +8  the Bytekiller stream, running to the end of the chunk

Bytekiller stream (identical token set to the one Krisalis shipped on
[Legends], transcribed there from the same 68000 routine):
    trailer, at the end of the stream, read backwards
        end-4   u32  unpacked length   (must equal the container's)
        end-8   u32  checksum
    then the bit pump runs backwards a longword at a time with a sentinel
    bit, and the output is filled backwards from `unpacked` down to zero.

The difference from [Legends] is that Myth KEEPS the checksum test that
Krisalis removed: the routine at MYTH.A+0x2d4c XORs every longword it pulls
off the stream into d5, which was seeded with the stored checksum, and
`tst.l d5 / bne` flashes COLOR00 red forever if the result is not zero.  So
every stream here can be validated three independent ways -- the container
length, the trailer length, and the running XOR -- and this script reports
all three.

Usage: python3 tools/dave.py <file>... [--out DIR]
"""
import struct, sys, os, hashlib

MAGIC = b'DAVE'


class Bits(object):
    """The bit pump as the 68000 routine keeps it in d0, plus the d5 XOR."""

    def __init__(self, data, pos, chk):
        self.d, self.pos = data, pos
        self.chk = chk
        self.reg = self._long()
        self.chk ^= self.reg

    def _long(self):
        self.pos -= 4
        if self.pos < 0:
            raise EOFError('bitstream ran off the front of the stream')
        return struct.unpack_from('>I', self.d, self.pos)[0]

    def bit(self):
        c = self.reg & 1                       # lsr.l #1,d0
        self.reg >>= 1
        if self.reg == 0:                      # the sentinel has come out
            v = self._long()                   # move.l -(a0),d0
            self.chk ^= v                      # eor.l d0,d5
            self.reg = (v >> 1) | (c << 31)    # roxr.l #1,d0
            c = v & 1
        return c

    def code(self, n):
        v = 0
        for _ in range(n):
            v = (v << 1) | self.bit()
        return v


def _copy(out, o, n, dist):
    for _ in range(n):
        o -= 1
        out[o] = out[o + dist]
    return o


def unpack_stream(body, unpacked):
    """Decode a bare Bytekiller stream. Returns (bytes, checksum_residue)."""
    crc = struct.unpack_from('>I', body, len(body) - 8)[0]
    trailer_len = struct.unpack_from('>I', body, len(body) - 4)[0]
    out = bytearray(unpacked)
    bs = Bits(body, len(body) - 8, crc)
    o = unpacked
    while o > 0:
        if not bs.bit():
            if bs.bit():                       # 2 bytes at an 8-bit offset
                o = _copy(out, o, 2, bs.code(8))
            else:                              # 1-8 literal bytes
                for _ in range(bs.code(3) + 1):
                    o -= 1
                    out[o] = bs.code(8)
        else:
            c = bs.code(2)
            if c == 3:                         # 9-264 literal bytes
                for _ in range(bs.code(8) + 9):
                    o -= 1
                    out[o] = bs.code(8)
            elif c < 2:                        # 3 or 4 bytes, 9/10-bit offset
                o = _copy(out, o, c + 3, bs.code(c + 9))
            else:                              # 1-256 bytes, 12-bit offset
                n = bs.code(8) + 1
                o = _copy(out, o, n, bs.code(12))
    return bytes(out), bs.chk, trailer_len


def unpack(data):
    """Decode a whole `DAVE` chunk."""
    if data[:4] != MAGIC:
        raise ValueError('no DAVE magic')
    unpacked = struct.unpack_from('>I', data, 4)[0]
    body = data[8:]
    out, residue, trailer_len = unpack_stream(body, unpacked)
    return out, residue, unpacked, trailer_len


def main():
    out_dir = None
    args = list(sys.argv[1:])
    if '--out' in args:
        i = args.index('--out')
        out_dir = args[i + 1]
        del args[i:i + 2]
        os.makedirs(out_dir, exist_ok=True)
    ok = bad = 0
    tot_p = tot_u = 0
    print("%-22s %9s %9s %6s %-8s %-8s %s" %
          ("chunk", "packed", "unpacked", "ratio", "hdr==tlr", "checksum", "sha1"))
    for p in args:
        d = open(p, 'rb').read()
        try:
            u, residue, n, tlr = unpack(d)
        except Exception as e:
            print("%-22s FAILED  %s" % (os.path.basename(p), e))
            bad += 1
            continue
        ok += 1
        tot_p += len(d)
        tot_u += len(u)
        print("%-22s %9d %9d %5.1f%% %-8s %-8s %s" %
              (os.path.basename(p), len(d), len(u), 100.0 * len(d) / len(u),
               "yes" if tlr == n else "NO(%d)" % tlr,
               "zero" if residue == 0 else "%08X" % residue,
               hashlib.sha1(u).hexdigest()[:16]))
        if out_dir:
            open(os.path.join(out_dir, os.path.basename(p) + '.out'), 'wb').write(u)
    print()
    print("decoded %d, failed %d;  %d packed -> %d unpacked  %.2fx" %
          (ok, bad, tot_p, tot_u, tot_u / max(1, tot_p)))


if __name__ == '__main__':
    main()
