#!/usr/bin/env python3
"""Inventory the four asset families, from the CrunchMania-decrunched tree.

    python tools/assets.py _work/unpacked
"""
import sys, os, struct, collections


def objs(root):
    d = os.path.join(root, 'objs')
    print("## objs/  - chunky sprite banks")
    print()
    print("| file | bytes | rotations | states | frames | max w | max h |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for f in sorted(os.listdir(d)):
        b = open(os.path.join(d, f), 'rb').read()
        a, c, w, h, sz = struct.unpack_from('>HHHHI', b, 0)
        first = struct.unpack_from('>I', b, 12)[0]
        n = (first - 12) // 4
        print("| `%s` | %d | %d | %d | %d | %d | %d |" % (f, len(b), 1 << a, c, n, w, h))
    print()


def txts(root):
    d = os.path.join(root, 'txts')
    print("## txts/  - chunky texture banks")
    print()
    print("| file | bytes | textures | palette at | palette words | used | 0xFFFF |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for f in sorted(os.listdir(d)):
        b = open(os.path.join(d, f), 'rb').read()
        if f.startswith(('floor', 'roof')):
            n = struct.unpack_from('>H', b, 16384)[0] + 1
            print("| `%s` | %d | 1 x 128x128 | 16384 | %d | %d | 0 |" % (f, len(b), n, n))
            continue
        po = struct.unpack_from('>I', b, 0)[0]
        n = (po - 4) // 4160
        words = (len(b) - po) // 2
        used = sum(1 for i in range(words)
                   if struct.unpack_from('>H', b, po + i * 2)[0] != 0xFFFF)
        print("| `%s` | %d | %d x 65x64 | %d | %d | %d | %d |" %
              (f, len(b), n, po, words, used, words - used))
    print()


def maps(root):
    d = os.path.join(root, 'maps')
    print("## maps/  - level files")
    print()
    print("| file | bytes | sections | grid | non-empty sections |")
    print("|---|---:|---:|---:|---:|")
    for f in sorted(os.listdir(d)):
        b = open(os.path.join(d, f), 'rb').read()
        n = struct.unpack_from('>I', b, 0)[0] // 4
        offs = [struct.unpack_from('>I', b, i * 4)[0] for i in range(n)] + [len(b)]
        sizes = [offs[i + 1] - offs[i] for i in range(n)]
        live = sum(1 for s in sizes if s > 4)
        print("| `%s` | %d | %d | %d | %d |" % (f, len(b), n, sizes[0], live))
    print()


def sfxs(root):
    d = os.path.join(root, 'sfxs')
    print("## sfxs/  - raw 8-bit PCM and OctaMED modules")
    print()
    print("| file | bytes | period | rate (PAL) | words | check |")
    print("|---|---:|---:|---:|---:|---|")
    for f in sorted(os.listdir(d)):
        b = open(os.path.join(d, f), 'rb').read()
        if b[:4] in (b'MMD0', b'MMD1', b'MMD2', b'MMD3'):
            print("| `%s` | %d | | | | OctaMED `%s` |" % (f, len(b), b[:4].decode()))
            continue
        per, n = struct.unpack_from('>HH', b, 0)
        ok = (4 + 2 * n == len(b))
        print("| `%s` | %d | %d | %d | %d | %s |" %
              (f, len(b), per, round(3546895 / per), n, "4+2n==size" if ok else "MISMATCH"))
    print()


def pics(root):
    d = os.path.join(root, 'pics')
    print("## pics/  - 7-bitplane screens")
    print()
    print("| file | bytes | w | h | planes | bitmap | ByteRun1 |")
    print("|---|---:|---:|---:|---:|---:|---|")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from pic import unrle
    for f in sorted(os.listdir(d)):
        if f.endswith('.pal'):
            continue
        b = open(os.path.join(d, f), 'rb').read()
        w, h, pl, _, sz = struct.unpack_from('>HHHHI', b, 0)
        got = len(unrle(b[12:]))
        print("| `%s` | %d | %d | %d | %d | %d | %s |" %
              (f, len(b), w, h, pl, sz, "exact" if got == sz else "%d" % got))
    print()


if __name__ == '__main__':
    root = sys.argv[1]
    for fn in (objs, txts, maps, sfxs, pics):
        fn(root)
