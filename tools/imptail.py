import os, struct
for root, d, fs in os.walk('_work/root'):
    for f in sorted(fs):
        p = os.path.join(root, f)
        b = open(p, 'rb').read()
        if b[:4] == b'IMP!':
            t = b[-38:]
            print('%-32s %s' % (f, t.hex(' ')))
