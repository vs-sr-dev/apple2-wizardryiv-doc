#!/usr/bin/env python3
"""CrunchMania decruncher (CrM2, and the CrM! variant the loader also carries).

Transcribed register-for-register from the decoder inside the shipped Gloom
executable: dispatcher at code-hunk offset 0x24d7c, CrM! decoder at 0x24daa,
CrM2 decoder at 0x24eb8 (file offsets 0x24d9c / 0x24dca / 0x24ed8).

Container, 14 bytes big-endian:

    0   'CrM2' (or 'CrM!')
    4   UWORD  leeway - extra bytes needed to decrunch in place
    6   ULONG  unpacked length
    10  ULONG  packed length      (14 + packed == filesize on all 115 files)
    14  the stream, read BACKWARDS from its last byte

    python tools/crm.py <file> [-o out]
    python tools/crm.py -a <dir> -o <outdir>     unpack a whole tree
"""
import sys, os, struct

MASK = [(1 << n) - 1 for n in range(33)]


class Bits:
    """d6 = 32-bit buffer, d7 = bit counter, a2 = input pointer walking down."""

    def __init__(self, data, end):
        self.d = data
        self.p = end
        self.p -= 2
        d0 = struct.unpack_from('>H', self.d, self.p)[0]
        self.p -= 4
        self.d6 = struct.unpack_from('>I', self.d, self.p)[0]
        self.d7 = (16 - d0) & 0xFFFF
        self.d6 = (self.d6 >> self.d7) & 0xFFFFFFFF
        self.d7 = d0

    def _word(self):
        self.p -= 2
        if self.p < 0:
            raise ValueError("stream underrun")
        return struct.unpack_from('>H', self.d, self.p)[0]

    def bit(self):
        """the READBIT half of the Huffman loop at 0x24f8c"""
        self.d7 = (self.d7 - 1) & 0xFFFF
        if self.d7 != 0:
            c = self.d6 & 1
            self.d6 >>= 1
        else:
            self.d7 = 16
            c = self.d6 & 1
            v = (self.d6 >> 1) & 0xFFFF          # lsr.l #1 then keep low word
            self.d6 = (self._word() << 16) | v   # swap / move.w -(a2),d6 / swap
        return c

    def get(self, k):
        """GETBITS at 0x24fb8"""
        d0 = self.d6 & 0xFFFF
        self.d6 = (self.d6 >> k) & 0xFFFFFFFF
        d7 = self.d7 - k
        if d7 <= 0:
            d7 += 16
            v = self.d6 & 0xFFFFFFFF
            v = ((v >> d7) | (v << (32 - d7))) & 0xFFFFFFFF        # ror.l d7,d6
            v = (v & 0xFFFF0000) | self._word()                    # move.w -(a2),d6
            v = ((v << d7) | (v >> (32 - d7))) & 0xFFFFFFFF        # rol.l d7,d6
            self.d6 = v
        self.d7 = d7
        return d0 & MASK[k]


def read_table(b, maxbits):
    """READTBL at 0x24ff0 -> (counts[16], symbols[])"""
    counts = [0] * 16
    n = b.get(4)
    total = 0
    for i in range(n):
        k = min(i + 1, maxbits)
        counts[i] = b.get(k)
        total += counts[i]
    syms = [b.get(maxbits) for _ in range(total)]
    return counts, syms


def build(counts):
    """BUILD at 0x2502e -> (limit[16], base[16]) for the canonical decoder"""
    limit = [0] * 16
    base = [0] * 16
    d2 = 0
    d3 = 0
    prev = 0                       # the cleared word in front of limit[0]
    for i in range(15):
        d6 = counts[i]
        base[i] = (d3 - 2 * prev) & 0xFFFF
        d3 = (d3 + d6) & 0xFFFF
        d2 = (d2 + d6) & 0xFFFF
        limit[i] = d2
        prev = d2
        d2 = (d2 << 1) & 0xFFFF
    return limit, base


def huff(b, limit, base, syms):
    """HUFF at 0x24f8a"""
    d1 = 0
    for i in range(16):
        d1 = ((d1 << 1) | b.bit()) & 0xFFFF
        if limit[i] > d1:
            idx = (d1 + base[i]) & 0xFFFF
            return syms[idx]
    raise ValueError("huffman code too long")


def decrunch(blob):
    magic = blob[:4]
    if magic not in (b'CrM2', b'CrM!'):
        raise ValueError("not a CrunchMania file: %r" % magic)
    leeway, unp, pk = struct.unpack_from('>HII', blob, 4)
    if 14 + pk != len(blob):
        raise ValueError("14 + packed (%d) != filesize (%d)" % (pk, len(blob)))
    if magic == b'CrM!':
        raise NotImplementedError("CrM! stream: no file on the disc uses it")
    b = Bits(blob, 14 + pk)
    out = bytearray(unp)
    w = unp                                   # a1, walking down
    while True:
        c1, s1 = read_table(b, 9)             # length/literal alphabet, 9-bit symbols
        c2, s2 = read_table(b, 4)             # offset-width alphabet, 4-bit symbols
        l1, b1 = build(c1)
        l2, b2 = build(c2)
        n = b.get(16)                         # symbols in this block, minus one
        for _ in range(n + 1):
            d0 = huff(b, l1, b1, s1)
            if d0 & 0x100:
                w -= 1
                out[w] = d0 & 0xFF
                continue
            d4 = d0
            k = huff(b, l2, b2, s2)
            if k == 0:
                bits, setbit = 1, 16
            else:
                bits, setbit = k, k
            v = b.get(bits)
            v |= (1 << setbit)
            off = v & 0xFFFF                  # lea $1(a1,d0.w) uses the low word only
            src = w + off + 1
            for _ in range(d4 + 3):
                src -= 1
                w -= 1
                out[w] = out[src]
        if b.get(1) == 0:
            break
    if w != 0:
        raise ValueError("output pointer landed on %d, not 0" % w)
    return bytes(out), leeway


def main():
    a = sys.argv[1:]
    out = None
    if '-o' in a:
        i = a.index('-o'); out = a[i + 1]; del a[i:i + 2]
    if a and a[0] == '-a':
        root = a[1]
        ok = fail = skip = 0
        for dp, dn, fn in os.walk(root):
            dn.sort()
            for f in sorted(fn):
                p = os.path.join(dp, f)
                blob = open(p, 'rb').read()
                rel = os.path.relpath(p, root).replace(chr(92), '/')
                if not blob.startswith(b'CrM'):
                    skip += 1
                    continue
                try:
                    d, lw = decrunch(blob)
                except Exception as e:
                    print("FAIL %-24s %s" % (rel, e)); fail += 1; continue
                ok += 1
                print("ok   %-24s %7d -> %7d  (%.1f%%, leeway %d)" %
                      (rel, len(blob), len(d), 100.0 * len(blob) / len(d), lw))
                if out:
                    q = os.path.join(out, rel)
                    os.makedirs(os.path.dirname(q), exist_ok=True)
                    open(q, 'wb').write(d)
        print("\n%d decrunched, %d failed, %d not packed" % (ok, fail, skip))
        return
    blob = open(a[0], 'rb').read()
    d, lw = decrunch(blob)
    sys.stderr.write("%d -> %d bytes, leeway %d\n" % (len(blob), len(d), lw))
    if out: open(out, 'wb').write(d)
    else: sys.stdout.buffer.write(d)


if __name__ == '__main__':
    main()
