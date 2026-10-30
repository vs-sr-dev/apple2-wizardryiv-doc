"""RNC ProPack method 1 decompressor (the `.cru` files on the Dragonstone disc).

Header, 18 bytes big-endian:
    0   'RNC'
    3   method (1 here; method 2 exists but is not used on this disc)
    4   unpacked length
    8   packed length
    12  CRC-16 of the unpacked data
    14  CRC-16 of the packed data
    16  leeway  -- extra bytes needed to unpack in place
    17  chunk count

The bit stream is read LSB-first out of little-endian 16-bit units, and is
interleaved with runs of literal bytes: the reader always sits two bytes
behind the byte pointer, so a literal run starts where the byte pointer is
and the bit buffer is refilled from beyond the run afterwards.  The residual
bits of the current unit survive the run -- that detail is what makes the
format awkward to reimplement, and it is why every unpack here is checked
against the CRC in the header.
"""
import sys

CRC_TAB = []
for _i in range(256):
    _c = _i
    for _ in range(8):
        _c = (_c >> 1) ^ 0xA001 if _c & 1 else _c >> 1
    CRC_TAB.append(_c)


def crc16(data):
    c = 0
    for b in data:
        c = CRC_TAB[(c ^ b) & 0xFF] ^ (c >> 8)
    return c


class Reader:
    """Faithful port of ProPack's input_bits_m1 / read_source_byte pair."""

    def __init__(self, src):
        self.src = src
        self.p = 0          # next unread byte (ProPack's pack_block_start)
        self.buf = 0
        self.cnt = 0

    def _at(self, i):
        j = self.p + i
        return self.src[j] if j < len(self.src) else 0

    def _byte(self):
        b = self._at(0)
        self.p += 1
        return b

    def bits(self, n):
        out, place = 0, 1
        for _ in range(n):
            if self.cnt == 0:
                b1 = self._byte()
                b2 = self._byte()
                self.buf = (self._at(1) << 24) | (self._at(0) << 16) | (b2 << 8) | b1
                self.cnt = 16
            if self.buf & 1:
                out |= place
            self.buf >>= 1
            place <<= 1
            self.cnt -= 1
        return out

    def literals(self, n):
        out = self.src[self.p:self.p + n]
        self.p += n
        # keep the residual bits, refill everything above them
        top = (self._at(2) << 16) | (self._at(1) << 8) | self._at(0)
        self.buf = (top << self.cnt) | (self.buf & ((1 << self.cnt) - 1))
        return out


def _table(r):
    """5-bit leaf count, then 4 bits of code length per leaf, canonical order."""
    depth = [0] * 16
    n = r.bits(5)
    if n:
        for i in range(min(n, 16)):
            depth[i] = r.bits(4)
    tab = []          # (bit_depth, mirrored_code, symbol)
    val, div = 0, 0x80000000
    for bl in range(1, 17):
        for i in range(16):
            if depth[i] == bl:
                code, m = val // div, 0
                for _ in range(bl):
                    m = (m << 1) | (code & 1)
                    code >>= 1
                tab.append((bl, m, i))
                val += div
        div >>= 1
    return tab


def _value(r, tab):
    for bl, code, sym in tab:
        if (r.buf & ((1 << bl) - 1)) == code:
            r.bits(bl)
            if sym < 2:
                return sym
            return r.bits(sym - 1) | (1 << (sym - 1))
    raise ValueError('no Huffman code matches')


def unpack(data):
    if data[:3] != b'RNC':
        raise ValueError('not RNC')
    if data[3] != 1:
        raise ValueError('method %d not supported' % data[3])
    ulen = int.from_bytes(data[4:8], 'big')
    plen = int.from_bytes(data[8:12], 'big')
    ucrc = int.from_bytes(data[12:14], 'big')
    r = Reader(data[18:18 + plen])
    flags = r.bits(2)
    if flags & 2:
        raise ValueError('stream is encrypted')
    out = bytearray()
    while len(out) < ulen:
        raw, lens, poss = _table(r), _table(r), _table(r)
        sub = r.bits(16)
        while sub:
            sub -= 1
            n = _value(r, raw)
            if n:
                out += r.literals(n)
            if sub:
                off = _value(r, lens) + 1
                cnt = _value(r, poss) + 2
                for _ in range(cnt):
                    out.append(out[-off])
    out = bytes(out)
    if crc16(out) != ucrc:
        raise ValueError('CRC mismatch: got %04X want %04X' % (crc16(out), ucrc))
    return out


def info(data):
    return dict(method=data[3],
                unpacked=int.from_bytes(data[4:8], 'big'),
                packed=int.from_bytes(data[8:12], 'big'),
                crc_unpacked=int.from_bytes(data[12:14], 'big'),
                crc_packed=int.from_bytes(data[14:16], 'big'),
                leeway=data[16], chunks=data[17])


if __name__ == '__main__':
    blob = open(sys.argv[1], 'rb').read()
    out = unpack(blob)
    if len(sys.argv) > 2:
        open(sys.argv[2], 'wb').write(out)
    print('%s -> %d bytes, CRC ok' % (sys.argv[1], len(out)))
