"""Decrunch a headerless Imploder stream: data at [0..n), 38-byte tail after.

The 12-byte 'IMP!' header exists only so the decruncher can shuffle the last
twelve bytes of the stream down to offset 0 and make it contiguous.  A stream
stored without a header is already in that state, so the only unknown is the
unpacked length -- and that falls out of running until the read pointer hits
zero rather than until the write pointer does.
"""
import struct, sys

def decrunch_raw(data, tail, room=4 << 20):
    buf = bytearray(room + 0x10000)   # slack above the output for stray matches
    n = len(data)
    buf[:n] = data
    d2 = struct.unpack_from('>I', tail, 0)[0]
    d3w = struct.unpack_from('>H', tail, 4)[0]
    base = struct.unpack_from('>8H', tail, 6)
    nbits = tail[22:34]
    a3 = n
    a4 = room
    d3 = d3w & 0xFF
    x = 0
    if not (d3w & 0x8000):
        a3 -= 1

    def bit():
        nonlocal d3, a3, x
        r = (d3 * 2) & 0xFF
        c = d3 >> 7
        if r:
            d3, x = r, c
            return c
        a3 -= 1
        s = buf[a3] * 2 + c
        d3, x = s & 0xFF, s >> 8
        return x

    def bits(k):
        v = 0
        for _ in range(k):
            v = v * 2 + bit()
        return v

    LITBASE = (6, 10, 10, 18)
    LITBITS = (1, 1, 1, 1, 2, 3, 3, 4, 4, 5, 7, 14)
    while True:
        while d2:
            a3 -= 1; a4 -= 1
            buf[a4] = buf[a3]
            d2 -= 1
        if a3 <= 0:
            break
        if not bit():          d4, cls = 1, 0
        elif not bit():        d4, cls = 2, 1
        elif not bit():        d4, cls = 3, 2
        elif not bit():        d4, cls = 4, 3
        elif not bit():        d4, cls = bits(3) + 5, 3
        else:
            a3 -= 1
            d4, cls = (buf[a3] - 1) & 0xFF, 3
        if not bit():          i, d5 = cls, 0
        elif not bit():        i, d5 = cls + 4, 2
        else:                  i, d5 = cls + 8, LITBASE[cls]
        d2 = (bits(LITBITS[i]) + d5) & 0xFFFF
        if not bit():          j, off = cls, 0
        elif not bit():        j, off = cls + 4, base[cls]
        else:                  j, off = cls + 8, base[cls + 4]
        src = a4 + off + bits(nbits[j]) + 1
        for _ in range(d4 + 1):
            src -= 1; a4 -= 1
            buf[a4] = buf[src]
        if a3 <= 0:
            break
    return bytes(buf[a4:]), a3

if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    a, e = int(sys.argv[2], 0), int(sys.argv[3], 0)      # data start, tail start
    out, a3 = decrunch_raw(d[a:e], d[e:e+38])
    sys.stderr.write('%d packed -> %d unpacked, read pointer landed on %d\n'
                     % (e-a, len(out), a3))
    if len(sys.argv) > 4:
        open(sys.argv[4], 'wb').write(out)
