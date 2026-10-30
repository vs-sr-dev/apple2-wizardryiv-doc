"""Find every IFF 8SVX sample linked into the level executables and write it out.

The samples went into the binary with their IFF wrapper intact, NAME and ANNO
chunks and all, so each one still carries its filename from the artist's
machine and the name of the tool that saved it.
"""
import os, struct, sys

def forms(d):
    o = 0
    while True:
        o = d.find(b'FORM', o)
        if o < 0:
            return
        n = struct.unpack_from('>I', d, o + 4)[0]
        if d[o+8:o+12] == b'8SVX' and 12 <= n <= len(d) - o - 8:
            yield o, n + 8
            o += n + 8
        else:
            o += 4

def chunks(f):
    o, out = 12, {}
    while o + 8 <= len(f):
        tag = f[o:o+4]
        n = struct.unpack_from('>I', f, o + 4)[0]
        out.setdefault(tag, f[o+8:o+8+n])
        o += 8 + n + (n & 1)
    return out

def wav(body, rate):
    hdr = b'RIFF' + struct.pack('<I', 36 + len(body)) + b'WAVEfmt ' \
        + struct.pack('<IHHIIHH', 16, 1, 1, rate, rate, 1, 8) \
        + b'data' + struct.pack('<I', len(body))
    return hdr + bytes((b + 128) & 0xFF for b in body)     # 8SVX is signed

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '_work/8svx'
    os.makedirs(out, exist_ok=True)
    rows = []
    for root, dirs, files in os.walk('_work/unpak'):
        dirs.sort(); files.sort()
        for fn in files:
            p = os.path.join(root, fn)
            d = open(p, 'rb').read()
            src = os.path.relpath(p, '_work/unpak').replace(os.sep, '/')
            for i, (o, n) in enumerate(forms(d)):
                c = chunks(d[o:o+n])
                vh = c.get(b'VHDR', b'')
                if len(vh) < 20:
                    continue
                one, rep, cyc, rate, oct_, comp, vol = struct.unpack('>IIIHBBI', vh)
                name = c.get(b'NAME', b'').split(b'\0')[0].decode('latin-1')
                anno = c.get(b'ANNO', b'').split(b'\0')[0].decode('latin-1')
                body = c.get(b'BODY', b'')
                base = (name or 'sample%d' % i).replace('/', '_')
                open(os.path.join(out, '%s_%s.wav'
                                  % (src.replace('/', '_'), base)), 'wb').write(wav(body, rate or 16726))
                rows.append((src, o, name, anno, rate, len(body), rep))
    for r in rows:
        print('%-28s @%08X  %-14s %-16s %5d Hz  %7d B  loop=%d' % r)
    print('--- %d samples, %d bytes of audio' % (len(rows), sum(r[5] for r in rows)))
