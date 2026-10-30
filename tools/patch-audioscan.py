#!/usr/bin/env python3
"""Vectorise the per-sample statistics in tools/audioscan.py.

The first version walked 54 million stereo samples in a Python loop and was
going to take hours.  The measurements are unchanged; only the arithmetic moves
into numpy.  Anchors asserted unique.
"""
import io

P = 'tools/audioscan.py'
s = io.open(P, encoding='utf-8').read()

old = '''def stats(buf, acc):
    """Accumulate peak/RMS/silence over one block of stereo 16-bit LE samples."""
    n = len(buf) // 4
    for i in range(0, len(buf), 4):
        l, r = struct.unpack_from('<hh', buf, i)
        if l or r:
            acc['nonzero'] += 1
        acc['peakL'] = max(acc['peakL'], abs(l))
        acc['peakR'] = max(acc['peakR'], abs(r))
        acc['sumL'] += l * l
        acc['sumR'] += r * r
    acc['samples'] += n'''

new = '''def stats(buf, acc):
    """Accumulate peak/RMS/silence over one block of stereo 16-bit LE samples."""
    a = np.frombuffer(buf, dtype='<i2')
    if a.size % 2:
        a = a[:a.size - 1]
    a = a.reshape(-1, 2).astype(np.int64)
    L, R = a[:, 0], a[:, 1]
    acc['nonzero'] += int(np.count_nonzero(L | R))
    acc['peakL'] = max(acc['peakL'], int(np.abs(L).max(initial=0)))
    acc['peakR'] = max(acc['peakR'], int(np.abs(R).max(initial=0)))
    acc['sumL'] += int((L * L).sum())
    acc['sumR'] += int((R * R).sum())
    acc['samples'] += int(a.shape[0])'''

assert s.count(old) == 1, "stats() anchor not unique"
s = s.replace(old, new, 1)

old2 = "import sys, hashlib, struct, json, os"
new2 = "import sys, hashlib, struct, json, os\nimport numpy as np"
assert s.count(old2) == 1, "import anchor not unique"
s = s.replace(old2, new2, 1)

# per-sector silence test, vectorised the same way
old3 = """            for j in range(k):
                s = blk[j * RAW:(j + 1) * RAW]
                if s == bytes(RAW):
                    run_silent += 1
                    if not seen_sound and lead_silent is None:
                        pass
                else:
                    if not seen_sound:
                        lead_silent = p + j - lba
                        seen_sound = True
                    run_silent = 0"""
new3 = """            m = np.frombuffer(blk, dtype=np.uint8).reshape(k, RAW).any(axis=1)
            for j in range(k):
                if not m[j]:
                    run_silent += 1
                else:
                    if not seen_sound:
                        lead_silent = p + j - lba
                        seen_sound = True
                    run_silent = 0"""
assert s.count(old3) == 1, "silence loop anchor not unique"
s = s.replace(old3, new3, 1)

# progress line once per track-chunk group, not every 26 sectors
old4 = """            sys.stderr.write("  track %d: %d/%d sectors\\r" % (num, p - lba, n))"""
new4 = """            if (p - lba) % 2600 < CH:
                sys.stderr.write("  track %d: %d/%d sectors\\r" % (num, p - lba, n))"""
assert s.count(old4) == 1, "progress anchor not unique"
s = s.replace(old4, new4, 1)

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print("patched %s" % P)
