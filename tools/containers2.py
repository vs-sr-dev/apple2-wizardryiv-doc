#!/usr/bin/env python3
"""Container walk that accepts RNC method 1 *and* method 2.

The version inherited from cd32-universe-doc calls `rnc.unpack` only, which is
the method-1 bit stream.  Gunship 2000 packs with method 2 exclusively, so the
inherited tool reports zero streams on a disc that has 542 of them.  Same
validation rule: a candidate is accepted only when the decoder consumes exactly
the declared packed length and produces exactly the declared unpacked length,
which cannot produce a false positive.

Usage:
    python3 tools/containers2.py <dir-or-file> [--out DIR] [--json FILE]
"""
import sys, os, json, argparse, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rnc
import rnc2

HDR = 18


def try_unpack(chunk, method):
    for mod in (rnc, rnc2):
        try:
            d = mod.unpack(chunk)
            if d is not None:
                return d
        except Exception:
            pass
    return None


def streams(blob):
    """Every validated RNC stream in blob, as (offset, packed, method, data)."""
    out = []
    off = 0
    n = len(blob)
    while off < n - HDR:
        if blob[off:off + 3] == b'RNC' and blob[off + 3] in (1, 2):
            m = blob[off + 3]
            ulen = int.from_bytes(blob[off + 4:off + 8], 'big')
            plen = int.from_bytes(blob[off + 8:off + 12], 'big')
            if 0 < plen and 0 < ulen < (32 << 20) and off + HDR + plen <= n:
                data = try_unpack(blob[off:off + HDR + plen], m)
                if data is not None and len(data) == ulen:
                    out.append((off, HDR + plen, m, data))
                    off += HDR + plen
                    continue
        off += 1
    return out


def walk(blob, name, depth, rows, outdir):
    ss = streams(blob)
    cur = 0
    for off, packed, m, data in ss:
        if off > cur:
            rows.append(dict(name=name, depth=depth, kind="gap", off=cur,
                             length=off - cur, sha1=hashlib.sha1(blob[cur:off]).hexdigest()[:12],
                             zero=not any(blob[cur:off])))
            if outdir:
                open(os.path.join(outdir, "%s.gap%06d.bin" % (name, cur)), "wb").write(blob[cur:off])
        stem = "%s.%06d" % (name, off)
        rows.append(dict(name=name, depth=depth, kind="RNC%d" % m, off=off,
                         packed=packed, length=len(data),
                         sha1=hashlib.sha1(data).hexdigest()[:12]))
        if outdir:
            open(os.path.join(outdir, stem + ".bin"), "wb").write(data)
        sub = os.path.join(outdir, stem + ".d") if outdir else None
        if sub:
            os.makedirs(sub, exist_ok=True)
        n0 = len(rows)
        walk(data, stem, depth + 1, rows, sub)
        if sub and len(rows) == n0:
            os.rmdir(sub)
        cur = off + packed
    if ss and cur < len(blob):
        rows.append(dict(name=name, depth=depth, kind="gap", off=cur,
                         length=len(blob) - cur,
                         sha1=hashlib.sha1(blob[cur:]).hexdigest()[:12],
                         zero=not any(blob[cur:])))
        if outdir:
            open(os.path.join(outdir, "%s.gap%06d.bin" % (name, cur)), "wb").write(blob[cur:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out")
    ap.add_argument("--json")
    a = ap.parse_args()

    files = []
    if os.path.isdir(a.src):
        for r, _d, fs in os.walk(a.src):
            for f in sorted(fs):
                files.append(os.path.join(r, f))
    else:
        files = [a.src]

    allrows = []
    for p in files:
        blob = open(p, "rb").read()
        name = os.path.basename(p)
        outdir = None
        rows = []
        if a.out:
            outdir = os.path.join(a.out, name)
            os.makedirs(outdir, exist_ok=True)
        walk(blob, name, 0, rows, outdir)
        if not rows and outdir:
            os.rmdir(outdir)
        if rows:
            print("=== %s (%d bytes) ===" % (name, len(blob)))
            bydepth = {}
            for r in rows:
                if r["kind"] != "gap":
                    bydepth.setdefault(r["depth"], [0, 0, 0])
                    bydepth[r["depth"]][0] += 1
                    bydepth[r["depth"]][1] += r["packed"]
                    bydepth[r["depth"]][2] += r["length"]
            for d in sorted(bydepth):
                c, pk, un = bydepth[d]
                print("  depth %d: %4d streams, %9d packed -> %9d unpacked" % (d, c, pk, un))
            gaps = [r for r in rows if r["kind"] == "gap"]
            gz = [r for r in gaps if r.get("zero")]
            print("  gaps   : %4d, %d bytes (%d all-zero, %d bytes)"
                  % (len(gaps), sum(r["length"] for r in gaps),
                     len(gz), sum(r["length"] for r in gz)))
        allrows += rows
    if a.json:
        json.dump(allrows, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
