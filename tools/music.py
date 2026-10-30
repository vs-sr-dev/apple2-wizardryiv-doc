"""Census the .pc music modules.

Each file in music/ is a self-contained, position-independent 68000 module:
seven `jmp d16(pc)` entries at offset 0, the player, then the song and its
samples.  There is no hunk header and no magic word; `work` loads the file
and calls into the jump table.

Two player builds shipped.  Diffing the files against each other separates
them, and the split lines up with the file naming and with two directory
timestamps that fell out of the MS-DOS epoch.

Sample slots are 22-byte NUL-padded names in the tracker tradition, and on
this disc several of them carry the composer's address instead.
"""
import glob, os, re, sys


def common_prefix(a, b):
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


if __name__ == '__main__':
    paths = sorted(glob.glob(os.path.join(sys.argv[1], '*')))
    blobs = [(p, open(p, 'rb').read()) for p in paths]
    ref = dict(blobs)[paths[0]]
    print('%-26s %8s %8s' % ('file', 'bytes', 'prefix'))
    for p, d in blobs:
        print('%-26s %8d %8d' % (os.path.basename(p), len(d),
                                 common_prefix(ref, d)))
    print()
    for p, d in blobs:
        names = [m.group().decode('latin-1')
                 for m in re.finditer(rb'[A-Za-z][A-Za-z0-9 ._+\-#()/]{4,22}',
                                      d[6000:])]
        seen = []
        for n in names:
            if re.search(r'[a-z]{3}', n) and n not in seen:
                seen.append(n)
        print('%s:' % os.path.basename(p))
        print('   ', seen[:32])
