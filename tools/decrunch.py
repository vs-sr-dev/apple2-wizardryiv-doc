#!/usr/bin/env python3
"""Decrunch every RNC ProPack method-1 block on the HeroQuest II disc.

Three shapes occur, and this walks all three:

  * a whole file that *is* one RNC block  (88 of the 97 files);
  * a **block container** -- `n` big-endian ULONG offsets, the first of which
    is the header length `4 * n`, each pointing at an RNC block.  Three files
    use it (`CreditsG.Bin`, `OverG.Rnc`, `Pack.Bin`) and an offset of 0 is an
    empty slot;
  * an AmigaDOS hunk file whose CODE/DATA bodies are each
    `ULONG reloc_offset, ULONG longwords|memflags, RNC block`  -- which is
    what `/QuestII` is.

Every block is verified against the CRC-16 in its own header.

    python tools/decrunch.py _work/files _work/unpacked
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rnc
import rnc1x
import hunk as hunkmod


def is_rnc(d, o=0):
    return len(d) >= o + 18 and d[o:o + 3] == b'RNC' and d[o + 3] in (1, 2)


def container_offsets(d):
    """Return the offset list if this looks like the disc's block container."""
    if len(d) < 8:
        return None
    first = struct.unpack_from('>I', d, 0)[0]
    if first < 8 or first % 4 or first > 256 or first > len(d):
        return None
    n = first // 4
    offs = [struct.unpack_from('>I', d, 4 * i)[0] for i in range(n)]
    if not all(o == 0 or (o < len(d) and is_rnc(d, o)) for o in offs):
        return None
    return offs


def walk(root):
    for dp, dn, fn in os.walk(root):
        dn.sort()
        for f in sorted(fn):
            yield os.path.join(dp, f)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    tot_in = tot_out = 0
    n_files = n_blocks = 0
    for p in walk(src):
        d = open(p, 'rb').read()
        rel = os.path.relpath(p, src).replace(os.sep, '/')
        out = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        if is_rnc(d):
            u, how = rnc1x.auto(d)
            open(out, 'wb').write(u)
            print("%-28s RNC          %8d -> %8d  %5.1f%%  CRC ok  key %s" %
                  (rel, len(d), len(u), 100.0 * len(d) / len(u), how))
            tot_in += len(d); tot_out += len(u); n_files += 1; n_blocks += 1
            continue
        offs = container_offsets(d)
        if offs:
            parts = []
            for i, o in enumerate(offs):
                if o == 0:
                    print("%-28s container[%d] EMPTY SLOT" % (rel, i))
                    parts.append(b'')
                    continue
                u, how = rnc1x.auto(d[o:])
                print("%-28s container[%d] at %6d -> %8d  key %s" % (rel, i, o, len(u), how))
                parts.append(u)
                open(out + '.%d' % i, 'wb').write(u)
                n_blocks += 1
            tot_in += len(d); tot_out += sum(len(x) for x in parts); n_files += 1
            print("%-28s container %2d %8d -> %8d  %5.1f%%  offsets %s" %
                  (rel, len(offs), len(d), sum(len(x) for x in parts),
                   100.0 * len(d) / max(1, sum(len(x) for x in parts)),
                   ','.join(str(o) for o in offs)))
            continue
        if d[:4] == b'\x00\x00\x03\xf3':
            try:
                _, hunks, sizes = hunkmod.parse(p, verbose=False)
            except SystemExit:
                hunks = []
            done = False
            for h in hunks:
                if h['off'] is None:
                    continue
                b = d[h['off']:h['off'] + h['size']]
                if not is_rnc(b, 8):
                    continue
                relo = struct.unpack_from('>I', b, 0)[0]
                hdr = struct.unpack_from('>I', b, 4)[0]
                u, khow = rnc1x.auto(b[8:])
                open(out + '.hunk%d' % h['index'], 'wb').write(u)
                print("%-28s hunk %d      %8d -> %8d  reloc at %d (%d entries follow), "
                      "hdr %08x, alloc %d, key %s" %
                      (rel, h['index'], h['size'], len(u), relo,
                       (len(u) - relo) // 4, hdr, sizes[h['index']][0] * 4, khow))
                n_blocks += 1
                tot_out += len(u)
                done = True
            if done:
                tot_in += len(d); n_files += 1
                continue
        open(out, 'wb').write(d)
        print("%-28s raw          %8d" % (rel, len(d)))
    print()
    print("%d files carried %d RNC blocks: %d bytes on disc -> %d bytes unpacked (%.1f%%)" %
          (n_files, n_blocks, tot_in, tot_out, 100.0 * tot_in / tot_out))


if __name__ == '__main__':
    main()
