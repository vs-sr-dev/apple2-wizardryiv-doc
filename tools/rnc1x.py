#!/usr/bin/env python3
"""RNC ProPack method 1 as HeroQuest II ships it -- plus the disc's XOR layer.

The container is stock RNC ProPack 1 (18-byte header, `RNC` 0x01, both CRC-16s
present and both correct on every block here).  The *stream* is not stock: every
literal byte is XORed with the low byte of a 16-bit key, and the key is rotated
right one bit after each non-empty literal run.  Match copies take their bytes
from output that has already been de-XORed, so the obfuscation touches literals
only.

Two variants ship on the disc and they differ in where the key comes from:

  * **stream key** -- 16 bits follow the two RNC flag bits and *are* the key.
    Used by the three crunched hunks inside `/QuestII`, where the key reads
    0xBE1A in all three.
  * **fixed key** -- no key field; the decruncher carries 0x5ED0 as an
    immediate.  Used by all 88 whole-file blocks and all 16 container blocks.

Both are verified against the CRC-16 of the unpacked data in each block's own
header, which is what tells the two apart with no guessing.

The bit reader is Dragonstone's, unchanged: LSB-first out of little-endian
16-bit units with the byte pointer running two bytes ahead of the bits.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rnc

FIXED_KEY = 0x5ED0


def _ror16(k):
    return ((k >> 1) | ((k & 1) << 15)) & 0xFFFF


def unpack(blob, stream_key=False, key=FIXED_KEY, check=True):
    if blob[:3] != b'RNC' or blob[3] != 1:
        raise ValueError('not RNC method 1')
    ulen = int.from_bytes(blob[4:8], 'big')
    plen = int.from_bytes(blob[8:12], 'big')
    ucrc = int.from_bytes(blob[12:14], 'big')
    r = rnc.Reader(blob[18:18 + plen])
    r.bits(2)                      # RNC flag bits, discarded by the game too
    k = r.bits(16) if stream_key else key
    out = bytearray()
    while len(out) < ulen:
        raw, lens, poss = rnc._table(r), rnc._table(r), rnc._table(r)
        sub = r.bits(16)
        while sub:
            sub -= 1
            n = rnc._value(r, raw)
            if n:
                lit = r.literals(n)
                kb = k & 0xFF
                out += bytes(b ^ kb for b in lit)
                k = _ror16(k)
            if sub:
                off = rnc._value(r, lens) + 1
                cnt = rnc._value(r, poss) + 2
                for _ in range(cnt):
                    out.append(out[-off])
    out = bytes(out)
    if check and rnc.crc16(out) != ucrc:
        raise ValueError('CRC-16 mismatch: got %04X want %04X' % (rnc.crc16(out), ucrc))
    return out


def auto(blob):
    """Identify the variant by CRC and return (data, a label for it).

    Three answers occur on this disc: plain RNC (key 0), the fixed 0x5ED0 key,
    and a key carried in the stream.  Nothing has to be guessed -- the CRC-16
    in the block's own header decides.
    """
    for k, tag in ((0x0000, 'plain'), (FIXED_KEY, 'xor 0x%04X' % FIXED_KEY)):
        try:
            return unpack(blob, stream_key=False, key=k), tag
        except Exception:
            pass
    r = rnc.Reader(blob[18:])
    r.bits(2)
    k = r.bits(16)
    return unpack(blob, stream_key=True), 'xor 0x%04X (from stream)' % k


if __name__ == '__main__':
    b = open(sys.argv[1], 'rb').read()
    o, how = auto(b)
    print('%s -> %d bytes, CRC ok, key %s' % (sys.argv[1], len(o), how))
    if len(sys.argv) > 2:
        open(sys.argv[2], 'wb').write(o)
