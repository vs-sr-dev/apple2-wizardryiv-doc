#!/usr/bin/env python3
"""RNC ProPack *method 2* decompressor, and the self-decrunching hunk file
that wraps it on this disc.

Method 1 (`tools/rnc.py`, carried over from the Dragonstone repository) packs
all 37 data files on the Banshee disc.  Method 2 packs nothing in the file
system at all -- it appears only *inside* `picture.exe`, where each of the
three payload hunks is an independent method 2 stream and hunk 0 is a
484-byte stub that decrunches them and then walks the decrunched image
applying `HUNK_RELOC32` tables itself, which is why the file has no
relocations of its own.

The algorithm below is transcribed from that stub (file offsets
0x2c..0x210 of `picture.exe`; the annotated listing is in
`notes/picture-depacker.txt`), and every stream it produces is checked
against the CRC-16/ARC in its own header.

Header, 18 bytes big-endian, identical in shape to method 1:

    0   'RNC'          3  method (2)
    4   unpacked length        8   packed length
    12  CRC-16 unpacked        14  CRC-16 packed
    16  leeway                 17  chunk count

The bit stream is MSB-first, carried in a byte-wide register with a sentinel
bit below it (`add.b d7,d7`; on a zero result `move.b (a3)+,d7` then
`addx.b d7,d7`), and the first **two** bits are read and discarded.

Usage:
    python3 tools/rnc2.py unpack <file> <offset> [out]
    python3 tools/rnc2.py exe    <hunkfile> <outdir>
"""
import sys, struct, os, importlib.util

_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("rnc1", os.path.join(_here, "rnc.py"))
rnc1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rnc1)
crc16 = rnc1.crc16


class Bits(object):
    """The stub's bit reader, register for register (d7 and the X flag)."""

    def __init__(self, src):
        self.src = src
        self.p = 0
        self.d7 = 0x80          # sentinel only; the first read forces a refill

    def bit(self):
        v = (self.d7 << 1) & 0xff
        c = (self.d7 >> 7) & 1
        if v == 0:                      # buffer exhausted: refill, X carried in
            b = self.src[self.p]
            self.p += 1
            self.d7 = ((b << 1) | c) & 0xff
            c = (b >> 7) & 1
        else:
            self.d7 = v
        return c

    def bits(self, n):
        v = 0
        for _ in range(n):
            v = 2 * v + self.bit()
        return v

    def byte(self):
        b = self.src[self.p]
        self.p += 1
        return b


def unpack(data, off=0):
    if data[off:off + 3] != b'RNC':
        raise ValueError('no RNC magic at 0x%x' % off)
    if data[off + 3] != 2:
        raise ValueError('method %d, not 2' % data[off + 3])
    ulen, plen = struct.unpack_from('>II', data, off + 4)
    ucrc, pcrc = struct.unpack_from('>HH', data, off + 12)
    src = data[off + 18:off + 18 + plen]
    r = Bits(src)
    out = bytearray()
    r.bit()                              # the two discarded bits
    r.bit()
    done = False
    while not done:
        while r.bit() == 0:              # L24/L27: literal run
            out.append(r.byte())
        length = 2                       # L28
        d6 = 0
        short_offset = False
        if r.bit() == 0:                 # L09  -- prefix '0'
            length = 2 * length + r.bit()            # 4 or 5
            if r.bit() == 1:
                length -= 1
                length = 2 * length + r.bit()        # 6..9
                if length == 9:                      # L05: long literal run
                    n = r.bits(4)
                    for _ in range(4 * (n + 3)):
                        out.append(r.byte())
                    continue
        elif r.bit() == 0:               # prefix '10': length 2, one-byte offset
            short_offset = True
        else:                            # prefix '11'
            length += 1                                  # 3
            if r.bit() == 1:
                b = r.byte()
                if b == 0:                               # L35
                    if r.bit() == 0:
                        done = True                      # end of stream
                    continue                             # else: next chunk
                length = b + 8
        if not short_offset and r.bit() == 1:            # L13/L14
            d6 = r.bit()                                 # L15
            if r.bit() == 1:                             # L32
                d6 = 2 * d6 + r.bit()
                d6 |= 4
                if r.bit() == 0:                         # L34 -> L17
                    d6 = 2 * d6 + r.bit()
            else:
                if d6 == 0:
                    d6 = 1
                    d6 = 2 * d6 + r.bit()                # L17
            d6 <<= 8                                     # L19: rol.w #8
        d6 |= r.byte()                                   # L20
        i = len(out) - d6 - 1
        for _ in range(length):
            out.append(out[i])
            i += 1
    out = bytes(out)
    if len(out) != ulen:
        raise ValueError('produced %d bytes, header says %d' % (len(out), ulen))
    if crc16(out) != ucrc:
        raise ValueError('CRC mismatch %04X != %04X' % (crc16(out), ucrc))
    return out


