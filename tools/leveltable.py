#!/usr/bin/env python3
"""Walk RoboCod's 12-byte-per-level table and read the music column.

The table's address and stride are not guessed. They come out of the routine
that starts a level:

    015b66  41 f9 00 02 cf 3a    lea.l   $2cf3a.l, a0     ; the table
    015b6c  30 39 00 03 c5 9a    move.w  $3c59a.l, d0     ; the level number
    015b72  c0 fc 00 0c          mulu.w  #$c, d0          ; 12 bytes per record
    015b78  41 f0 00 00          lea.l   (a0, d0.w), a0
    015c8e  10 28 00 0b          move.b  $b(a0), d0       ; byte 11 = the music id
    015c92  4e b9 00 00 bd 6a    jsr     $bd6a.l          ; play it

and the music id is interpreted by the routine at hunk $bd6a: bit 7 set means
"CD track (id & 0x7f)", bit 7 clear means "internal replayer, index id".

The table has no length field. The walk stops at the first record that fails
two independent sanity conditions — byte 0 (the world number) in 1..15 and
byte 11 having bit 7 set or being a small internal index — which is a weaker
test than a stored count and is why the terminator is printed.

Usage:  python tools/leveltable.py extract/RoboCod [--base 0x2cf3a] [--stride 12]
"""
import sys, argparse, collections

HUNK0_FILE_OFFSET = 40      # three-hunk header with no resident list


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file', nargs='?', default='extract/RoboCod')
    ap.add_argument('--base', type=lambda s: int(s, 0), default=0x2cf3a,
                    help='hunk-0 offset of the table')
    ap.add_argument('--stride', type=int, default=12)
    ap.add_argument('--music', type=int, default=0x0b,
                    help='byte within the record holding the music id')
    ap.add_argument('--max', type=int, default=400)
    a = ap.parse_args()

    d = open(a.file, 'rb').read()
    base = a.base + HUNK0_FILE_OFFSET
    print("table at hunk 0x%x = file 0x%x, %d bytes per record"
          % (a.base, base, a.stride))
    print(" idx  record                                     music  meaning")
    music = collections.Counter()
    world = collections.Counter()
    n = 0
    for i in range(a.max):
        r = d[base + i * a.stride: base + (i + 1) * a.stride]
        m = r[a.music]
        if not (1 <= r[0] <= 15) or not (0x80 <= m <= 0x8f):
            print(" %3d  %s   <- stops here" % (i, r.hex(' ')))
            break
        n = i + 1
        music[m] += 1
        world[r[0]] += 1
        kind = ("CD track %d" % (m & 0x7f)) if m & 0x80 else ("internal tune %d" % m)
        print(" %3d  %s    %02x    %s" % (i, r.hex(' '), m, kind))

    print()
    print("records that fit the pattern: %d" % n)
    print("table spans hunk 0x%x .. 0x%x (%d bytes)"
          % (a.base, a.base + n * a.stride - 1, n * a.stride))
    print("music ids : %s" % {hex(k): v for k, v in sorted(music.items())})
    print("CD tracks : %s" % {(k & 0x7f): v for k, v in sorted(music.items())})
    print("byte 0 (world) histogram: %s" % dict(sorted(world.items())))
    print()
    print("internal-replayer entries (bit 7 clear) in the whole table: %d"
          % sum(v for k, v in music.items() if not k & 0x80))


if __name__ == '__main__':
    main()
