import os, struct
rows = []
for root, d, fs in os.walk('_work/root'):
    for f in sorted(fs):
        p = os.path.join(root, f)
        b = open(p, 'rb').read()
        if b[:4] == b'IMP!':
            orig, pk = struct.unpack_from('>II', b, 4)
            rel = p[len('_work/root'):].replace(os.sep, '/')
            rows.append((rel, len(b), orig, pk, len(b) - pk - 12))
print('%-38s %9s %9s %9s %4s %6s' % ('file', 'filesz', 'orig', 'packed', 'ovh', 'ratio'))
for r in rows:
    print('%-38s %9d %9d %9d %4d %5.1f%%' % (r[0], r[1], r[2], r[3], r[4], 100.0*r[3]/r[2]))
print(len(rows), 'IMP! files;', sum(r[2] for r in rows), 'bytes unpacked;', sum(r[1] for r in rows), 'on disc')
