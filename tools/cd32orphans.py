"""Two checks that cost nothing and have paid on every disc in this series.

  orphans.py <tree> --named    every filename-shaped string in every
                               executable, checked against the directory:
                               the misses are cut content the code still
                               believes in.
  orphans.py <tree> --unnamed  every file on the disc that no other file
                               names, allowing for the loader's `%` and `*`
                               templates: the hits are leftovers.

Usage: orphans.py _work/iso --named
"""
import os, re, sys

NAMEPAT = re.compile(
    rb'[A-Za-z0-9_./%*\-]{3,40}\.'
    rb'(x3g|x3d|img|spr|vgm|txt|asp|sty|fnt|bin|sam|log|library|vfx|dat|sav)',
    re.I)
# names the loader builds from a template rather than naming outright
TEMPLATES = [
    (re.compile(r'^Wall\d\d\.VGM$', re.I), 'WALL*.VGM'),
    (re.compile(r'^[0-3]Liberation\.FNT$', re.I), '%Liberation.FNT'),
    (re.compile(r'^Samples[01]\.BIN$', re.I), 'Samples%.BIN'),
    (re.compile(r'^[1-3].*\.x3g$', re.I), 'the 0-prefixed form'),
    (re.compile(r'^(Char1|shop1|newChar|EndGame|endgamet)/Voice[12]\.(SAM|LOG)$',
                re.I), 'the directory plus Voice1/2'),
    (re.compile(r'^(Char1|shop1|newChar|EndGame|endgamet)/.*\.txt$', re.I),
     'the directory name'),
    (re.compile(r'^libs/.*\.library$', re.I), 'LIBS: and the library name'),
    (re.compile(r'^s/startup-sequence$', re.I), 'Kickstart'),
    (re.compile(r'^The Game(\.info)?$'), 'Workbench'),
    (re.compile(r'^c/(Delete|dir|Assign|copy|makedir|mount|noopenwb|relabel'
                r'|setpatch)$', re.I), 'the C: assign'),
]


def tree(root):
    out = []
    for dp, dn, fn in os.walk(root):
        for f in fn:
            out.append(os.path.relpath(os.path.join(dp, f), root)
                       .replace(os.sep, '/'))
    return sorted(out)


if __name__ == '__main__':
    root, mode = sys.argv[1], sys.argv[2]
    files = tree(root)
    lower = {f.split('/')[-1].lower() for f in files}
    if mode == '--named':
        blobs = {f: open(os.path.join(root, f), 'rb').read()
                 for f in files
                 if os.path.getsize(os.path.join(root, f)) < 400_000
                 and open(os.path.join(root, f), 'rb').read(4)
                 == bytes.fromhex('000003f3')}
        seen = {}
        for f, b in blobs.items():
            for m in NAMEPAT.finditer(b):
                seen.setdefault(m.group().decode('latin-1'), set()).add(f)
        print('%-24s %-9s %s' % ('string in code', 'on disc', 'named by'))
        for s in sorted(seen, key=str.lower):
            base = s.split(':')[-1].split('/')[-1].lower()
            if base.endswith('.library'):
                continue
            hit = base in lower
            print('%-24s %-9s %s'
                  % (s, 'yes' if hit else '** NO **',
                     ', '.join(sorted(seen[s]))))
    else:
        blobs = {f: open(os.path.join(root, f), 'rb').read()
                 for f in files
                 if os.path.getsize(os.path.join(root, f)) < 4_000_000}
        for f in files:
            base = f.split('/')[-1]
            tmpl = next((t for p, t in TEMPLATES if p.match(f)
                         or p.match(base)), None)
            pat = re.compile(rb'[:/]' + re.escape(base.encode()), re.I)
            who = [g for g, b in blobs.items() if g != f and pat.search(b)]
            if who:
                continue
            print('%-26s %9d   %s'
                  % (f, os.path.getsize(os.path.join(root, f)),
                     'built from ' + tmpl if tmpl else '** nothing names it **'))
