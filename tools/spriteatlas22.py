#!/usr/bin/env python3
"""spriteatlas22.py -- `SpriteAtlas` objects (class 687078895) out of a
version-22 Unity SerializedFile, read from a hex dump on
pc-celltosingularity-doc, closed on every atlas and joined to every sprite.

WHY
---
On that object 3,432 of 4,749 `Sprite` objects name NO texture of their own:
their pixels live on the pages of 45 `SpriteAtlas` objects, and the pages are
`sactx-*` Texture2Ds (107 of them, every one Crunch-compressed). Without the
atlas a sprite is a name and a rectangle in nothing; with it, a name, a page
and a rectangle on the page. `unitytex22.py` reads the Sprite and the
Texture2D; this reads the atlas between them and nothing else.

THE BODY AT FORMAT 22, as measured on `Achievements` (32,344 bytes, 236
sprites) and closed on 45 of 45:

    aligned string   m_Name
    i32 n, n x PPtr  m_PackedSprites        fileID i32 + pathID i64 = 12 bytes
    i32 m, m x astr  m_PackedSpriteNamesToIndex
    i32 k, k x ENTRY m_RenderDataMap        108 bytes each:
        16 bytes     key: GUID
        i64          key: the second word     (the pair a Sprite carries as
                                              m_RenderDataKey)
        PPtr         texture                   the page
        PPtr         alphaTexture              zero on this object
        f32 x4       textureRect               x, y, w, h on the page
        f32 x2       textureRectOffset
        f32 x2       atlasRectOffset
        f32 x4       uvTransform
        f32          downscaleMultiplier
        u32          settingsRaw
        i32 s, s x   secondaryTextures         0 on this object
    aligned string   m_Tag
    u8               m_IsVariant, then alignment to 4
    = end of the body

CLOSURES: n == m == k on every atlas; the body ends at its last byte; every
entry's page PPtr names a Texture2D in the same file; and the JOIN -- every
Sprite whose texture PPtr is null carries a render key that exactly one
atlas entry has, and its textureRect lies inside that page's width and
height. The tool prints the pages by name and format and says which, if
any, can be rendered without a Crunch decoder (`unitytex22.py`'s decoders:
RGBA32, DXT1, DXT5 ...). It does not decode Crunch.

    python tools/spriteatlas22.py census DIR         -- every atlas, the closures, the join
    python tools/spriteatlas22.py pages  DIR         -- the pages: texture, size, format, sprites on it
    python tools/spriteatlas22.py list   DIR --atlas NAME   -- one atlas's sprites and rects
    python tools/spriteatlas22.py selftest
"""
import argparse
import collections
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dirguard                                            # noqa: E402
import nameguard                                           # noqa: E402
import unityfs                                             # noqa: E402
import unitytex22                                          # noqa: E402

CLASS_ID = 687078895
Refused = unitytex22.Refused


class Atlas(object):
    def __init__(self, b, little=True):
        r = unitytex22.R(b, little)
        self.name = r.astr()
        n = r.i32()
        if n < 0 or n > 1 << 20:
            raise Refused('%s: %d packed sprites is not credible' % (self.name, n))
        self.packed = [r.pptr() for _ in range(n)]
        m = r.i32()
        if m < 0 or m > 1 << 20:
            raise Refused('%s: %d names is not credible' % (self.name, m))
        self.names = [r.astr() for _ in range(m)]
        k = r.i32()
        if k < 0 or k > 1 << 20:
            raise Refused('%s: %d map entries is not credible' % (self.name, k))
        self.entries = []
        for _ in range(k):
            guid = r.raw(16).hex()
            second = r.i64()
            tex = r.pptr()
            alpha = r.pptr()
            rect = tuple(r.f32() for _ in range(4))
            rect_off = (r.f32(), r.f32())
            atlas_off = (r.f32(), r.f32())
            uv = tuple(r.f32() for _ in range(4))
            down = r.f32()
            settings = r.u32()
            s = r.i32()
            if s < 0 or s > 64:
                raise Refused('%s: %d secondary textures is not credible'
                              % (self.name, s))
            secondary = []
            for _ in range(s):
                secondary.append((r.pptr(), r.astr()))
            self.entries.append({'key': (guid, second), 'texture': tex,
                                 'alpha': alpha, 'rect': rect,
                                 'rect_off': rect_off, 'atlas_off': atlas_off,
                                 'uv': uv, 'downscale': down,
                                 'settings': settings, 'secondary': secondary})
        self.tag = r.astr()
        self.is_variant = r.u8()
        r.align(4)
        self.end = r.p
        self.padding = len(b) - r.p
        self.closed = (self.padding == 0)
        self.counts_agree = (n == m == k)

    def by_key(self):
        return {e['key']: e for e in self.entries}


