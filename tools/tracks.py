"""Read the cue sheet's audio tracks and print their real durations.

The `.wav` files a redump-style rip produces are plain 44.1 kHz 16-bit
stereo, so the sector count is bytes/2352 and the duration is bytes/176400.

Usage: tracks.py <directory containing the cue and the wavs>
"""
import sys, os, glob, struct

d = sys.argv[1] if len(sys.argv) > 1 else '.'
cue = glob.glob(os.path.join(d, '*.cue'))
if cue:
    print(open(cue[0]).read().splitlines()[0])
iso = sorted(glob.glob(os.path.join(d, '*Track 01*.iso')))
if iso:
    n = os.path.getsize(iso[0])
    print('track 01  %12d bytes  %6d sectors  data' % (n, n // 2048))
tot = 0
for p in sorted(glob.glob(os.path.join(d, '*.wav'))):
    h = open(p, 'rb').read(44)
    ch, rate = struct.unpack_from('<HI', h, 22)
    bits = struct.unpack_from('<H', h, 34)[0]
    n = os.path.getsize(p) - 44
    tot += n
    print('%s  %12d bytes  %6d sectors  %7.1f s  %d ch %d Hz %d bit'
          % (os.path.basename(p)[-24:-4], n, n // 2352,
             n / (rate * ch * bits // 8), ch, rate, bits))
print('audio total %d bytes, %d sectors, %.1f s = %d:%04.1f'
      % (tot, tot // 2352, tot / 176400, tot / 176400 // 60,
         tot / 176400 % 60))
