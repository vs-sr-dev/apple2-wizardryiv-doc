#!/usr/bin/env python3
"""Parse the ISO 9660 volume of the Banshee data track.

Prints the primary volume descriptor field by field, follows the CDTV
trademark pointer, walks the directory tree, and builds a sector map of
every claimed and unclaimed run inside the declared volume.

Usage:  python3 tools/isodump.py <track1.iso> [--extract DIR] [--json FILE]
"""
import sys, os, json, hashlib, argparse

SEC = 2048
NUL = chr(0)


def u16le(b, o):
    return int.from_bytes(b[o:o + 2], 'little')


def u32le(b, o):
    return int.from_bytes(b[o:o + 4], 'little')


def u32be(b, o):
    return int.from_bytes(b[o:o + 4], 'big')


def dirdate(b, o):
    y, mo, d, h, mi, s, tz = b[o], b[o + 1], b[o + 2], b[o + 3], b[o + 4], b[o + 5], b[o + 6]
    if y == 0 and mo == 0:
        return None
    off = tz - 256 if tz > 127 else tz
    return "%04d-%02d-%02d %02d:%02d:%02d %+d" % (1900 + y, mo, d, h, mi, s, off)


def strdate(b, o):
    s = b[o:o + 16].decode('latin-1')
    if s.strip("0 " + NUL) == "":
        return None
    return "%s-%s-%s %s:%s:%s.%s %+d" % (s[0:4], s[4:6], s[6:8], s[8:10],
                                         s[10:12], s[12:14], s[14:16], b[o + 16])


def field(b, o, n):
    return b[o:o + n].decode('latin-1')