def atlases_of(path, sf=None):
    try:
        sf = sf or unitytex22.load22(path)
    except Refused as e:
        yield e, None
        return
    little = sf.endianness == 0
    for o in sf.objects:
        if sf.class_of(o) != CLASS_ID:
            continue
        try:
            yield Atlas(sf.body(o), little), o
        except (Refused, struct.error, IndexError) as e:
            yield Refused(str(e)), o


def _textures(path, sf):
    out = {}
    for t, o in unitytex22.textures_of(path):
        if o is not None and not isinstance(t, Refused):
            out[o['path_id']] = t
    return out


def gather(root):
    """Every atlas, every sprite, every texture under root, by file."""
    atl, spr, tex, refused = [], [], {}, []
    for p in unitytex22.files_of(root):
        try:
            sf = unitytex22.load22(p)
        except Refused:
            continue
        rel = os.path.relpath(p, root).replace(os.sep, '/')
        tex[rel] = None
        for a, o in atlases_of(p, sf):
            if isinstance(a, Refused):
                refused.append((rel, o['path_id'] if o else None, str(a)))
            else:
                atl.append((rel, o, a))
        for s, o in unitytex22.sprites_of(p, sf):
            if not isinstance(s, Refused):
                spr.append((rel, p, sf, o, s))
        if any(sf.class_of(o) == 28 for o in sf.objects):
            tex[rel] = _textures(p, sf)
        else:
            tex[rel] = {}
    return atl, spr, tex, refused


def cmd_census(args):
    dirguard.want_tree(args.path, 'spriteatlas22')
    atl, spr, tex, refused = gather(args.path)
    if not atl:
        sys.exit('spriteatlas22: no SpriteAtlas (class %d) under %s'
                 % (CLASS_ID, args.path))
    closed = agree = 0
    entries = packed = 0
    pages_ok = pages_n = 0
    keymap = {}
    dup_keys = 0
    per_file = collections.Counter()
    print('%-40s %7s %6s %6s %6s %s' % ('ATLAS', 'BYTES', 'SPRITE', 'NAMES',
                                       'MAP', 'CLOSE AGREE VARIANT TAG'))
    for rel, o, a in sorted(atl, key=lambda x: (x[0], x[2].name)):
        closed += a.closed
        agree += a.counts_agree
        entries += len(a.entries)
        packed += len(a.packed)
        per_file[rel] += 1
        for e in a.entries:
            pages_n += 1
            fid, pid = e['texture']
            t = tex.get(rel, {}).get(pid) if fid == 0 else None
            pages_ok += t is not None
            if e['key'] in keymap:
                dup_keys += 1
            keymap[e['key']] = (rel, a, e, t)
        print('%-40s %7d %6d %6d %6d %-5s %-5s %-7d %s'
              % (a.name[:40], o['size'], len(a.packed), len(a.names),
                 len(a.entries), 'yes' if a.closed else 'NO',
                 'yes' if a.counts_agree else 'NO', a.is_variant, a.tag))
    print()
    print('SpriteAtlas objects      %d in %d serialized files' % (len(atl), len(per_file)))
    print('closure (body end)       %d of %d' % (closed, len(atl)))
    print('closure (n == m == k)    %d of %d' % (agree, len(atl)))
    print('map entries              %d   packed PPtrs %d   distinct keys %d   duplicate keys %d'
          % (entries, packed, len(keymap), dup_keys))
    print('page PPtrs resolving to a Texture2D in the same file: %d of %d'
          % (pages_ok, pages_n))
    # the join
    null_tex = [x for x in spr if x[4].texture[1] == 0]
    joined = inside = 0
    unjoined = []
    for rel, p, sf, o, s in null_tex:
        hit = keymap.get(s.render_key)
        if hit is None:
            unjoined.append((rel, s.name))
            continue
        joined += 1
        arel, a, e, t = hit
        x, y, w, h = e['rect']
        if t is not None and 0 <= x and 0 <= y and x + w <= t.width + 1e-3 and y + h <= t.height + 1e-3:
            inside += 1
    print('sprites with a null texture PPtr: %d; joined to an atlas entry by '
          'render key: %d; rect inside the page: %d' % (len(null_tex), joined, inside))
    ext = [x for x in spr if x[4].texture[0] != 0]
    own = [x for x in spr if x[4].texture[0] == 0 and x[4].texture[1] != 0]
    print('sprites with an external texture PPtr: %d; with a texture of their '
          'own in the same file: %d; total sprites %d' % (len(ext), len(own), len(spr)))
    # entries nobody uses
    used = set(x[4].render_key for x in null_tex) | set(x[4].render_key for x in ext)
    print('atlas entries no null-texture or external sprite claims: %d of %d'
          % (sum(1 for k in keymap if k not in used), len(keymap)))
    if unjoined:
        print()
        print('%d sprites with a null texture and NO atlas entry:' % len(unjoined))
        for rel, nm in unjoined[:20]:
            print('  %-28s %s' % (rel, nm))
    if refused:
        print()
        print('%d atlases REFUSED:' % len(refused))
        for rel, pid, why in refused:
            print('  %-28s #%s %s' % (rel, pid, why))
    ok = (closed == len(atl) and agree == len(atl) and pages_ok == pages_n
          and not refused and not unjoined and dup_keys == 0)
    return 0 if ok else 1


