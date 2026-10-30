#!/usr/bin/env python3
"""Find PowerPacker streams *inside* files, and print windowed entropy.

Two things the platform notes ask for that a file-level census cannot do:

1.  A container census over files misses compression held inside an
    executable or inside another container.  This scans every offset for a
    `PP20` magic whose four following bytes are a plausible offset-length
    table and whose trailing length field is consistent with the bytes that
    remain, then tries to decrunch it.

2.  Whole-file Shannon entropy misses a packed blob that is a minority of a
    large file.  `--window` prints the entropy of each N-byte window so the
    packed regions show up as a plateau above 7.5 bits/byte even when the
    file average is far below it.

    python3 tools/ppscan.py FILE [FILE ...] [--window 4096] [--extract DIR]
"""
import sys, os, math, argparse, importlib.util

_here = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("pp20mod", os.path.join(_here, "pp20.py"))


def _load_pp20():
    """pp20.py runs main() at import, so load its functions by exec with argv
    neutralised."""
    src = open(os.path.join(_here, "pp20.py"), encoding='utf-8').read()
    src = src.replace("\nmain()\n", "\n")
    ns = {'__name__': 'pp20'}
    exec(compile(src, 'pp20.py', 'exec'), ns)
    return ns


pp = _load_pp20()


def entropy(b):
    if not b:
        return 0.0
    c = [0] * 256
    for x in b:
        c[x] += 1
    n = float(len(b))
    return -sum((k / n) * math.log(k / n, 2) for k in c if k)


def scan(path, window, extract):
    d = open(path, 'rb').read()
    rel = os.path.basename(path)
    hits = []
    o = 0
    while True:
        o = d.find(b'PP20', o)
        if o < 0:
            break
        tab = list(d[o + 4:o + 8])
        if all(1 <= t <= 32 for t in tab) and sorted(tab) == tab:
            # try every plausible end: the stream's own trailing longword must
            # give a length we can actually decrunch
            for end in range(o + 12, len(d) + 1, 2):
                blob = d[o:end]
                try:
                    u = pp['unpack'](blob)
                except Exception:
                    continue
                hits.append((o, end - o, len(u), tab))
                if extract:
                    q = os.path.join(extract, "%s@0x%06x.bin" % (rel, o))
                    os.makedirs(extract, exist_ok=True)
                    open(q, 'wb').write(u)
                break
        o += 4
    print("### %s  (%d bytes, whole-file entropy %.3f b/B)"
          % (path, len(d), entropy(d)))
    if hits:
        for off, plen, ulen, tab in hits:
            print("    PP20 at 0x%06x  packed %7d -> %7d  olens=%s" % (off, plen, ulen, tab))
    else:
        print("    no decodable PP20 stream inside")
    if window:
        hi = [(i, entropy(d[i:i + window]))
              for i in range(0, len(d), window)]
        over = [x for x in hi if x[1] > 7.5]
        print("    windowed entropy, %d windows of %d bytes: %d above 7.5 b/B (%.1f %%), max %.3f"
              % (len(hi), window, len(over), 100.0 * len(over) / len(hi),
                 max(x[1] for x in hi)))
        if over:
            runs, s, p = [], over[0][0], over[0][0]
            for i, _ in over[1:]:
                if i == p + window:
                    p = i
                else:
                    runs.append((s, p + window)); s = p = i
            runs.append((s, p + window))
            for a, b in runs:
                print("        high-entropy run 0x%06x..0x%06x  (%d bytes)" % (a, b, b - a))
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--window", type=int, default=4096)
    ap.add_argument("--extract")
    a = ap.parse_args()
    for p in a.files:
        scan(p, a.window, a.extract)


main()
