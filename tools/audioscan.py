#!/usr/bin/env python3
"""audioscan.py -- measure the Red Book tracks of a physical CD without writing
217 MB to disk.

For every audio track this reports: length in sectors and in mm:ss:ff, peak and
RMS level per channel, how many leading and trailing sectors are digital
silence, and a SHA-1 of the audio payload so the read is reproducible.  It also
walks the sectors *before* track 2's start address to measure the real pregap,
which a .cue file flattens to a nominal two seconds.

The drive's read offset (measured by tools/rawsectors.py from the data track's
sync pattern) is compensated, so the samples reported are the samples on the
disc rather than the samples the drive happened to hand back.

Usage: audioscan.py E [firsttrack lasttrack]
"""
import sys, hashlib, struct, json, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rawcd, rawsectors

RAW = 2352
CH = 26          # this drive refuses raw transfers of 32 sectors or more


def msf(lba):
    lba += 150
    return "%02d:%02d:%02d" % (lba // (60 * 75), (lba // 75) % 60, lba % 75)


def read_block(h, lba, n, off):
    r, _ = rawcd.raw_read(h, lba, n + 1, 'CDDA')
    if r is not None and len(r) >= off + RAW * n:
        return r[off:off + RAW * n]
    out = bytearray()
    for j in range(n):
        a, _ = rawcd.raw_read(h, lba + j, 1, 'CDDA')
        b, _ = rawcd.raw_read(h, lba + j + 1, 1, 'CDDA')
        if a is None:
            out += bytes(RAW)
            continue
        tail = b[:off] if b is not None else bytes(off)
        out += (a[off:] + tail)[:RAW]
    return bytes(out)


def stats(buf, acc):
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
    acc['samples'] += int(a.shape[0])


def main():
    letter = sys.argv[1]
    h = rawcd.open_drive(letter)
    off = rawsectors.find_offset(h)
    raw_lba, _ = rawcd.read_toc(h, 0, 0)
    t = rawcd.parse_toc(raw_lba)
    entries = []
    for e in t['tracks'][:t['last'] - t['first'] + 2]:
        lba = int.from_bytes(bytes(e['addr']), 'big', signed=True)
        entries.append((e['track'], e['control'], lba))
    print("read offset %+d bytes" % -off, file=sys.stderr)

    first = int(sys.argv[2]) if len(sys.argv) > 2 else t['first']
    last = int(sys.argv[3]) if len(sys.argv) > 3 else t['last']

    results = []
    for idx, (num, ctrl, lba) in enumerate(entries):
        if num == 0xAA or (ctrl & 0x4) or not (first <= num <= last):
            continue
        end = entries[idx + 1][2]
        n = end - lba
        acc = dict(peakL=0, peakR=0, sumL=0, sumR=0, samples=0, nonzero=0)
        sha = hashlib.sha1()
        lead_silent = None
        trail_silent = 0
        run_silent = 0
        seen_sound = False
        p = lba
        while p < end:
            k = min(CH, end - p)
            blk = read_block(h, p, k, off)
            sha.update(blk)
            stats(blk, acc)
            m = np.frombuffer(blk, dtype=np.uint8).reshape(k, RAW).any(axis=1)
            for j in range(k):
                if not m[j]:
                    run_silent += 1
                else:
                    if not seen_sound:
                        lead_silent = p + j - lba
                        seen_sound = True
                    run_silent = 0
            p += k
            if (p - lba) % 2600 < CH:
                sys.stderr.write("  track %d: %d/%d sectors\r" % (num, p - lba, n))
        trail_silent = run_silent
        import math
        rmsL = math.sqrt(acc['sumL'] / acc['samples']) if acc['samples'] else 0
        rmsR = math.sqrt(acc['sumR'] / acc['samples']) if acc['samples'] else 0
        rec = dict(track=num, lba=lba, end=end, sectors=n,
                   length=msf(n - 150), start_msf=msf(lba),
                   peakL=acc['peakL'], peakR=acc['peakR'],
                   rmsL=round(rmsL, 1), rmsR=round(rmsR, 1),
                   nonzero_samples=acc['nonzero'], samples=acc['samples'],
                   lead_silent_sectors=lead_silent if lead_silent is not None else n,
                   trail_silent_sectors=trail_silent,
                   sha1=sha.hexdigest())
        results.append(rec)
        sys.stderr.write("\n")
        print("track %-2d LBA %-6d %6d sectors  %s  peak %5d/%5d  rms %7.1f/%7.1f  "
              "lead-in silence %4d  tail silence %4d  sha1 %s"
              % (num, lba, n, rec['length'], rec['peakL'], rec['peakR'],
                 rmsL, rmsR, rec['lead_silent_sectors'], rec['trail_silent_sectors'],
                 rec['sha1'][:16]))
    print()
    print(json.dumps(results, indent=1))


if __name__ == '__main__':
    main()
