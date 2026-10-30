#!/usr/bin/env python3
"""Read an 880 KiB Amiga floppy image: bootblock, checksum, OFS/FFS tree, bitmap.

Also reports, for a non-DOS image, how much of the 1,760 blocks is non-zero and
where the used regions are — which is the only census available when there is no
file system to walk.

Usage: python3 tools/adf.py <image> [--tree] [--extract DIR] [--map]
"""
import sys, os, struct, hashlib, argparse

BS = 512
NBLK = 1760


def be32(b, o):
    return int.from_bytes(b[o:o + 4], 'big')


def bootsum(b):
    """Amiga bootblock checksum over the first 1024 bytes, field at offset 4."""
    s = 0
    for i in range(0, 1024, 4):
        v = be32(b, i) if i != 4 else 0
        s += v
        if s > 0xFFFFFFFF:
            s = (s & 0xFFFFFFFF) + 1
    return (~s) & 0xFFFFFFFF


def blocksum(b):
    """Standard Amiga block checksum: sum of longwords is zero, field at 20."""
    s = 0
    for i in range(0, BS, 4):
        s = (s + be32(b, i)) & 0xFFFFFFFF
    return s


def bstr(b, o):
    n = b[o]
    return b[o + 1:o + 1 + n].decode('latin-1')


def ts(b, o):
    days, mins, ticks = be32(b, o), be32(b, o + 4), be32(b, o + 8)
    import datetime
    try:
        d = datetime.date(1978, 1, 1) + datetime.timedelta(days=days)
    except Exception:
        return "days=%d mins=%d ticks=%d" % (days, mins, ticks)
    return "%s %02d:%02d:%05.2f" % (d, mins // 60, mins % 60, ticks / 50.0)


class Adf(object):
    def __init__(self, path):
        self.d = open(path, 'rb').read()
        self.path = path
        self.n = len(self.d) // BS

    def blk(self, i):
        return self.d[i * BS:(i + 1) * BS]

    def boot(self):
        b = self.blk(0) + self.blk(1)
        return {
            'type': b[0:4],
            'checksum_stored': be32(b, 4),
            'checksum_calc': bootsum(b),
            'rootblock': be32(b, 8),
        }

    def walk(self, root=880):
        """Walk an OFS/FFS hash tree from the root block. Returns list of entries."""
        out = []
        rb = self.blk(root)
        if be32(rb, 0) != 2 or be32(rb, BS - 4) != 1:
            return None
        ht_size = be32(rb, 12)
        self._dir(root, "", out, ht_size, set())
        return out

    def _dir(self, blk, prefix, out, ht_size, seen):
        if blk in seen:
            return
        seen.add(blk)
        b = self.blk(blk)
        for i in range(ht_size):
            e = be32(b, 24 + 4 * i)
            while e:
                if e in seen or e >= self.n:
                    break
                eb = self.blk(e)
                sec = be32(eb, BS - 4)
                name = bstr(eb, BS - 80)
                if sec == 2:  # directory
                    out.append(('dir', prefix + name, 0, e, ts(eb, BS - 92)))
                    self._dir(e, prefix + name + "/", out, ht_size, seen)
                elif sec == 0xFFFFFFFD:  # file header
                    out.append(('file', prefix + name, be32(eb, BS - 188), e,
                                ts(eb, BS - 92)))
                    seen.add(e)
                else:
                    out.append(('?%d' % sec, prefix + name, 0, e, ''))
                    seen.add(e)
                e = be32(eb, BS - 16)  # hash chain

    def filedata(self, hdr, ffs=False):
        """Read a file's data following the extension-block chain."""
        b = self.blk(hdr)
        size = be32(b, BS - 188)
        out = bytearray()
        cur = hdr
        while cur:
            cb = self.blk(cur)
            hi = be32(cb, 8)  # high_seq
            for i in range(hi):
                dp = be32(cb, BS - 204 - 4 * i)
                if dp == 0 or dp >= self.n:
                    continue
                db = self.blk(dp)
                if ffs:
                    out += db
                else:
                    n = be32(db, 12)
                    out += db[24:24 + n]
            cur = be32(cb, BS - 8)  # extension
        return bytes(out[:size])

    def nonzero_map(self):
        """Blocks that are not all zero, collapsed into runs."""
        nz = [i for i in range(self.n) if self.d[i * BS:(i + 1) * BS].strip(b'\0')]
        runs = []
        for i in nz:
            if runs and runs[-1][1] == i - 1:
                runs[-1][1] = i
            else:
                runs.append([i, i])
        return nz, runs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('image')
    ap.add_argument('--tree', action='store_true')
    ap.add_argument('--map', action='store_true')
    ap.add_argument('--extract')
    a = ap.parse_args()
    f = Adf(a.image)
    bt = f.boot()
    print("%s  %d bytes  %d blocks" % (os.path.basename(a.image), len(f.d), f.n))
    print("  bootblock type     %r" % bt['type'])
    print("  checksum stored    0x%08X" % bt['checksum_stored'])
    print("  checksum computed  0x%08X   %s" % (
        bt['checksum_calc'],
        "VALID" if bt['checksum_stored'] == bt['checksum_calc'] else "MISMATCH"))
    print("  root block field   %d" % bt['rootblock'])

    nz, runs = f.nonzero_map()
    print("  non-zero blocks    %d of %d (%.2f%%) = %d B" % (
        len(nz), f.n, 100.0 * len(nz) / f.n, len(nz) * BS))
    if a.map:
        for r in runs:
            print("    blocks %5d..%-5d  %5d  (%d B)" % (r[0], r[1], r[1] - r[0] + 1,
                                                         (r[1] - r[0] + 1) * BS))
        print("    %d runs" % len(runs))

    if bt['type'][:3] == b'DOS':
        ffs = bool(bt['type'][3] & 1)
        print("  filesystem         %s" % ("FFS" if ffs else "OFS"))
        rb = f.blk(880)
        print("  root block name    %r  %s" % (bstr(rb, BS - 80), ts(rb, BS - 92)))
        ents = f.walk(880)
        if ents is None:
            print("  root block         NOT a valid root block")
            return
        print("  entries            %d" % len(ents))
        if a.tree or a.extract:
            for kind, name, size, blk, t in sorted(ents, key=lambda e: e[1]):
                print("    %-5s %-30s %8s  blk %5d  %s" % (
                    kind, name, size if kind == 'file' else '', blk, t))
                if a.extract and kind == 'file':
                    d = f.filedata(blk, ffs)
                    p = os.path.join(a.extract, name.replace('/', os.sep))
                    os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
                    open(p, 'wb').write(d)
                    print("          -> %d B  sha1 %s" % (len(d), hashlib.sha1(d).hexdigest()))


if __name__ == '__main__':
    main()