def cmd_pages(args):
    dirguard.want_tree(args.path, 'spriteatlas22')
    atl, spr, tex, refused = gather(args.path)
    if not atl:
        sys.exit('spriteatlas22: no SpriteAtlas under %s' % args.path)
    pages = collections.Counter()
    where = {}
    for rel, o, a in atl:
        for e in a.entries:
            fid, pid = e['texture']
            pages[(rel, pid)] += 1
            where[(rel, pid)] = a.name
    fmt_n = collections.Counter()
    print('%-28s %7s %-46s %5s %5s %-14s %7s %s'
          % ('FILE', 'PATHID', 'PAGE', 'W', 'H', 'FORMAT', 'SPRITES', 'ATLAS'))
    decodable = 0
    for (rel, pid), n in sorted(pages.items(), key=lambda kv: (-kv[1], kv[0])):
        t = tex.get(rel, {}).get(pid)
        if t is None:
            print('%-28s %7d %-46s %5s %5s %-14s %7d %s' % (rel, pid, '(no Texture2D)', '-', '-', '-', n, where[(rel, pid)]))
            continue
        fmt = unitytex22.FORMAT.get(t.format, t.format)
        fmt_n[fmt] += 1
        decodable += t.format in unitytex22.DECODABLE
        print('%-28s %7d %-46s %5d %5d %-14s %7d %s'
              % (rel, pid, t.name[:46], t.width, t.height, fmt, n, where[(rel, pid)][:30]))
    print()
    print('pages %d; by format: %s' % (len(pages), ', '.join('%s x%d' % kv for kv in fmt_n.most_common())))
    print('pages renderable by unitytex22.py today (no Crunch decoder): %d of %d'
          % (decodable, len(pages)))
    return 0


def cmd_list(args):
    dirguard.want_tree(args.path, 'spriteatlas22')
    atl, spr, tex, refused = gather(args.path)
    for rel, o, a in atl:
        if a.name != args.atlas:
            continue
        print('%s (path %d in %s): %d sprites' % (a.name, o['path_id'], rel, len(a.entries)))
        names = dict(zip([k for k in (a.packed)], a.names))
        for nm, e in zip(a.names, a.entries):
            x, y, w, h = e['rect']
            print('  %-40s page #%-6d rect %7.1f %7.1f %6.1f x %6.1f  settings 0x%02x'
                  % (nm[:40], e['texture'][1], x, y, w, h, e['settings']))
        return 0
    sys.exit('spriteatlas22: no atlas named %r under %s' % (args.atlas, args.path))


