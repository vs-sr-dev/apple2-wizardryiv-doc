"""Scan a file (or a whole disc image) for the compression and container
magics this format uses, and for the Akiko / custom-chip register accesses
of checklist section 4.

  scan.py --magic  <file>      count every known cruncher magic
  scan.py --regs   <file>      histogram $00DFF0xx custom-chip registers
  scan.py --akiko  <file>      every byte pattern that could be Akiko
  scan.py --lvo    <file>      histogram of  jsr d(a6)  offsets

Section 5 of the platform checklist insists the census comes first: a magic
scan that finds nothing proves nothing.  This is the second step.
"""
import sys, struct, collections

MAGICS = [b'RNC\x01', b'RNC\x02', b'IMP!', b'ATN!', b'PP20', b'PP11',
          b'XPKF', b'CrM!', b'CrM2', b'LZX', b'SQSH', b'RNC', b'S404',
          b'FORM', b'AmSp', b'ImgA', b'CHAR']


def magic(data):
    for m in MAGICS:
        n = data.count(m)
        if n:
            print('%-6s %6d' % (m.decode('latin-1'), n))


def regs(data):
    """Every  $00DFF0xx  longword, by low byte -- not just  lea $DFF000,aN."""
    h = collections.Counter()
    i = 0
    while True:
        i = data.find(b'\x00\xdf\xf0', i)
        if i < 0 or i + 3 >= len(data):
            break
        h[data[i + 3]] += 1
        i += 1
    for k in sorted(h):
        print('  $DFF0%02X  %5d  %s' % (k, h[k], REGNAME.get(k, '')))


REGNAME = {
    0x00: 'BLTDDAT', 0x02: 'DMACONR', 0x06: 'VHPOSR', 0x0A: 'JOY0DAT',
    0x0C: 'JOY1DAT', 0x10: 'ADKCONR', 0x1C: 'INTENAR', 0x1E: 'INTREQR',
    0x40: 'BLTCON0', 0x42: 'BLTCON1', 0x44: 'BLTAFWM', 0x46: 'BLTALWM',
    0x48: 'BLTCPTH', 0x4C: 'BLTBPTH', 0x50: 'BLTAPTH', 0x54: 'BLTDPTH',
    0x58: 'BLTSIZE', 0x60: 'BLTCMOD', 0x62: 'BLTBMOD', 0x64: 'BLTAMOD',
    0x66: 'BLTDMOD', 0x70: 'BLTCDAT', 0x72: 'BLTBDAT', 0x74: 'BLTADAT',
    0x80: 'COP1LCH', 0x84: 'COP2LCH', 0x88: 'COPJMP1', 0x8A: 'COPJMP2',
    0x8E: 'DIWSTRT', 0x90: 'DIWSTOP', 0x92: 'DDFSTRT', 0x94: 'DDFSTOP',
    0x96: 'DMACON', 0x9A: 'INTENA', 0x9C: 'INTREQ', 0x9E: 'ADKCON',
    0xA0: 'AUD0LCH', 0xA4: 'AUD0LEN', 0xA6: 'AUD0PER', 0xA8: 'AUD0VOL',
    0xB0: 'AUD1LCH', 0xB4: 'AUD1LEN', 0xB6: 'AUD1PER', 0xB8: 'AUD1VOL',
    0xC0: 'AUD2LCH', 0xC4: 'AUD2LEN', 0xC6: 'AUD2PER', 0xC8: 'AUD2VOL',
    0xD0: 'AUD3LCH', 0xD4: 'AUD3LEN', 0xD6: 'AUD3PER', 0xD8: 'AUD3VOL',
    0xE0: 'BPL1PTH', 0xE4: 'BPL2PTH', 0xE8: 'BPL3PTH', 0xEC: 'BPL4PTH',
    0xF0: 'BPL5PTH', 0xF4: 'BPL6PTH', 0xF8: 'BPL7PTH', 0xFC: 'BPL8PTH',
}


def akiko(data):
    """Checklist section 7: the byte pattern 00 B8 00 is not evidence.
    A pointer load or a reference to the C2P port at $B80038 is."""
    print('%-25s %6d' % ('bare  00 B8 00 xx', count3(data, b'\x00\xb8\x00')))
    for name, pat in [
            ('longword $00B80000',  b'\x00\xb8\x00\x00'),
            ('C2P port $00B80038',  b'\x00\xb8\x00\x38'),
            ('C2P port $00B8003C',  b'\x00\xb8\x00\x3c'),
            ('ID       $C0DE0000',  b'\xc0\xde\x00\x00')]:
        print('%-25s %6d' % (name, count3(data, pat)))
    # lea $00B80000,aN  =  4xF9 00B8 0000 ; movea.l #$00B80000,aN = 2x7C ...
    for r in range(8):
        op = struct.pack('>H', 0x41F9 | (r << 9))
        c = data.count(op + b'\x00\xb8\x00\x00')
        if c:
            print('  lea $B80000,a%d          %6d' % (r, c))
        op = struct.pack('>H', 0x207C | (r << 9))
        c = data.count(op + b'\x00\xb8\x00\x00')
        if c:
            print('  movea.l #$B80000,a%d     %6d' % (r, c))


def count3(data, pat):
    n, i = 0, 0
    while True:
        i = data.find(pat, i)
        if i < 0:
            break
        n += 1
        i += 1
    return n


def lvo(data):
    """jsr d(a6)  =  4E AE dddd, and jmp d(a6) = 4E EE dddd."""
    h = collections.Counter()
    for op, tag in ((b'\x4e\xae', 'jsr'), (b'\x4e\xee', 'jmp')):
        i = 0
        while True:
            i = data.find(op, i)
            if i < 0 or i + 4 > len(data):
                break
            d = struct.unpack_from('>h', data, i + 2)[0]
            if d < 0:
                h[(tag, d)] += 1
            i += 2
    for (tag, d), n in sorted(h.items(), key=lambda kv: kv[0][1]):
        print('  %s %5d(a6)  %4d' % (tag, d, n))
    print('  total %d' % sum(h.values()))


if __name__ == '__main__':
    mode, path = sys.argv[1], sys.argv[2]
    data = open(path, 'rb').read()
    {'--magic': magic, '--regs': regs, '--akiko': akiko,
     '--lvo': lvo}[mode](data)
