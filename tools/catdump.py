#!/usr/bin/env python3
"""Parse the Gunship 2000 `.cat` / `.dat` resource archives.

Format, recovered from the bytes (nothing on the disc declares it):

    u16            entry count N
    N x 24 bytes   16-byte name, NUL padded
                   u32 length
                   u32 offset, absolute from the start of the file
    ...            the payload, starting at 2 + 24*N

The first entry's offset equals 2 + 24*N exactly on all six archives, which is
what confirms the entry stride and that offsets are file-absolute rather than
payload-relative.

Usage:
    python3 tools/catdump.py <file> [--extract DIR] [--verify-loose ISODIR]
"""
import sys, os, struct, argparse, hashlib, collections


def parse(d):
    n = struct.unpack_from(">H", d, 0)[0]
    ents = []
    o = 2
    for i in range(n):
        name = d[o:o + 16].split(b"\x00")[0].decode("latin-1")
        ln, off = struct.unpack_from(">II", d, o + 16)
        ents.append((name, ln, off))
        o += 24
    return n, ents, o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--extract")
    ap.add_argument("--verify-loose")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    d = open(a.file, "rb").read()
    n, ents, tbl_end = parse(d)
    print("=== %s : %d bytes ===" % (os.path.basename(a.file), len(d)))
    print("entries %d, table 2..%d, first payload offset %d (table end %s)"
          % (n, tbl_end, ents[0][2] if ents else -1,
             "matches" if ents and ents[0][2] == tbl_end else "MISMATCH"))

    ext = collections.Counter()
    covered = 0
    prev_end = tbl_end
    gaps = []
    dup = collections.Counter()
    if not a.quiet:
        print()
        print("%-4s %-16s %9s %9s %-9s %s" % ("#", "name", "length", "offset", "ext", "sha1"))
    for i, (name, ln, off) in enumerate(ents):
        blob = d[off:off + ln]
        sha = hashlib.sha1(blob).hexdigest()
        dup[sha] += 1
        ext[name.rsplit(".", 1)[-1].upper() if "." in name else "(none)"] += 1
        covered += ln
        if off > prev_end:
            gaps.append((prev_end, off - prev_end))
        prev_end = max(prev_end, off + ln)
        if not a.quiet:
            print("%-4d %-16s %9d %9d %-9s %s"
                  % (i, name, ln, off,
                     name.rsplit(".", 1)[-1].upper() if "." in name else "-", sha[:16]))
        if a.extract:
            os.makedirs(a.extract, exist_ok=True)
            open(os.path.join(a.extract, name), "wb").write(blob)

    print()
    print("payload %d bytes, entries cover %d (%.1f%%), table %d, trailing %d"
          % (len(d) - tbl_end, covered, 100.0 * covered / max(1, len(d) - tbl_end),
             tbl_end, len(d) - prev_end))
    print("gaps between entries: %d (%d bytes)" % (len(gaps), sum(g[1] for g in gaps)))
    for g in gaps[:20]:
        print("   gap at %d, %d bytes" % g)
    print("extensions: %s" % ", ".join("%s x%d" % kv for kv in ext.most_common()))
    rep = [k for k, v in dup.items() if v > 1]
    if rep:
        print("duplicate payloads (same SHA-1): %d group(s)" % len(rep))

    if a.verify_loose:
        print()
        print("=== entries that also exist as loose files on the disc ===")
        same = diff = miss = 0
        for name, ln, off in ents:
            p = os.path.join(a.verify_loose, name)
            if not os.path.exists(p):
                miss += 1
                continue
            loose = open(p, "rb").read()
            inner = d[off:off + ln]
            if loose == inner:
                same += 1
            else:
                diff += 1
                print("   %-16s loose %d vs archived %d  %s"
                      % (name, len(loose), len(inner),
                         "archived is loose+%d" % (len(inner) - len(loose))
                         if inner[:len(loose)] == loose else "content differs"))
        print("   identical %d, different %d, not present loose %d" % (same, diff, miss))


if __name__ == "__main__":
    main()
