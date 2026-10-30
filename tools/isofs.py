"""ISO 9660 reader for the Liberation (CD32) data track.

The track is a plain MODE1/2048 image, so a "sector" is 2,048 bytes at offset
lba*2048.  Only what the disc actually uses is implemented: one primary volume
descriptor (duplicated at 17), an L path table, and 8.3 directory records.  No
Joliet, no Rock Ridge, no extended attributes -- the disc has none.  Walking
it also yields the timestamps, which is the first thing worth doing: twelve of
the 197 records read 1992-02-05 and one of the twelve is the game executable,
whose own version string says 1994-04-08.

Usage: isofs.py <track01.iso>
"""
import struct, sys, os


class Entry:
    def __init__(self, parent, rec):
        self.len_dr   = rec[0]
        self.xa_len   = rec[1]
        self.lba      = struct.unpack_from('<I', rec, 2)[0]
        self.size     = struct.unpack_from('<I', rec, 10)[0]
        self.date     = tuple(rec[18:25])          # y-1900,m,d,h,m,s,gmtoff
        self.flags    = rec[25]
        self.unit_sz  = rec[26]
        self.gap_sz   = rec[27]
        self.volseq   = struct.unpack_from('<H', rec, 28)[0]
        n             = rec[32]
        self.raw_name = bytes(rec[33:33+n])
        self.system_use = bytes(rec[33+n + (1 - (n & 1)):self.len_dr])
        self.parent   = parent

    @property
    def is_dir(self):
        return bool(self.flags & 2)

    @property
    def name(self):
        if self.raw_name == b'\x00':
            return '.'
        if self.raw_name == b'\x01':
            return '..'
        return self.raw_name.decode('latin-1')

    @property
    def path(self):
        if self.parent is None:
            return '/' + self.name
        return self.parent.rstrip('/') + '/' + self.name

    def iso_date(self):
        y, mo, d, h, mi, s, off = self.date
        return '%04d-%02d-%02d %02d:%02d:%02d %+03d:%02d' % (
            1900 + y, mo, d, h, mi, s, off // 4, abs(off % 4) * 15)


class Iso:
    def __init__(self, path):
        self.data = open(path, 'rb').read()
        self.nsec = len(self.data) // 2048
        self.pvd  = self.sector(16)
        self.root_rec = self.pvd[156:156+34]
        self.vol_size = struct.unpack_from('<I', self.pvd, 80)[0]

    def sector(self, lba, n=1):
        return self.data[lba*2048:(lba+n)*2048]

    def read(self, e):
        return self.data[e.lba*2048: e.lba*2048 + e.size]

    def listdir(self, lba, size, parent):
        out, off = [], 0
        blob = self.data[lba*2048: lba*2048 + size]
        while off < len(blob):
            ln = blob[off]
            if ln == 0:                       # pad to end of the logical block
                off = (off // 2048 + 1) * 2048
                continue
            out.append(Entry(parent, blob[off:off+ln]))
            off += ln
        return out

    def walk(self):
        """Depth-first, directories in on-disc order."""
        root = Entry(None, self.root_rec)
        stack = [(root.lba, root.size, '')]
        while stack:
            lba, size, parent = stack.pop(0)
            kids = self.listdir(lba, size, parent or '/')
            for e in kids:
                if e.name in ('.', '..'):
                    continue
                yield e
                if e.is_dir:
                    stack.insert(0, (e.lba, e.size, e.path))


if __name__ == '__main__':
    iso = Iso(sys.argv[1])
    for e in iso.walk():
        print('%6d %9d %s %s%s' % (e.lba, e.size, e.iso_date(), e.path,
                                   '/' if e.is_dir else ''))
