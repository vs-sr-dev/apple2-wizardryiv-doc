#!/usr/bin/env python3
"""Census of the electronic book's page images, and the localisation split.

Every page is an IFF ILBM. This walks the chunk list of each, reports the
geometry, compression, CAMG mode id and palette, and then compares the three
language sets against each other: which page numbers exist in each language,
which pages are byte-identical across languages (a page with no text on it, or
a page nobody translated), and how far the CMAPs agree.

Usage:  python tools/pages.py <Pages-dir>
"""
import sys, os, glob, struct, hashlib, collections

CAMG_BITS = [
    (0x00000004, 'LACE'), (0x00000080, 'SPRITES'), (0x00000200, 'HAM'),
    (0x00000400, 'EHB'), (0x00000800, 'HIRES'), (0x00008000, 'GENLOCK_AUDIO'),
]
MONITORS = {0x00000000: 'DEFAULT', 0x00011000: 'NTSC', 0x00021000: 'PAL',
            0x00031000: 'MULTISCAN', 0x00041000: 'A2024',
            0x00051000: 'PROTO', 0x00061000: 'EURO72', 0x00071000: 'EURO36',
            0x00081000: 'SUPER72', 0x00091000: 'DBLNTSC', 0x000a1000: 'DBLPAL'}


def camg(v):
    mon = MONITORS.get(v & 0xFFFF1000, '0x%08x' % (v & 0xFFFF1000))
    fl = [n for b, n in CAMG_BITS if v & b]
    return "%s%s" % (mon, (' | ' + ' | '.join(fl)) if fl else '')


def walk(d):
    if d[0:4] != b'FORM':
        return None, []
    form = d[8:12]
    out = []
    o = 12
    while o + 8 <= len(d):
        cid = d[o:o + 4]
        sz = struct.unpack_from('>I', d, o + 4)[0]
        out.append((cid.decode('latin-1'), o, sz, d[o + 8:o + 8 + sz]))
        o += 8 + sz + (sz & 1)
    return form.decode('latin-1'), out


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else 'extract/Pages'
    files = sorted(glob.glob(os.path.join(root, '*')))
    langs = collections.defaultdict(dict)
    info = {}
    geoms = collections.Counter()
    camgs = collections.Counter()
    comps = collections.Counter()
    forms = collections.Counter()
    chunkorder = collections.Counter()
    for p in files:
        base = os.path.basename(p)
        d = open(p, 'rb').read()
        parts = base.split('.')
        if len(parts) < 3:
            continue
        lang, num = parts[1], parts[2]
        if num == 'chapters':
            langs[lang]['chapters'] = hashlib.sha1(d).hexdigest()
            continue
        form, chunks = walk(d)
        if form is None:
            print("NOT IFF: %s" % base)
            continue
        forms[form] += 1
        chunkorder[' '.join(c[0] for c in chunks)] += 1
        bmhd = dict(chunks and [(c[0], c[3]) for c in chunks]).get('BMHD')
        cm = dict([(c[0], c[3]) for c in chunks]).get('CMAP')
        cg = dict([(c[0], c[3]) for c in chunks]).get('CAMG')
        body = dict([(c[0], c[3]) for c in chunks]).get('BODY')
        w, h, x, y, planes, mask, comp = struct.unpack_from('>HHhhBBB', bmhd, 0)
        tc, xa, ya, pw, ph = struct.unpack_from('>HBBhh', bmhd, 9)
        cgv = struct.unpack_from('>I', cg, 0)[0] if cg else None
        geoms[(w, h, planes)] += 1
        camgs[cgv] += 1
        comps[comp] += 1
        info[base] = dict(lang=lang, num=int(num), w=w, h=h, planes=planes,
                          comp=comp, camg=cgv, aspect=(xa, ya),
                          cmap=hashlib.sha1(cm).hexdigest() if cm else None,
                          cmaplen=len(cm) if cm else 0,
                          bodylen=len(body) if body else 0,
                          size=len(d), sha1=hashlib.sha1(d).hexdigest())
        langs[lang][int(num)] = info[base]

    print("=== geometry ===")
    for (w, h, pl), n in geoms.most_common():
        print("  %d x %d, %d planes : %d files (%d colours, %d bytes raw)"
              % (w, h, pl, n, 1 << pl, (w // 8) * h * pl))
    print("  compression codes  : %s (1 = ByteRun1)" % dict(comps))
    print("  IFF form types     : %s" % dict(forms))
    print("  chunk order        :")
    for k, n in chunkorder.most_common():
        print("      %-40s %d" % (k, n))
    print("  CAMG values        :")
    for v, n in camgs.most_common():
        print("      0x%08x  %-30s %d files" % (v, camg(v), n))

    print()
    print("=== language sets ===")
    for lang in sorted(langs):
        nums = sorted(k for k in langs[lang] if isinstance(k, int))
        tot = sum(langs[lang][k]['size'] for k in nums)
        body = sum(langs[lang][k]['bodylen'] for k in nums)
        raw = sum((langs[lang][k]['w'] // 8) * langs[lang][k]['h']
                  * langs[lang][k]['planes'] for k in nums)
        print("  %s : %d pages %s..%s, %d bytes on disc, %d BODY bytes, "
              "%d bytes unpacked (ByteRun1 ratio %.3f)"
              % (lang, len(nums), nums[0], nums[-1], tot, body, raw, body / raw))
        print("       chapters file sha1 %s" % langs[lang].get('chapters', '-')[:16])

    print()
    print("=== byte-identical pages across languages ===")
    bysha = collections.defaultdict(list)
    for b, i in info.items():
        bysha[i['sha1']].append(b)
    for s, v in sorted(bysha.items()):
        if len(v) > 1:
            print("  %s  %s  (%d bytes)"
                  % (s[:12], ', '.join(sorted(v)), info[v[0]]['size']))
    print("  identical groups : %d of %d pages"
          % (sum(1 for v in bysha.values() if len(v) > 1), len(info)))

    print()
    print("=== palette sharing ===")
    bycm = collections.Counter(i['cmap'] for i in info.values())
    print("  distinct CMAPs : %d over %d pages" % (len(bycm), len(info)))
    for c, n in bycm.most_common(6):
        who = sorted(b for b, i in info.items() if i['cmap'] == c)
        print("     %s x%-3d  e.g. %s" % (c[:12], n, ', '.join(who[:4])))


if __name__ == '__main__':
    main()
