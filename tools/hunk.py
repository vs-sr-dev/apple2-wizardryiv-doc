#!/usr/bin/env python3
"""AmigaDOS hunk reader for /cosm.

Prints the hunk table, then every SYMBOL and DEBUG block.  The DEBUG blocks on
this executable are HCLN/HEADDBGV01 line-number tables emitted by the
assembler, so each one names one source file.
"""
import sys, struct

HT = {0x3E7:'UNIT',0x3E8:'NAME',0x3E9:'CODE',0x3EA:'DATA',0x3EB:'BSS',
      0x3EC:'RELOC32',0x3ED:'RELOC16',0x3EE:'RELOC8',0x3EF:'EXT',
      0x3F0:'SYMBOL',0x3F1:'DEBUG',0x3F2:'END',0x3F3:'HEADER',
      0x3F7:'BREAK',0x3F9:'DREL16'}

d = open(sys.argv[1],'rb').read()
def L(o): return struct.unpack_from('>I', d, o)[0]
o = 0
assert L(0) == 0x3F3, 'not a hunk file'
o = 4
while L(o): o += 4 * (L(o) + 1)   # resident library names
o += 4
tabsize, first, last = L(o), L(o+4), L(o+8); o += 12
sizes = [L(o + 4*i) for i in range(last - first + 1)]
o += 4 * len(sizes)
print('hunk table: %d hunks, first=%d last=%d' % (tabsize, first, last))
for i, s in enumerate(sizes):
    print('  hunk %d  %d longwords = %d bytes  flags=%s' %
          (i, s & 0x3FFFFFFF, (s & 0x3FFFFFFF) * 4,
           {0:'any',1:'chip',2:'fast'}.get(s >> 30, '?')))
hunk = -1
symbols = []
debugs = []
while o < len(d) - 3:
    t = L(o) & 0x3FFFFFFF; o += 4
    name = HT.get(t)
    if name is None:
        print('  ?? unknown hunk id 0x%x at 0x%x' % (t, o-4)); break
    if t in (0x3E9, 0x3EA):
        n = L(o); o += 4; hunk += 1
        print('0x%08x %-8s hunk %d  %d bytes' % (o-8, name, hunk, n*4)); o += n*4
    elif t == 0x3EB:
        n = L(o); o += 4; hunk += 1
        print('0x%08x %-8s hunk %d  %d bytes' % (o-8, name, hunk, n*4))
    elif t == 0x3EC:
        print('0x%08x RELOC32' % (o-4))
        tot = 0
        while True:
            n = L(o); o += 4
            if n == 0: break
            o += 4; tot += n; o += 4*n
        print('          %d relocations' % tot)
    elif t == 0x3F0:
        while True:
            n = L(o); o += 4
            if n == 0: break
            nm = d[o:o+4*n].split(b'\0')[0].decode('latin-1'); o += 4*n
            val = L(o); o += 4
            symbols.append((hunk, nm, val))
    elif t == 0x3F1:
        n = L(o); o += 4
        blob = d[o:o+4*n]; o += 4*n
        debugs.append((o - 4*n, blob))
    elif t == 0x3F2:
        pass
    else:
        print('  unhandled %s at 0x%x' % (name, o-4)); break
print('%d SYMBOL entries, %d DEBUG blocks' % (len(symbols), len(debugs)))
for h, nm, v in symbols[:400]:
    print('  sym h%d %-32s 0x%08x' % (h, nm, v))
for off, b in debugs:
    tag = b[4:14].decode('latin-1', 'replace')
    # HEADDBGV01 blocks: base(4) 'HEADDBGV01' pad ... name then line/offset pairs
    txt = b''.join(bytes([c]) if 32 <= c < 127 else b'.' for c in b[:120])
    print('  dbg @0x%06x len=%d  %s' % (off, len(b), txt.decode()))