# ------------------------------------------------------------------ selftest
def _atlas_body(name, sprites, page_pid=813, tag='', variant=0):
    """sprites: [(name, pathid, guid16, second, rect)]"""
    b = unitytex22._astr(name)
    b += struct.pack('<i', len(sprites))
    for _n, pid, _g, _s, _r in sprites:
        b += struct.pack('<iq', 0, pid)
    b += struct.pack('<i', len(sprites))
    for n, _p, _g, _s, _r in sprites:
        b += unitytex22._astr(n)
    b += struct.pack('<i', len(sprites))
    for _n, _p, g, s, r in sprites:
        b += g + struct.pack('<q', s) + struct.pack('<iq', 0, page_pid) + struct.pack('<iq', 0, 0)
        b += struct.pack('<ffff', *r) + struct.pack('<ff', 0, 0) + struct.pack('<ff', 0, 0)
        b += struct.pack('<ffff', 50, 64, 50, 499) + struct.pack('<f', 1.0) + struct.pack('<I', 0x43)
        b += struct.pack('<i', 0)
    b += unitytex22._astr(tag) + bytes([variant]) + bytes(3)
    return b


def cmd_selftest(_args):
    checks = []
    g1 = bytes(range(16))
    g2 = bytes(range(16, 32))
    body = _atlas_body('Achievements', [('ac_a_1', 6012, g1, 0x01450320, (0.0, 448.08, 114.92, 114.92)),
                                        ('ac_b_2', 4471, g2, 0x01450320, (114.92, 448.08, 114.92, 114.92))])
    a = Atlas(body)
    checks.append(('a hand-built atlas of two sprites parses, counts agree, body closes',
                   a.name == 'Achievements' and a.counts_agree and a.closed
                   and len(a.entries) == 2, '%s %s' % (a.counts_agree, a.closed)))
    checks.append(('the map key is (GUID hex, i64) and the page PPtr is (0, 813)',
                   a.entries[0]['key'] == (g1.hex(), 0x01450320)
                   and a.entries[0]['texture'] == (0, 813), str(a.entries[0]['key'])))
    checks.append(('the entry is 108 bytes: two entries, names and PPtrs make the measured body size',
                   len(body) == 4 + 12 + 4 + 2 * 12 + 4 + 2 * 12 + 4 + 2 * 108 + 4 + 4, str(len(body))))
    checks.append(('textureRect is read as x, y, w, h',
                   abs(a.entries[1]['rect'][0] - 114.92) < 1e-3, ''))
    checks.append(('a body with 4 bytes of padding does not close',
                   not Atlas(body + bytes(4)).closed, ''))
    try:
        Atlas(body[:-40])
        checks.append(('a body cut short is REFUSED, not read', False, 'accepted'))
    except (Refused, struct.error, IndexError):
        checks.append(('a body cut short is REFUSED, not read', True, ''))
    bad = struct.pack('<i', 12) + b'Achievements' + struct.pack('<i', 1 << 30)
    try:
        Atlas(bad)
        checks.append(('an absurd sprite count is REFUSED', False, 'accepted'))
    except Refused:
        checks.append(('an absurd sprite count is REFUSED', True, ''))
    # a sprite body from unitytex22's own builder carries the same key shape
    sb = unitytex22._sprite_body('ac_a_1', (0, 0, 115, 115), (0, 0), (0.0, 448.08, 114.92, 114.92))
    s = unitytex22.Sprite(sb)
    checks.append(("unitytex22's Sprite carries a render key of the same shape (hex, int)",
                   isinstance(s.render_key[0], str) and len(s.render_key[0]) == 32
                   and isinstance(s.render_key[1], int), str(s.render_key)))
    width = max(len(c[0]) for c in checks)
    bad = 0
    for label, ok, note in checks:
        print('  %-*s  %s  %s' % (width, label, 'ok  ' if ok else 'FAIL', note))
        bad += not ok
    print()
    print('%d checks, %d failures' % (len(checks), bad))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    for nm in ('census', 'pages', 'list'):
        p = sub.add_parser(nm)
        p.add_argument('path')
        if nm == 'list':
            p.add_argument('--atlas', required=True)
    sub.add_parser('selftest')
    args = ap.parse_args()
    nameguard.guard()
    return {'census': cmd_census, 'pages': cmd_pages, 'list': cmd_list,
            'selftest': cmd_selftest}[args.cmd](args)


if __name__ == '__main__':
    sys.exit(main())
