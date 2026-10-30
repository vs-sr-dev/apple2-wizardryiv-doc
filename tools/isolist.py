#!/usr/bin/env python3
"""Walk the ISO 9660 directory tree of the Microcosm CD32 data track.

Reads the PVD, follows the root directory extent, and prints every record with
LBA, size, timestamp and flags.  No external dependencies.
"""
import sys, os, struct, json

SECT = 2048

def find_iso(root):
    for f in os.listdir(root):
        if f.lower().endswith('.iso'):
            return os.path.join(root, f)
    raise SystemExit('no .iso found in %s' % root)

def both16(b, o):   return struct.unpack_from('<H', b, o)[0]
def both32(b, o):   return struct.unpack_from('<I', b, o)[0]

def dirdate(b, o):
    y, m, d, hh, mm, ss, tz = struct.unpack_from('<BBBBBBb', b, o)
    return '%04d-%02d-%02d %02d:%02d:%02d %+d' % (1900 + y, m, d, hh, mm, ss, tz)

def records(img, lba, length):
    data = b''
    for i in range((length + SECT - 1) // SECT):
        img.seek((lba + i) * SECT); data += img.read(SECT)
    data = data[:length]
    o = 0
    while o < len(data):
        ln = data[o]
        if ln == 0:
            o = (o // SECT + 1) * SECT
            continue
        r = data[o:o + ln]
        ext = both32(r, 2)
        size = both32(r, 10)
        flags = r[25]
        nlen = r[32]
        name = r[33:33 + nlen]
        yield {'lba': ext, 'size': size, 'flags': flags,
               'date': dirdate(r, 18),
               'name': name.decode('latin-1'), 'reclen': ln}
        o += ln

def walk(img, lba, size, path, out):
    for r in records(img, lba, size):
        n = r['name']
        if n in ('\x00', '\x01'):
            continue
        full = path + '/' + n
        r['path'] = full
        r['dir'] = bool(r['flags'] & 2)
        out.append(r)
        if r['dir']:
            walk(img, r['lba'], r['size'], full, out)

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    iso = find_iso(root)
    img = open(iso, 'rb')
    img.seek(16 * SECT); pvd = img.read(SECT)
    info = {
        'image': os.path.basename(iso),
        'image_bytes': os.path.getsize(iso),
        'image_sectors': os.path.getsize(iso) // SECT,
        'system_id': pvd[8:40].decode('latin-1'),
        'volume_id': pvd[40:72].decode('latin-1'),
        'volume_space': both32(pvd, 80),
        'block_size': both16(pvd, 128),
        'path_table_size': both32(pvd, 132),
        'l_path': struct.unpack_from('<I', pvd, 140)[0],
        'l_path_opt': struct.unpack_from('<I', pvd, 144)[0],
        'm_path': struct.unpack_from('>I', pvd, 148)[0],
        'm_path_opt': struct.unpack_from('>I', pvd, 152)[0],
        'root_lba': both32(pvd, 156 + 2),
        'root_size': both32(pvd, 156 + 10),
        'root_date': dirdate(pvd, 156 + 18),
        'volume_set': pvd[190:318].decode('latin-1'),
        'publisher': pvd[318:446].decode('latin-1'),
        'preparer': pvd[446:574].decode('latin-1'),
        'application': pvd[574:702].decode('latin-1'),
        'copyright_file': pvd[702:739].decode('latin-1'),
        'abstract_file': pvd[739:776].decode('latin-1'),
        'biblio_file': pvd[776:813].decode('latin-1'),
        'created': pvd[813:830].decode('latin-1'),
        'modified': pvd[830:847].decode('latin-1'),
        'expires': pvd[847:864].decode('latin-1'),
        'effective': pvd[864:881].decode('latin-1'),
    }
    out = []
    walk(img, info['root_lba'], info['root_size'], '', out)
    info['entries'] = len(out)
    info['files'] = sum(1 for r in out if not r['dir'])
    info['dirs'] = sum(1 for r in out if r['dir'])
    print(json.dumps(info, indent=1)[:2000])
    print('--- %d entries ---' % len(out))
    for r in sorted(out, key=lambda r: r['lba']):
        print('%8d %10d %s %s%s' % (r['lba'], r['size'], r['date'], r['path'],
                                    '/' if r['dir'] else ''))
    with open(os.path.join(root, '_work', 'tree.json'), 'w') as fh:
        json.dump({'pvd': info, 'records': out}, fh, indent=1)

main()