class Iso(object):
    def __init__(self, path):
        self.path = path
        self.f = open(path, 'rb')
        self.size = os.path.getsize(path)
        self.sectors = self.size // SEC
        self.pvd = self.sector(16)

    def sector(self, lba, n=1):
        self.f.seek(lba * SEC)
        return self.f.read(n * SEC)

    def read(self, lba, length):
        self.f.seek(lba * SEC)
        return self.f.read(length)

    def pvd_report(self):
        p = self.pvd
        out = []
        A = out.append
        A("image bytes            %d (%d sectors of %d)" % (self.size, self.sectors, SEC))
        A("descriptor type        %d" % p[0])
        A("standard identifier    %r" % field(p, 1, 5))
        A("version                %d" % p[6])
        A("system identifier      %r" % field(p, 8, 32))
        A("volume identifier      %r" % field(p, 40, 32))
        A("volume space size      %d sectors (LE) / %d (BE)" % (u32le(p, 80), u32be(p, 84)))
        A("volume set size        %d" % u16le(p, 120))
        A("volume sequence        %d" % u16le(p, 124))
        A("logical block size     %d" % u16le(p, 128))
        A("path table size        %d" % u32le(p, 132))
        A("L path table           %d" % u32le(p, 140))
        A("L path table optional  %d" % u32le(p, 144))
        A("M path table           %d" % u32be(p, 148))
        A("M path table optional  %d" % u32be(p, 152))
        A("root dir extent        %d, %d bytes" % (u32le(p, 156 + 2), u32le(p, 156 + 10)))
        A("root dir date          %s" % dirdate(p, 156 + 18))
        A("volume set identifier  %r" % field(p, 190, 128))
        A("publisher identifier   %r" % field(p, 318, 128))
        A("data preparer          %r" % field(p, 446, 128))
        A("application identifier %r" % field(p, 574, 128))
        A("copyright file         %r" % field(p, 702, 37))
        A("abstract file          %r" % field(p, 739, 37))
        A("bibliographic file     %r" % field(p, 776, 37))
        A("creation date          %s" % strdate(p, 813))
        A("modification date      %s" % strdate(p, 830))
        A("expiration date        %s" % strdate(p, 847))
        A("effective date         %s" % strdate(p, 864))
        A("file structure version %d" % p[881])
        return "\n".join(out)

    def padding_report(self):
        p = self.pvd
        names = [("system identifier", 8, 32), ("volume identifier", 40, 32),
                 ("volume set identifier", 190, 128), ("publisher", 318, 128),
                 ("data preparer", 446, 128), ("application identifier", 574, 128)]
        out = []
        for n, o, ln in names:
            raw = p[o:o + ln]
            body = raw.rstrip(b"\x00").rstrip(b" ")
            tail = raw[len(body):]
            if not body:
                kind = "empty(%s)" % ("NUL" if raw[:1] == b"\x00" else "space")
            elif tail[:1] == b"\x00":
                kind = "NUL"
            elif tail[:1] == b" ":
                kind = "space"
            else:
                kind = "flush"
            out.append("%-24s %-12s value=%r" % (n, kind, body.decode('latin-1')))
        return "\n".join(out)

    def tm_pointer(self):
        p = self.pvd
        area = p[883:1395]
        i = area.find(b'TM')
        if i < 0:
            return None
        base = 883 + i
        return {"tag_offset": base,
                "constant": int.from_bytes(p[base + 2:base + 4], 'big'),
                "length": u32be(p, base + 4),
                "lba": u32be(p, base + 8),
                "fs_record": p[884:888] == b'FS\x00\x00'}

    def walk(self):
        p = self.pvd
        root_lba = u32le(p, 156 + 2)
        root_len = u32le(p, 156 + 10)
        todo = [("", root_lba, root_len)]
        seen = set()
        files = []
        dirs = []
        while todo:
            path, lba, ln = todo.pop(0)
            if (lba, ln) in seen:
                continue
            seen.add((lba, ln))
            dirs.append({"path": path or "/", "lba": lba, "size": ln})
            data = self.read(lba, ln)
            o = 0
            while o < len(data):
                rl = data[o]
                if rl == 0:
                    o = (o // SEC + 1) * SEC
                    continue
                rec = data[o:o + rl]
                ext = u32le(rec, 2)
                sz = u32le(rec, 10)
                dt = dirdate(rec, 18)
                flags = rec[25]
                nlen = rec[32]
                raw = rec[33:33 + nlen].decode('latin-1')
                if nlen == 1 and rec[33] in (0, 1):
                    pass
                else:
                    nm = raw.split(';')[0]
                    entry = {"path": path + "/" + nm, "name": nm, "lba": ext,
                             "size": sz, "date": dt, "flags": flags,
                             "reclen": rl, "raw_name": raw}
                    if flags & 2:
                        todo.append((path + "/" + nm, ext, sz))
                        entry["dirdate"] = dt
                    else:
                        files.append(entry)
                    if flags & 2:
                        dirs_dates.append(entry)
                o += rl
        return dirs, files

    def sha1(self, lba, size):
        return hashlib.sha1(self.read(lba, size)).hexdigest()


dirs_dates = []


def sector_map(iso, dirs, files):
    declared = u32le(iso.pvd, 80)
    claimed = {}

    def claim(lba, size, what):
        n = max(1, (size + SEC - 1) // SEC)
        for s in range(lba, lba + n):
            claimed.setdefault(s, what)

    for s in range(0, 16):
        claim(s, SEC, "system area")
    claim(16, SEC, "PVD")
    claim(17, SEC, "PVD copy")
    claim(18, SEC, "terminator")
    claim(u32le(iso.pvd, 140), u32le(iso.pvd, 132), "L path table")
    claim(u32be(iso.pvd, 148), u32le(iso.pvd, 132), "M path table")
    tm = iso.tm_pointer()
    if tm:
        claim(tm["lba"], tm["length"], ".TM block")
    for d in dirs:
        claim(d["lba"], d["size"], "dir " + d["path"])
    for f in files:
        claim(f["lba"], f["size"], f["path"])
    runs = []
    cur = None
    for s in range(declared):
        w = claimed.get(s)
        if cur and cur[2] == w:
            cur[1] = s
        else:
            if cur:
                runs.append(cur)
            cur = [s, s, w]
    if cur:
        runs.append(cur)
    return declared, runs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("iso")
    ap.add_argument("--extract")
    ap.add_argument("--json")
    a = ap.parse_args()
    iso = Iso(a.iso)
    print("=== PRIMARY VOLUME DESCRIPTOR ===")
    print(iso.pvd_report())
    print()
    print("=== STRING FIELD PADDING ===")
    print(iso.padding_report())
    print()
    print("=== DESCRIPTOR SECTORS ===")
    print("sector 17 == sector 16:", iso.sector(17) == iso.sector(16))
    print("sector 18 type %d id %r" % (iso.sector(18)[0], field(iso.sector(18), 1, 5)))
    print()
    print("=== .TM POINTER ===")
    tm = iso.tm_pointer()
    print(tm)
    if tm:
        blk = iso.read(tm["lba"], tm["length"])
        print("whole block          sha1 %s" % hashlib.sha1(blk).hexdigest())
        print("banner 0x000..0x44C  sha1 %s" % hashlib.sha1(blk[:0x44C]).hexdigest())
        print("object 0x44C..0x7B8  sha1 %s" % hashlib.sha1(blk[0x44C:0x7B8]).hexdigest())
    print()
    dirs, files = iso.walk()
    print("=== DIRECTORIES (%d) ===" % len(dirs))
    for d in dirs:
        print("  %-24s lba %6d  %6d bytes" % (d["path"], d["lba"], d["size"]))
    print()
    print("=== DIRECTORY RECORDS FOR DIRECTORIES ===")
    for e in dirs_dates:
        print("  %-24s %s" % (e["path"], e["date"]))
    print()
    print("=== FILES (%d) ===" % len(files))
    for f in sorted(files, key=lambda x: x["lba"]):
        print("  %6d %9d  %-24s %s" % (f["lba"], f["size"], f["date"], f["path"]))
    print()
    declared, runs = sector_map(iso, dirs, files)
    print("=== SECTOR MAP (declared %d sectors, image %d) ===" % (declared, iso.sectors))
    for a0, a1, w in runs:
        if w is None:
            blob = iso.read(a0, (a1 - a0 + 1) * SEC)
            z = "all zero" if blob.count(0) == len(blob) else "NOT zero"
            print("  UNCLAIMED %6d..%-6d  %5d sectors  %s" % (a0, a1, a1 - a0 + 1, z))
    n_over = iso.sectors - declared
    tail = iso.read(declared, n_over * SEC)
    print("  overrun beyond declared: %d sectors, %s" %
          (n_over, "all zero" if tail.count(0) == len(tail) else "NOT zero"))
    if a.extract:
        for f in files:
            p = os.path.join(a.extract, f["path"].lstrip("/"))
            d = os.path.dirname(p)
            if d:
                os.makedirs(d, exist_ok=True)
            open(p, "wb").write(iso.read(f["lba"], f["size"]))
    if a.json:
        for f in files:
            f["sha1"] = iso.sha1(f["lba"], f["size"])
        json.dump({"dirs": dirs, "dirrecs": dirs_dates, "files": files},
                  open(a.json, "w"), indent=1)


main()
