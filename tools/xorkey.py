#!/usr/bin/env python3
"""Recover the 16-bit XOR key of an RNC block on this disc, by measurement.

CRC-16/ARC with a zero initial value and no final inversion is linear over
GF(2): `crc(A ^ B) == crc(A) ^ crc(B)` for messages of equal length.  So the
key can be solved rather than searched:

  1. decode the block once with key 0, recording for every output byte which
     literal run it descends from (a match copy inherits its source byte's run);
  2. the mask that the real key would have XORed in is
     `mask[i] = ror16(K, run[i]) & 0xFF`, which is a XOR of 128 basis masks --
     one per (run class 0..15, bit 0..7);
  3. CRC each basis mask once, then every candidate key is a XOR of at most
     128 precomputed words, and the 65,536 candidates cost nothing.

    python tools/xorkey.py <file> [offset]
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rnc


def decode_prov(blob):
    """Decode with key 0 and return (bytes, run-class per byte, run count)."""
    ulen = int.from_bytes(blob[4:8], 'big')
    plen = int.from_bytes(blob[8:12], 'big')
    r = rnc.Reader(blob[18:18 + plen])
    r.bits(2)
    out = bytearray()
    prov = bytearray()
    run = 0
    while len(out) < ulen:
        raw, lens, poss = rnc._table(r), rnc._table(r), rnc._table(r)
        sub = r.bits(16)
        while sub:
            sub -= 1
            n = rnc._value(r, raw)
            if n:
                out += r.literals(n)
                prov += bytes([run % 16]) * n
                run += 1
            if sub:
                off = rnc._value(r, lens) + 1
                cnt = rnc._value(r, poss) + 2
                for _ in range(cnt):
                    out.append(out[-off])
                    prov.append(prov[-off])
    return bytes(out), bytes(prov), run


def solve(blob):
    base, prov, nruns = decode_prov(blob)
    want = int.from_bytes(blob[12:14], 'big')
    target = rnc.crc16(base) ^ want
    # basis CRCs: class r, bit b
    basis = [[0] * 8 for _ in range(16)]
    for r_ in range(16):
        sel = [i for i, p in enumerate(prov) if p == r_]
        if not sel:
            continue
        for b in range(8):
            msg = bytearray(len(base))
            v = 1 << b
            for i in sel:
                msg[i] = v
            basis[r_][b] = rnc.crc16(bytes(msg))
    for K in range(65536):
        acc = 0
        k = K
        for r_ in range(16):
            kb = k & 0xFF
            if kb:
                row = basis[r_]
                for b in range(8):
                    if kb >> b & 1:
                        acc ^= row[b]
            k = ((k >> 1) | ((k & 1) << 15)) & 0xFFFF
        if acc == target:
            return K, len(base), nruns
    return None, len(base), nruns


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    o = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0
    K, n, runs = solve(d[o:])
    print("%s+%d: %d bytes, %d literal runs, key %s" %
          (sys.argv[1], o, n, runs, ('0x%04X' % K) if K is not None else 'NOT FOUND'))