def info(data, off=0):
    ulen, plen = struct.unpack_from('>II', data, off + 4)
    ucrc, pcrc = struct.unpack_from('>HH', data, off + 12)
    return dict(method=data[off + 3], unpacked=ulen, packed=plen,
                crc_unpacked=ucrc, crc_packed=pcrc,
                leeway=data[off + 16], chunks=data[off + 17])


HK = {0x3e9: 'CODE', 0x3ea: 'DATA', 0x3eb: 'BSS'}


def exe(path, outdir):
    """Walk a hunk file, decrunch every method 2 body, write the plain hunks."""
    d = open(path, 'rb').read()
    assert struct.unpack_from('>I', d, 0)[0] == 0x3f3
    o = 4
    n = struct.unpack_from('>I', d, o)[0]
    o += 4
    while n:
        o += 4 * n + 4
        n = struct.unpack_from('>I', d, o - 4)[0]
    tbl, first, last = struct.unpack_from('>III', d, o)
    o += 12
    decl = []
    for _ in range(tbl):
        v = struct.unpack_from('>I', d, o)[0]
        o += 4
        decl.append(v)
    print("hunk table: " + ", ".join(
        "%d=%d bytes%s" % (i, (v & 0x3fffffff) * 4,
                           " CHIP" if v >> 30 == 1 else (" FAST" if v >> 30 == 2 else ""))
        for i, v in enumerate(decl)))
    idx = first
    os.makedirs(outdir, exist_ok=True)
    while o < len(d) - 3:
        hid = struct.unpack_from('>I', d, o)[0] & 0x3fffffff
        o += 4
        if hid in HK:
            ln = struct.unpack_from('>I', d, o)[0] * 4
            o += 4
            if hid == 0x3eb:
                print("hunk %d BSS %d bytes" % (idx, ln))
                continue
            body = d[o:o + ln]
            o += ln
            pre = struct.unpack_from('>II', body, 0) if ln >= 8 else (0, 0)
            if body[8:12] == b'RNC\x02':
                h = info(body, 8)
                out = unpack(body, 8)
                p = os.path.join(outdir, "hunk%d.bin" % idx)
                open(p, 'wb').write(out)
                print("hunk %-2d %-4s stored %7d  prefix %d/%08x  RNC2 ulen %7d "
                      "plen %7d leeway %d chunks %d -> %s  CRC ok"
                      % (idx, HK[hid], ln, pre[0], pre[1], h['unpacked'],
                         h['packed'], h['leeway'], h['chunks'], p))
            else:
                p = os.path.join(outdir, "hunk%d.bin" % idx)
                open(p, 'wb').write(body)
                print("hunk %-2d %-4s stored %7d  (not crunched) -> %s" % (idx, HK[hid], ln, p))
        elif hid == 0x3ec:
            while True:
                c = struct.unpack_from('>I', d, o)[0]
                o += 4
                if c == 0:
                    break
                o += 4 + 4 * c
        elif hid == 0x3f2:
            idx += 1
        else:
            print("stopped at unknown hunk id 0x%x at 0x%x" % (hid, o - 4))
            break


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    if sys.argv[1] == 'unpack':
        d = open(sys.argv[2], 'rb').read()
        out = unpack(d, int(sys.argv[3], 0))
        print('%d bytes, CRC ok' % len(out))
        if len(sys.argv) > 4:
            open(sys.argv[4], 'wb').write(out)
    elif sys.argv[1] == 'exe':
        exe(sys.argv[2], sys.argv[3])


if __name__ == '__main__':
    main()
