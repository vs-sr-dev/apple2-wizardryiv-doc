#!/usr/bin/env python3
"""PowerPacker 2.0 (`PP20`) data-file decruncher.

Layout of a PP20 data file:

    0x00  'PP20'
    0x04  four offset-length bytes (the "efficiency" table)
    0x08  packed bit stream
    -4    24-bit unpacked length, then one byte of bits to skip

The bit stream is read *backwards* in big-endian longwords from the end of
the packed data, consuming bits from the low end of the longword and
assembling each field most-significant-bit first.  Output is written
backwards from the end of the destination buffer.

PowerPacker carries **no checksum**, so the only validation available is
structural: the decruncher must consume the stream and land on exactly the
declared length.  `unpack()` raises if it does not.

Usage:  python3 tools/pp20.py <file> [-o OUT]
        python3 tools/pp20.py --dir EXTRACTDIR --out UNPACKDIR
"""
import sys, os, argparse


def is_pp20(b):
    return len(b) >= 12 and b[:4] == b'PP20'


def info(b):
    if not is_pp20(b):
        raise ValueError("not a PP20 file")
    tail = b[-4:]
    return {
        'offset_lens': list(b[4:8]),
        'unpacked': (tail[0] << 16) | (tail[1] << 8) | tail[2],
        'skip_bits': tail[3],
        'packed': len(b) - 12,
    }


class _Bits(object):
    """Backwards big-endian longword bit reader."""

    def __init__(self, data, end):
        self.d = data
        self.p = end          # exclusive; refills read the 4 bytes below p
        self.buf = 0
        self.left = 0

    def get(self, n):
        r = 0
        for _ in range(n):
            if self.left == 0:
                if self.p < 4:
                    raise ValueError("PP20 stream underrun")
                self.p -= 4
                self.buf = int.from_bytes(self.d[self.p:self.p + 4], 'big')
                self.left = 32
            r = (r << 1) | (self.buf & 1)
            self.buf >>= 1
            self.left -= 1
        return r


def unpack(b):
    h = info(b)
    olens = h['offset_lens']
    dest_len = h['unpacked']
    out = bytearray(dest_len)
    bits = _Bits(b, len(b) - 4)
    bits.get(h['skip_bits'])

    o = dest_len                      # write pointer, moves down
    written = 0
    while written < dest_len:
        if bits.get(1) == 0:
            todo = 1
            while True:
                x = bits.get(2)
                todo += x
                if x != 3:
                    break
            for _ in range(todo):
                o -= 1
                out[o] = bits.get(8)
                written += 1
            if written >= dest_len:
                break
        x = bits.get(2)
        offbits = olens[x]
        todo = x + 2
        if x == 3:
            if bits.get(1) == 0:
                offbits = 7
            offset = bits.get(offbits)
            while True:
                y = bits.get(3)
                todo += y
                if y != 7:
                    break
        else:
            offset = bits.get(offbits)
        for _ in range(todo):
            src = o + offset
            if src >= dest_len:
                raise ValueError("PP20 back-reference past end of buffer")
            v = out[src]
            o -= 1
            out[o] = v
            written += 1

    if written != dest_len or o != 0:
        raise ValueError("PP20 length mismatch: wrote %d of %d (o=%d)"
                         % (written, dest_len, o))
    return bytes(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?")
    ap.add_argument("-o", "--out")
    ap.add_argument("--dir")
    a = ap.parse_args()
    if a.dir:
        for root, _, names in os.walk(a.dir):
            for n in sorted(names):
                p = os.path.join(root, n)
                d = open(p, 'rb').read()
                if not is_pp20(d):
                    continue
                rel = os.path.relpath(p, a.dir).replace(chr(92), '/')
                try:
                    u = unpack(d)
                    ok = "ok"
                except Exception as e:
                    u, ok = b'', str(e)
                h = info(d)
                print("%-24s %8d -> %8d  ratio %5.1f%%  olens=%s skip=%2d  %s"
                      % (rel, len(d), h['unpacked'],
                         100.0 * len(d) / h['unpacked'] if h['unpacked'] else 0,
                         h['offset_lens'], h['skip_bits'], ok))
                if a.out and u:
                    q = os.path.join(a.out, rel)
                    os.makedirs(os.path.dirname(q) or '.', exist_ok=True)
                    open(q, 'wb').write(u)
        return
    d = open(a.file, 'rb').read()
    print(info(d), file=sys.stderr)
    u = unpack(d)
    if a.out:
        open(a.out, 'wb').write(u)
    else:
        sys.stdout.buffer.write(u)


if __name__ == "__main__":
    main()
