"""wiz4krn.py -- Wizardry IV message text: ASCII.HUFF + ASCII.KRN.

ASCII.HUFF (1,024 bytes) is a 255-node Huffman tree in three 256-byte arrays:
    flags[n]  bit 0: the LEFT child is a leaf;  bit 1: the RIGHT child is a leaf
    left[n]   a node index, or the symbol if the flag says leaf
    right[n]  likewise
and 256 zero bytes. Node 0 is the root. A 1 bit goes LEFT, a 0 bit goes RIGHT,
and bits are taken least significant first from each byte.

ASCII.KRN is 512-byte blocks. Text blocks hold, from the front, lines; from
the back, a dictionary read backwards:

    last byte          number of messages M in this block
    then, M times      [delta]  nlines  size_1 .. size_nlines
                       (delta is one byte, or two when its first byte has bit 7
                       set: ((b0 & 0x7F) << 8) | b1; it is absent for the
                       block's first message, whose
                       number is the index entry for the block; each later
                       message's number is the previous one + delta)

A line is byte-aligned: one Huffman symbol giving its length, then that many
Huffman symbols, then zero padding to the byte; size_i is the line's length
in bytes including the length symbol and padding. Block 0 begins with two
16-bit words (the index block's number, and one more value reported as read).
The index block holds one word per text block: the number of its first
message, then 32767.

Closures checked on every block (printed by --audit):
  * every line decodes to exactly its dictionary size, to the byte;
  * the lines tile from the block's text start with no gap;
  * the lines end before the dictionary begins;
  * message numbers ascend, and each block's first equals the index entry.

Usage:
    python tools/wiz4krn.py HUFF KRN --audit
    python tools/wiz4krn.py HUFF KRN --dump            # every message, numbered
    python tools/wiz4krn.py HUFF --codes               # the code table
    python tools/wiz4krn.py --selftest
"""
import struct
import sys


class Refused(Exception):
    pass


class Tree:
    def __init__(self, huff):
        if len(huff) != 1024:
            raise Refused('HUFF is %d bytes, not 1024' % len(huff))
        if huff[768:] != bytes(256):
            raise Refused('HUFF bytes 768..1023 are not zero')
        self.F, self.L, self.R = huff[0:256], huff[256:512], huff[512:768]
        self.codes = {}
        self._walk(0, '', 0)
        if len(self.codes) != 256:
            raise Refused('tree has %d leaves, not 256' % len(self.codes))

    def _walk(self, node, prefix, depth):
        if depth > 255:
            raise Refused('tree deeper than 255')
        for arr, bit, flag in ((self.L, '1', 1), (self.R, '0', 2)):
            if self.F[node] & flag:
                if arr[node] in self.codes:
                    raise Refused('symbol %d twice' % arr[node])
                self.codes[arr[node]] = prefix + bit
            else:
                self._walk(arr[node], prefix + bit, depth + 1)


class Bits:
    def __init__(self, data, bytepos):
        self.d, self.pos = data, bytepos * 8

    def sym(self, t):
        node = 0
        while True:
            if self.pos >= len(self.d) * 8:
                raise Refused('ran off the data')
            b = (self.d[self.pos >> 3] >> (self.pos & 7)) & 1
            self.pos += 1
            if b:
                if t.F[node] & 1:
                    return t.L[node]
                node = t.L[node]
            else:
                if t.F[node] & 2:
                    return t.R[node]
                node = t.R[node]


def line_at(t, blk, off):
    br = Bits(blk, off)
    n = br.sym(t)
    s = bytes(br.sym(t) for _ in range(n))
    return s, (br.pos + 7) // 8 - off


def read_dict(blk):
    m = blk[511]
    p = 510
    msgs = []
    for i in range(m):
        delta = 0
        if i:
            delta = blk[p]
            p -= 1
            if delta & 0x80:
                delta = ((delta & 0x7F) << 8) | blk[p]
                p -= 1
        n = blk[p]
        p -= 1
        sizes = [blk[p - j] for j in range(n)]
        p -= n
        msgs.append((delta, sizes))
    return msgs, p + 1  # first byte of the dictionary


def find_index(krn):
    nb = len(krn) // 512
    first = struct.unpack_from('<H', krn, 0)[0]
    if not 0 < first < nb:
        raise Refused('block 0 word 0 is %d, not a block of this file' % first)
    return first


def parse(huff, krn):
    t = Tree(huff)
    if len(krn) % 512:
        raise Refused('KRN is not whole blocks')
    ib = find_index(krn)
    idx = []
    for j in range(256):
        w = struct.unpack_from('<H', krn, ib * 512 + 2 * j)[0]
        idx.append(w)
        if w == 32767:
            break
    else:
        raise Refused('index has no 32767 sentinel')
    ntext = len(idx) - 1
    out = []
    audit = []
    prev = 0
    for b in range(ntext):
        blk = krn[b * 512:(b + 1) * 512]
        start = 4 if b == 0 else 0
        msgs, dstart = read_dict(blk)
        off = start
        num = idx[b]
        bad = 0
        nl = 0
        for i, (delta, sizes) in enumerate(msgs):
            num = num + delta if i else idx[b]
            if num <= prev:
                bad += 1
            prev = num
            lines = []
            for sz in sizes:
                s, used = line_at(t, blk, off)
                if used != sz:
                    bad += 1
                lines.append(s)
                off += sz
                nl += 1
            out.append((num, b, lines))
        if off > dstart:
            bad += 1
        audit.append((b, idx[b], len(msgs), nl, start, off, dstart, bad))
    return t, ib, idx, out, audit, struct.unpack_from('<H', krn, 2)[0]


