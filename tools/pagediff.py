#!/usr/bin/env python3
"""Measure a localisation whose text is pixels rather than characters.

The manual on this disc is 115 IFF ILBM pages in three languages and there is
no character in any of them. The usual section 9 measurements — string count,
byte-identical strings across languages, encoding — all return zero. What can
still be measured is the picture: unpack the ByteRun1 BODY, convert the eight
bitplanes to one index per pixel, and then

  * how much of each page is ink (any index other than the commonest one),
  * how many distinct indices a page uses,
  * and, for the same page number in two languages, what fraction of the
    pixels differ — which separates the illustrations (identical) from the
    typeset text (different) without reading a word of it.

Usage:  python tools/pagediff.py <Pages-dir> [--pairs uk,fr]
"""
import sys, os, glob, struct, collections


def chunks(d):
    out = {}
    order = []
    o = 12
    while o + 8 <= len(d):
        cid = d[o:o + 4]
        sz = struct.unpack_from('>I', d, o + 4)[0]
        out[cid] = d[o + 8:o + 8 + sz]
        order.append(cid.decode('latin-1'))
        o += 8 + sz + (sz & 1)
    return out, order


def byterun1(src, want):
    out = bytearray()
    i = 0
    n = len(src)
    while len(out) < want and i < n:
        c = src[i]
        i += 1
        if c == 128:
            continue
        if c < 128:
            out += src[i:i + c + 1]
            i += c + 1
        else:
            if i >= n:
                break
            out += bytes([src[i]]) * (257 - c)
            i += 1
    return bytes(out)


def unpack(d):
    """Return (w, h, planes, indices) with one byte of colour index per pixel."""
    ch, _ = chunks(d)
    bm = ch[b'BMHD']
    w, h = struct.unpack_from('>HH', bm, 0)
    planes, mask, comp = bm[8], bm[9], bm[10]
    rb = ((w + 15) // 16) * 2
    want = rb * h * (planes + (1 if mask == 1 else 0))
    body = ch[b'BODY']
    raw = byterun1(body, want) if comp == 1 else body[:want]
    px = bytearray(w * h)
    for y in range(h):
        rowbase = y * rb * (planes + (1 if mask == 1 else 0))
        for p in range(planes):
            off = rowbase + p * rb
            bit = 1 << p
            row = raw[off:off + rb]
            base = y * w
            for xb in range(rb):
                b = row[xb]
                if not b:
                    continue
                x0 = xb * 8
                for k in range(8):
                    if b & (0x80 >> k):
                        x = x0 + k
                        if x < w:
                            px[base + x] |= bit
    return w, h, planes, bytes(px)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else 'extract/Pages'
    pairs = ('uk', 'fr', 'gr')
    if '--pairs' in sys.argv:
        pairs = tuple(sys.argv[sys.argv.index('--pairs') + 1].split(','))

    pages = {}
    for p in sorted(glob.glob(os.path.join(root, 'ebook.*.0*'))):
        base = os.path.basename(p)
        lang, num = base.split('.')[1], int(base.split('.')[2])
        w, h, planes, px = unpack(open(p, 'rb').read())
        c = collections.Counter(px)
        bg, bgn = c.most_common(1)[0]
        pages[(lang, num)] = dict(w=w, h=h, planes=planes, px=px,
                                  bg=bg, ink=1 - bgn / len(px), used=len(c))

    print("=== per page: background index, ink fraction, indices used ===")
    for lang in sorted(set(k[0] for k in pages)):
        nums = sorted(n for l, n in pages if l == lang)
        inks = [pages[(lang, n)]['ink'] for n in nums]
        used = [pages[(lang, n)]['used'] for n in nums]
        bgs = collections.Counter(pages[(lang, n)]['bg'] for n in nums)
        print("  %s : %d pages, ink %.1f%%..%.1f%% (mean %.1f%%), "
              "indices used %d..%d, background index %s"
              % (lang, len(nums), 100 * min(inks), 100 * max(inks),
                 100 * sum(inks) / len(inks), min(used), max(used),
                 dict(bgs)))

    print()
    print("=== same page number, two languages: fraction of pixels differing ===")
    a, b = pairs[0], pairs[1]
    common = sorted(n for l, n in pages if l == a and (b, n) in pages)
    print("  %s vs %s, %d page numbers in common" % (a, b, len(common)))
    print("  page   differ%%   ink(%s)  ink(%s)" % (a, b))
    tot = 0
    for n in common:
        pa, pb = pages[(a, n)]['px'], pages[(b, n)]['px']
        if len(pa) != len(pb):
            print("  %4d   (different geometry)" % n)
            continue
        d = sum(1 for i in range(len(pa)) if pa[i] != pb[i])
        tot += d
        print("  %4d   %7.2f   %6.2f%%  %6.2f%%"
              % (n, 100 * d / len(pa), 100 * pages[(a, n)]['ink'],
                 100 * pages[(b, n)]['ink']))
    if common:
        print("  mean over the %d common page numbers: %.2f%% of pixels differ"
              % (len(common), 100 * tot / (len(common) * 320 * 200)))


if __name__ == '__main__':
    main()
