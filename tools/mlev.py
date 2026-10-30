"""Reader for the 'Puzzle V2.0' level files in mlevs/.

Layout, all big endian:

    0x00  12 bytes   'Puzzle V2.0 '
    0x0C  u32        length of the header block that follows (always 8)
    0x10  u16 u16 u16 u16   version, ?, width, height  (in cells)
    0x18  chunks:    4-byte id, u32 length, length bytes, no padding

Every file on the disc is padded to exactly 15092 bytes, which is the
buffer the loader allocates; the chunk stream stops well before that.
"""
import struct, sys, os

MAGIC = b'Puzzle V2.0 '


class Level:
    def __init__(self, data):
        assert data[:12] == MAGIC, 'not a Puzzle V2.0 file'
        hlen = struct.unpack_from('>I', data, 12)[0]
        self.version, self.unk, self.w, self.h = struct.unpack_from('>4H', data, 16)
        self.chunks = []
        o = 16 + hlen
        while o + 8 <= len(data):
            cid = data[o:o+4]
            if not cid.strip() or cid == b'\0\0\0\0':
                break
            n = struct.unpack_from('>I', data, o+4)[0]
            if n > len(data) - o:
                break
            self.chunks.append((cid.decode('latin-1'), o, n, data[o+8:o+8+n]))
            o += 8 + n
        self.end = o
        self.data = data

    def chunk(self, cid):
        for c in self.chunks:
            if c[0].strip() == cid.strip():
                return c[3]
        return None

    def map(self):
        m = self.chunk('MAP')
        return [list(struct.unpack_from('>%dH' % self.w, m, r*self.w*2))
                for r in range(self.h)]


if __name__ == '__main__':
    for path in sorted(sys.argv[1:]):
        lv = Level(open(path, 'rb').read())
        print('%-24s v%d ?=%d %3dx%-3d  used %5d/%d  %s'
              % (os.path.basename(path), lv.version, lv.unk, lv.w, lv.h,
                 lv.end, len(lv.data),
                 ' '.join('%s:%d' % (c[0].strip(), c[2]) for c in lv.chunks)))