def show(s):
    return ''.join(chr(c) if 32 <= c < 127 else '{%02X}' % c for c in s)


def main(a):
    if not a or a[0] == '--selftest':
        return selftest()
    if '--codes' in a:
        t = Tree(open(a[0], 'rb').read())
        for c, code in sorted(t.codes.items(), key=lambda kv: (len(kv[1]), kv[0])):
            print('%3d %-6s %2d %s' % (c, repr(chr(c)) if 32 <= c < 127 else '-', len(code), code))
        return 0
    huff, krn = open(a[0], 'rb').read(), open(a[1], 'rb').read()
    t, ib, idx, out, audit, w1 = parse(huff, krn)
    if '--audit' in a:
        print('tree               : 256 leaves, depth %d..%d' % (
            min(map(len, t.codes.values())), max(map(len, t.codes.values()))))
        print('index block        : %d   (block 0 word 0)   block 0 word 1: %d' % (ib, w1))
        print('text blocks        : %d   index entries %d + sentinel 32767' % (len(audit), len(idx) - 1))
        print()
        print('blk  first#  msgs lines  text..end  dict@  slack  bad')
        tb = tl = tm = tbad = slack = text = 0
        for b, first, m, nl, st, end, ds, bad in audit:
            print('%3d  %6d  %4d %5d  %4d..%4d  %4d  %5d  %3d' % (b, first, m, nl, st, end, ds, ds - end, bad))
            tm += m
            tl += nl
            tbad += bad
            slack += ds - end
            text += end - st
        print()
        print('messages %d   lines %d   failures %d' % (tm, tl, tbad))
        print('text bytes %d   dictionary bytes %d   slack between them %d   header 4' % (
            text, sum(512 - ds for _, _, _, _, _, _, ds, _ in audit), slack))
        nums = [n for n, _, _ in out]
        print('message numbers %d..%d, %d distinct' % (min(nums), max(nums), len(set(nums))))
        chars = sum(len(s) for _, _, ls in out for s in ls)
        print('characters %d   bits/char %.3f' % (chars, 8.0 * text / max(chars, 1)))
    if '--dump' in a:
        for num, b, lines in out:
            print('#%05d  (block %d, %d line%s)' % (num, b, len(lines), '' if len(lines) == 1 else 's'))
            for s in lines:
                print('        |%s' % show(s))
    return 0


def selftest():
    ok = 0
    # a 4-symbol tree: root L=leaf 'a'(1), R=node1; node1 L=leaf 'b'(01), R=node2; node2 L=leaf 2 (001), R=leaf 0 (000)
    huff = bytearray(1024)
    F, L, R = 0, 256, 512
    huff[F + 0], huff[L + 0], huff[R + 0] = 1, ord('a'), 1
    huff[F + 1], huff[L + 1], huff[R + 1] = 1, ord('b'), 2
    # the remaining 252 symbols hang off a chain so the tree has 256 leaves
    sym = [c for c in range(256) if c not in (ord('a'), ord('b'))]
    node = 2
    for i, c in enumerate(sym[:-1]):
        huff[F + node] = 1
        huff[L + node] = c
        if i == len(sym) - 2:
            huff[F + node] |= 2
            huff[R + node] = sym[-1]
        else:
            huff[R + node] = node + 1
        node += 1
    t = Tree(bytes(huff))
    assert t.codes[ord('a')] == '1' and t.codes[ord('b')] == '01'; ok += 1
    code2 = t.codes[2]

    def pack(bits):
        out = bytearray((len(bits) + 7) // 8)
        for i, c in enumerate(bits):
            if c == '1':
                out[i >> 3] |= 1 << (i & 7)
        return bytes(out)
    line = pack(code2 + '1' + '01')  # len 2, 'a', 'b'
    s, used = line_at(t, line + b'\0', 0)
    assert s == b'ab' and used == len(line); ok += 1
    for bad in (bytes(1023), bytes(huff[:768]) + b'\1' + bytes(255)):
        try:
            Tree(bad)
            raise AssertionError('accepted a bad tree')
        except Refused:
            ok += 1
    blk = bytearray(512)
    blk[511], blk[510], blk[509], blk[508], blk[507], blk[506], blk[505] = 2, 1, 7, 3, 2, 5, 4
    msgs, ds = read_dict(bytes(blk))
    assert msgs == [(0, [7]), (3, [5, 4])] and ds == 505; ok += 1
    blk[508], blk[507], blk[506], blk[505], blk[504] = 0x82, 0x0B, 1, 9, 0
    msgs, ds = read_dict(bytes(blk))
    assert msgs == [(0, [7]), (523, [9])] and ds == 505; ok += 1
    print('selftest: %d checks, 0 failures' % ok)


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]) or 0)
    except Refused as r:
        print('REFUSED: %s' % r)
        sys.exit(1)
