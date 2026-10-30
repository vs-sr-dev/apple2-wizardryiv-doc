#!/usr/bin/env python3
"""Walk the ISO 9660 volume of the Gloom CD32 disc.

Prints the directory tree with LBA, size, timestamp and SHA-1, and optionally
extracts every file into a directory.

    python tools/isoread.py <image.iso>              list
    python tools/isoread.py <image.iso> -x _work/files   extract
"""
import sys, os, struct, hashlib

SECTOR = 2048

def u16le(b, o): return struct.unpack_from('<H', b, o)[0]
def u32le(b, o): return struct.unpack_from('<I', b, o)[0]
def u32be(b, o): return struct.unpack_from('>I', b, o)[0]

def dirdate(b):
    """7-byte directory record timestamp -> (iso string, gmt offset in 15-min units)"""
    y, mo, d, h, mi, s, off = b[0], b[1], b[2], b[3], b[4], b[5], struct.unpack_from('b', b, 6)[0]
    return "%04d-%02d-%02d %02d:%02d:%02d" % (1900 + y, mo, d, h, mi, s), off

def records(data, lba, length):
    """Yield raw directory records from an extent."""
    ext = data[lba * SECTOR: lba * SECTOR + length]
    off = 0
    while off < len(ext):
        n = ext[off]
        if n == 0:
            # skip to next logical sector boundary
            off = (off // SECTOR + 1) * SECTOR
            if off >= len(ext):
                break
            continue
        yield ext[off:off + n]
        off += n

def parse(rec):
    lba = u32le(rec, 2)
    size = u32le(rec, 10)
    ts, off = dirdate(rec[18:25])
    flags = rec[25]
    namelen = rec[32]
    name = rec[33:33 + namelen].decode('latin1')
    if name == '\x00': name = '.'
    elif name == '\x01': name = '..'
    if ';' in name: name = name.split(';')[0]
    return dict(lba=lba, size=size, ts=ts, tzoff=off, dir=bool(flags & 2), name=name, flags=flags)

def walk(data, lba, length, path, out):
    for rec in records(data, lba, length):
        e = parse(rec)
        if e['name'] in ('.', '..'):
            continue
        e['path'] = path + '/' + e['name']
        out.append(e)
        if e['dir']:
            walk(data, e['lba'], e['size'], e['path'], out)

def main():
    img = sys.argv[1]
    extract = None
    if '-x' in sys.argv:
        extract = sys.argv[sys.argv.index('-x') + 1]
    data = open(img, 'rb').read()
    pvd = data[16 * SECTOR:17 * SECTOR]
    rootrec = pvd[156:190]
    r = parse(rootrec)
    entries = []
    walk(data, r['lba'], r['size'], '', entries)
    print("volume %d sectors declared, image %d sectors" % (u32be(pvd, 84), len(data) // SECTOR))
    print("root at LBA %d, %d bytes, %s" % (r['lba'], r['size'], r['ts']))
    print()
    print("%-6s %8s  %-19s %-4s %-40s %s" % ("LBA", "size", "timestamp", "tz", "sha1", "path"))
    for e in sorted(entries, key=lambda x: x['lba']):
        if e['dir']:
            print("%-6d %8d  %-19s %-4d %-40s %s/" % (e['lba'], e['size'], e['ts'], e['tzoff'], '', e['path']))
        else:
            body = data[e['lba'] * SECTOR: e['lba'] * SECTOR + e['size']]
            h = hashlib.sha1(body).hexdigest()
            print("%-6d %8d  %-19s %-4d %-40s %s" % (e['lba'], e['size'], e['ts'], e['tzoff'], h, e['path']))
            if extract:
                # Windows cannot hold every AmigaDOS name (e.g. 'Gloom->HD')
                safe = e['path'].lstrip('/')
                for ch in '<>:"|?*':
                    safe = safe.replace(ch, '_')
                p = os.path.join(extract, safe)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                open(p, 'wb').write(body)
    files = [e for e in entries if not e['dir']]
    dirs = [e for e in entries if e['dir']]
    print()
    print("%d files, %d directories, %d bytes" % (len(files), len(dirs), sum(e['size'] for e in files)))

if __name__ == '__main__':
    main()
