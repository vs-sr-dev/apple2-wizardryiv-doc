#!/usr/bin/env python3
"""Audio-track geometry for a CUE whose tracks are separate WAV files.

The version inherited from cd32-universe-doc assumes one BIN with byte offsets.
This disc has one WAV per track, and three of the five declare INDEX 00 and
INDEX 01 one frame apart *inside the file* -- a one-frame pregap that no other
cue in the set shows.  The point of this tool is to test whether that frame is
anything: it measures the leading silence of every track in frames, so the
declared pregap can be compared with the measured one.

Usage: python3 tools/cueaudio.py <cue>
"""
import sys, os, re, struct, hashlib

FRAME = 2352  # bytes of Red Book audio per sector


def wav_data(path):
    b = open(path, "rb").read()
    assert b[:4] == b"RIFF" and b[8:12] == b"WAVE", path
    o = 12
    fmt = None
    while o + 8 <= len(b):
        cid = b[o:o + 4]
        sz = struct.unpack_from("<I", b, o + 4)[0]
        if cid == b"fmt ":
            fmt = struct.unpack_from("<HHIIHH", b, o + 8)
        if cid == b"data":
            return fmt, b[o + 8:o + 8 + sz]
        o += 8 + sz + (sz & 1)
    raise ValueError("no data chunk")


def lead_zero_frames(d):
    i = 0
    n = len(d)
    while i < n and d[i] == 0:
        i += 1
    return i, i // FRAME


def msf(frames):
    return "%d:%02d.%02d" % (frames // 4500, (frames // 75) % 60, frames % 75)


def main():
    cue = sys.argv[1]
    base = os.path.dirname(os.path.abspath(cue))
    text = open(cue, "r", errors="replace").read()
    entries = []
    cur = None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r'FILE "(.+)" (\w+)', s)
        if m:
            cur = dict(file=m.group(1), fmt=m.group(2), idx={}, pregap=None, num=None, type=None)
            entries.append(cur)
        m = re.match(r"TRACK (\d+) (\S+)", s)
        if m and cur:
            cur["num"] = int(m.group(1)); cur["type"] = m.group(2)
        m = re.match(r"INDEX (\d+) (\d+):(\d+):(\d+)", s)
        if m and cur:
            cur["idx"][int(m.group(1))] = (int(m.group(2)) * 60 + int(m.group(3))) * 75 + int(m.group(4))
        m = re.match(r"PREGAP (\d+):(\d+):(\d+)", s)
        if m and cur:
            cur["pregap"] = (int(m.group(1)) * 60 + int(m.group(2))) * 75 + int(m.group(3))

    print("%-3s %-10s %11s %8s %9s  %-7s %-7s %-9s %s"
          % ("tr", "type", "bytes", "frames", "time", "IDX00", "IDX01", "silent", "sha1"))
    tot = 0
    for e in entries:
        p = os.path.join(base, e["file"])
        if e["type"] != "AUDIO":
            sz = os.path.getsize(p)
            print("%-3d %-10s %11d %8d %9s  %-7s %-7s %-9s %s"
                  % (e["num"], "DATA", sz, sz // 2048, "-", "-", "-", "-",
                     hashlib.sha1(open(p, "rb").read()).hexdigest()[:12]))
            continue
        fmt, d = wav_data(p)
        fr = len(d) // FRAME
        rem = len(d) % FRAME
        zb, zf = lead_zero_frames(d)
        tot += fr
        print("%-3d %-10s %11d %8d %9s  %-7s %-7s %d B/%df  %s"
              % (e["num"], "%dHz/%dch/%db" % (fmt[2], fmt[1], fmt[5]),
                 len(d), fr, msf(fr),
                 "-" if 0 not in e["idx"] else msf(e["idx"][0]),
                 "-" if 1 not in e["idx"] else msf(e["idx"][1]),
                 zb, zf, hashlib.sha1(d).hexdigest()[:12]))
        if rem:
            print("      ! %d trailing bytes are not a whole frame" % rem)
    print()
    print("audio frames total %d  (%s)" % (tot, msf(tot)))


if __name__ == "__main__":
    main()
