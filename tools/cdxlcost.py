#!/usr/bin/env python3
"""What the same footage would have cost in CDXL.

CDXL is Commodore's own streaming animation format and it is uncompressed: a
frame costs the same whatever is in it.  This reproduces the comparison in
docs/06-video-codec.md from the measured frame sizes written by
tools/animscan.py, so every figure can be checked.
"""
import json, sys

RATE = 150 * 2048           # 2x CD, the speed CD_CONFIG asks cd.device for
W, H = 320, 144             # from the CPIC payload header
d = json.load(open('_work/animframes.json'))
fs = sorted(d['framesizes']); n = len(fs); tot = sum(fs)

print('measured: %d frames, %d bytes of video payload' % (n, tot))
print('          %d bytes/frame average, %d largest, %d smallest'
      % (tot // n, fs[-1], fs[0]))
print()
print('frame-size distribution')
for p in (0, 1, 5, 10, 25, 50, 75, 90, 99, 100):
    print('  p%-3d %7d bytes' % (p, fs[int(p / 100 * (n - 1))]))
print('  under 5,000 bytes: %d frames (%.1f %%)'
      % (sum(1 for x in fs if x < 5000), 100 * sum(1 for x in fs if x < 5000) / n))
print('  under 2,000 bytes: %d frames' % sum(1 for x in fs if x < 2000))
print()
print('%-34s %9s %9s %10s' % ('format', 'B/frame', 'fps at 2x', 'MB for %d' % n))
for planes in (8, 7, 6, 5, 4, 3):
    b = W // 8 * H * planes
    print('%-34s %9d %9.2f %10.0f'
          % ('CDXL %d planes (%d colours)' % (planes, 2 ** planes),
             b, RATE / b, n * b / 1048576))
b = 240 // 8 * 96 * 7
print('%-34s %9d %9.2f %10.0f'
      % ('CDXL at Prey CD32 geometry 240x96x7', b, RATE / b, n * b / 1048576))
avg = tot / n
print('%-34s %9d %9.2f %10.0f'
      % ('Microcosm, measured', avg, RATE / avg, tot / 1048576))
print()
print('compression against an 8-plane raw frame (%d bytes): %.2f:1 on average,'
      % (W // 8 * H * 8, (W // 8 * H * 8) / avg))
print('but only %.2f:1 on the largest frame, which is %.1f %% of raw.'
      % ((W // 8 * H * 8) / fs[-1], 100 * fs[-1] / (W // 8 * H * 8)))
