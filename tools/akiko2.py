#!/usr/bin/env python3
"""Akiko scan, all eight address registers -- and, since Power Drive, the
register-relative accesses that no absolute-address scan can see.

The version of this scan carried from the previous discs looked for
`lea $B80000,a0` (41f9) and `movea.l #$B80000,a6` (2c7c) only, and on Universe
that is a false negative: the CD driver loads the base into **a5** (4bf9) and
the NVRAM driver into **a2** (45f9).  A scan that fixes the address register
misses the disc.  Scan all eight forms of both instructions, always.

Reported separately, because they mean different things:

  $B80000 as a base or pointer load   the chip is being driven
  $B80004 / $B80008                   CD-ROM status and interrupt words
  $B80030                             the I2C port for the CD32's serial
                                      EEPROM -- saved games, not graphics
  $B80038 / $B8003C                   the chunky-to-planar data port
  $C0DE0000                           the Akiko identification constant

and the bare byte pattern `00 B8 00 xx`, which is reported for context only:
on this disc every one of its hits outside the two programs is a screen
x-coordinate of 184 in a hotspot table.

THE SECOND LOOK (`--follow`), FROM POWER DRIVE
----------------------------------------------
Once a driver has done `lea $B80000,a5`, the C2P port is `$38(a5)` and
`$3C(a5)`: a displacement, not an address, and the byte pattern `00 B8 00 38`
never appears.  Three discs in the collection drive the CD through such a base
register, and the absolute scan above would have called a `move.l d0,$38(a5)`
on any of them a negative.  `--follow` takes every Akiko load the byte scan
finds and WALKS THE CODE FROM IT: linear flow, plus the targets of bsr/Bcc/
DBcc/bra and of `jsr d16(pc)`, each path ending at rts/rte/jmp/`jsr (An)` or
at the first instruction that writes the base register (lea/movea/adda/
movem-restore/...).  Every (An)/d16(An)/d8(An,Xn) access met on the walk is
reported as the absolute Akiko register it touches.  A dispatch through a
table (`jsr (a3)`) is where the walk stops and says so: the count of
unresolved jumps is printed, and a reader with the disassembly open must
close those by hand.  Two lists come out:

  1. the accesses reached from each load, by absolute register;
  2. every d16(An) access with displacement $38 or $3C anywhere in the file
     (linear sweep, any register): the candidate list a reader closes by
     hand, whatever the walk said.

The selftest builds the controls that must pass before the tool's word is
worth anything: the positive control (`lea $B80000,a5` + `move.l d0,$38(a5)`
MUST be found as a C2P access); the subroutine control (the access sits in a
routine called by bsr AFTER the caller's rts: MUST be found -- this is the
shape of Power Drive's driver, and a linear sweep misses it); the table-walker
control (`lea $440(a5),a5` between them: MUST NOT be attributed); and the
restore control (`movem.l (a7)+,...a5...` between them: MUST NOT).

`--base ADDR` says where the file sits in memory (Power Drive's rboot.bin
copies itself to $28000), so that a `jsr $280CA.l` inside the image is
followed instead of counted as unresolved; a `jsr` outside the image still
stops the path.

Usage: python3 tools/akiko2.py <file> [<file> ...]
       python3 tools/akiko2.py --follow [--base 0x28000] <file> [<file> ...]
       python3 tools/akiko2.py --selftest
"""
import sys, os, re, collections

# lea $xxxxxxxx.l, An   = 4?f9   for An = a0..a7
LEA = {0x41f9: 'a0', 0x43f9: 'a1', 0x45f9: 'a2', 0x47f9: 'a3',
       0x49f9: 'a4', 0x4bf9: 'a5', 0x4df9: 'a6', 0x4ff9: 'a7'}
# movea.l #$xxxxxxxx, An = 2?7c
MOVEA = {0x207c: 'a0', 0x227c: 'a1', 0x247c: 'a2', 0x267c: 'a3',
         0x287c: 'a4', 0x2a7c: 'a5', 0x2c7c: 'a6', 0x2e7c: 'a7'}

AKIKO_LO, AKIKO_HI = 0x00B80000, 0x00B80100

# What the third-party register map calls the offsets (context for the
# reader; the scan does not depend on the names being right).
AKIKO_NAMES = {
    0x00: 'ID', 0x04: 'CDROM_INTREQ', 0x08: 'CDROM_INTENA',
    0x10: 'CDROM_ADDRESS1 (DMA buffer)', 0x14: 'CDROM_ADDRESS2 (cmd/resp buffer)',
    0x18: 'CDROM_SUBCODE', 0x19: 'CDROM_TXINX', 0x1a: 'CDROM_RXINX',
    0x1d: 'CDROM_TXCMP', 0x1f: 'CDROM_RXCMP',
    0x20: 'CDROM_DMA-PBX', 0x24: 'CDROM_CONFIG', 0x28: 'CDROM_PBX',
    0x30: 'I2C port (NVRAM)', 0x38: 'C2P DATA', 0x3c: 'C2P DATA (2)',
}


def u16(b, o):
    return int.from_bytes(b[o:o + 2], 'big')


def u32(b, o):
    return int.from_bytes(b[o:o + 4], 'big')


def scan(path=None, data=None):
    b = data if data is not None else open(path, 'rb').read()
    loads, direct = [], []
    for o in range(0, len(b) - 6, 2):
        w = u16(b, o)
        tab = LEA if w in LEA else (MOVEA if w in MOVEA else None)
        if tab is None:
            continue
        v = u32(b, o + 2)
        if AKIKO_LO <= v < AKIKO_HI:
            loads.append((o, tab[w], v))
    for m in re.finditer(rb'\xc0\xde\x00\x00', b):
        direct.append(('C0DE0000', m.start()))
    counts = {
        'B80038': b.count(b'\x00\xb8\x00\x38'),
        'B8003C': b.count(b'\x00\xb8\x00\x3c'),
        'C0DE0000': len(direct),
        'bare 00B800xx': len(re.findall(rb'\x00\xb8\x00', b)),
    }
    return b, loads, counts


# ----------------------------------------------------------------------
# --follow: walk the code from each Akiko load
# ----------------------------------------------------------------------

WRITERS = ('lea', 'movea', 'adda', 'suba', 'addq', 'subq', 'exg', 'unlk',
           'move', 'movem', 'addi', 'subi', 'add', 'sub')
PATH_END = ('rts', 'rte', 'rtr', 'rtd')


def s8(v):
    return v - 256 if v > 127 else v


def s16(v):
    return v - 65536 if v > 32767 else v


def s32(v):
    return v - (1 << 32) if v >= (1 << 31) else v


def branch_target(addr, b):
    """Target of a Bcc/BRA/BSR/DBcc at addr from its bytes, or None."""
    if len(b) < 2:
        return None
    op = u16(b, 0)
    if (op >> 12) == 6:                       # Bcc.b/.w/.l, BRA, BSR
        disp = op & 0xff
        if disp == 0:
            return addr + 2 + s16(u16(b, 2)) if len(b) >= 4 else None
        if disp == 0xff:
            return addr + 2 + s32(u32(b, 2)) if len(b) >= 6 else None
        return addr + 2 + s8(disp)
    if (op & 0xf0f8) == 0x50c8:               # DBcc
        return addr + 2 + s16(u16(b, 2)) if len(b) >= 4 else None
    return None


def _decoder():
    from capstone import Cs, CS_ARCH_M68K, CS_MODE_M68K_020, CS_MODE_BIG_ENDIAN
    md = Cs(CS_ARCH_M68K, CS_MODE_M68K_020 | CS_MODE_BIG_ENDIAN)
    md.detail = True
    return md


def _mem_base(insn, op, K):
    """Register name of the base of a memory operand, or None."""
    base = op.mem.base_reg
    if not base and op.address_mode in (K.M68K_AM_REGI_ADDR,
                                        K.M68K_AM_REGI_ADDR_POST_INC,
                                        K.M68K_AM_REGI_ADDR_PRE_DEC):
        base = op.reg
    if not base:
        return None
    rn = insn.reg_name(base)
    return rn if rn and rn.startswith('a') else None


def _writes(insn, ops, K):
    """Set of address-register names this instruction writes as a whole."""
    mn = insn.mnemonic.split('.')[0]
    out = set()
    if not ops or mn not in WRITERS:
        return out
    dst = ops[-1]
    if dst.type == K.M68K_OP_REG:
        rn = insn.reg_name(dst.reg)
        if rn and rn.startswith('a'):
            out.add(rn)
    elif dst.type == K.M68K_OP_REG_BITS:
        for i in range(8, 15):
            if dst.register_bits & (1 << i):
                out.add('a%d' % (i - 8))
    return out


def walk(data, load_off, reg, value, limit=200000, base=None):
    """Walk the code from the instruction after the load at load_off.

    Returns (accesses, stops) where accesses = [(off, disp, absolute, text)]
    and stops = Counter of why paths ended ('rts', 'rewrite', 'jmp',
    'jsr-indirect', 'jsr-absolute', 'end of file', 'undecodable', 'limit').
    """
    from capstone import m68k_const as K
    md = _decoder()
    first = next(md.disasm(data[load_off:load_off + 10], load_off), None)
    if first is None:
        return [], collections.Counter({'undecodable': 1})
    work = [load_off + first.size]
    seen = set()
    accesses, stops = [], collections.Counter()
    steps = 0
    while work:
        pc = work.pop()
        while True:
            if pc < 0 or pc >= len(data):
                stops['end of file'] += 1
                break
            if pc in seen:
                break
            seen.add(pc)
            steps += 1
            if steps > limit:
                stops['limit'] += 1
                return accesses, stops
            insn = next(md.disasm(data[pc:pc + 12], pc), None)
            if insn is None:
                stops['undecodable'] += 1
                break
            mn = insn.mnemonic.split('.')[0]
            ops = list(insn.operands)
            text = '%s %s' % (insn.mnemonic, insn.op_str)
            for op in ops:
                if op.type == K.M68K_OP_MEM and _mem_base(insn, op, K) == reg:
                    disp = op.mem.disp
                    if disp >= 0x8000:
                        disp -= 0x10000
                    accesses.append((pc, disp, value + disp, text))
            if reg in _writes(insn, ops, K):
                stops['rewrite'] += 1
                break
            if mn in PATH_END:
                stops['rts'] += 1
                break
            raw = data[pc:pc + insn.size]
            tgt = branch_target(pc, raw)
            if tgt is not None:
                work.append(tgt)
                if mn == 'bra':
                    break
            elif mn == 'jmp':
                stops['jmp'] += 1
                break
            elif mn == 'jsr':
                op = ops[0] if ops else None
                if op is not None and op.type == K.M68K_OP_MEM and \
                        op.address_mode == K.M68K_AM_PCI_DISP:
                    d = op.mem.disp
                    if d >= 0x8000:
                        d -= 0x10000
                    work.append(pc + 2 + d)
                elif op is not None and op.type == K.M68K_OP_MEM and \
                        op.address_mode in (K.M68K_AM_ABSOLUTE_DATA_LONG,
                                            K.M68K_AM_ABSOLUTE_DATA_SHORT):
                    # the absolute target is read from the bytes (Capstone's
                    # printed absolute addresses are not trusted, per dis68k.py)
                    tgt_abs = u32(raw, 2) if insn.size == 6 else s16(u16(raw, 2)) & 0xffffffff
                    if base is not None and base <= tgt_abs < base + len(data):
                        work.append(tgt_abs - base)
                    else:
                        stops['jsr-absolute'] += 1
                else:
                    stops['jsr-indirect'] += 1
            pc += insn.size
    return accesses, stops


def candidates(data):
    """Linear sweep: every d16(An) access with displacement $38 or $3C, any An."""
    from capstone import m68k_const as K
    md = _decoder()
    md.skipdata = True
    out = []
    lastload = {}
    for insn in md.disasm(data, 0):
        if insn.id == 0:
            continue
        ops = list(insn.operands)
        for op in ops:
            if op.type != K.M68K_OP_MEM:
                continue
            rn = _mem_base(insn, op, K)
            if rn is None:
                continue
            disp = op.mem.disp
            if disp >= 0x8000:
                disp -= 0x10000
            if disp in (0x38, 0x3c):
                out.append((insn.address, rn, disp, lastload.get(rn),
                            '%s %s' % (insn.mnemonic, insn.op_str)))
        for rn in _writes(insn, ops, K):
            lastload[rn] = insn.address
    return out


def follow(data, base=None):
    """(per-load results, candidates). per-load: [(off, reg, value, accesses, stops)]"""
    _, loads, _ = scan(data=data)
    res = []
    for off, reg, value in loads:
        acc, stops = walk(data, off, reg, value, base=base)
        res.append((off, reg, value, acc, stops))
    return res, candidates(data)


def report_follow(name, data, base=None):
    res, cands = follow(data, base=base)
    print('=== %s  (%d bytes) ===' % (name, len(data)))
    c2p = 0
    for off, reg, value, acc, stops in res:
        print('-- load at off %d: %s = $%08X; walked %d accesses; paths ended: %s --'
              % (off, reg, value, len(acc),
                 ', '.join('%s %d' % (k, v) for k, v in sorted(stops.items())) or 'none'))
        byabs = collections.Counter(a[2] for a in acc)
        for ab in sorted(byabs):
            first = [a for a in acc if a[2] == ab]
            print('   $%08X  x%-3d %-34s e.g. off %6d  %s'
                  % (ab, byabs[ab], AKIKO_NAMES.get(ab - AKIKO_LO, ''), first[0][0], first[0][3]))
        c2p += sum(1 for a in acc if a[2] in (0xB80038, 0xB8003C))
    if not res:
        print('-- no Akiko load in this file: nothing to walk --')
    print('-- C2P port ($B80038/$B8003C) reached from an Akiko load: %d --' % c2p)
    print('-- displacement $38/$3C on ANY address register (linear sweep): %d candidates --' % len(cands))
    for off, rn, disp, lo, text in cands:
        what = ('last write to %s at off %d' % (rn, lo)) if lo is not None else ('%s never written before' % rn)
        print('   off %6d  $%02X(%s)  %-36s %s' % (off, disp, rn, text, what))
    print()
    return c2p, len(cands)


def selftest():
    fails = 0

    def check(name, ok):
        nonlocal fails
        print('  %-76s %s' % (name, 'ok' if ok else 'FAIL'))
        if not ok:
            fails += 1

    def hits(data):
        res, cands = follow(data)
        return [a for r in res for a in r[3]], cands

    # positive control: lea $B80000,a5 ; move.l d0,$38(a5) ; rts
    a, c = hits(bytes.fromhex('4bf900b80000' '2b400038' '4e75'))
    check('positive control: $38(a5) after lea $B80000,a5 is a C2P access',
          any(x[2] == 0xB80038 for x in a))
    check('positive control: it is also a $38 candidate naming its load',
          len(c) == 1 and c[0][3] == 0)
    # subroutine control: lea ; bsr sub ; rts ; sub: move.l d0,$38(a5) ; rts
    a, c = hits(bytes.fromhex('4bf900b80000' '6102' '4e75' '2b400038' '4e75'))
    check('subroutine control: $38(a5) in a bsr target after the caller rts IS found',
          any(x[2] == 0xB80038 for x in a))
    # table-walker control: lea $B80000,a5 ; lea $440(a5),a5 ; move.l d0,$38(a5)
    a, c = hits(bytes.fromhex('4bf900b80000' '4bed0440' '2b400038' '4e75'))
    check('table-walker control: $38(a5) after lea $440(a5),a5 is NOT attributed',
          not any(x[2] == 0xB80038 for x in a))
    check('table-walker control: it stays a candidate for the reader', len(c) == 1)
    # restore control: lea ; movem.l (a7)+,d0-d7/a0-a6 ; move.l d0,$38(a5)
    a, c = hits(bytes.fromhex('4bf900b80000' '4cdf7fff' '2b400038' '4e75'))
    check('restore control: $38(a5) after movem.l (a7)+,...a5... is NOT attributed',
          not any(x[2] == 0xB80038 for x in a))
    # unreachable control: lea ; rts ; move.l d0,$38(a5)   (no path leads there)
    a, c = hits(bytes.fromhex('4bf900b80000' '4e75' '2b400038'))
    check('unreachable control: $38(a5) after rts with no branch to it is NOT attributed',
          not any(x[2] == 0xB80038 for x in a) and len(c) == 1)
    # movea + indirect on a2 = $B80030
    a, c = hits(bytes.fromhex('247c00b80030' '1480' '4e75'))
    check('movea.l #$B80030,a2 ; move.b d0,(a2) resolves to $B80030',
          any(x[2] == 0xB80030 for x in a))
    # jsr d16(pc) is followed
    # lea at 0..5, jsr at 6 (target = 6 + 2 + 4 = 12), rts at 10, move at 12
    a, c = hits(bytes.fromhex('4bf900b80000' '4eba0004' '4e75' '2b40003c' '4e75'))
    check('jsr d16(pc) is followed: $3C(a5) in its target is found',
          any(x[2] == 0xB8003C for x in a))
    # jsr abs.l inside the image is followed when --base says where the image is
    # lea at 0..5, jsr $28010.l at 6 (image at $28000: target off 16), rts at 12,
    # pad at 14, move at 16
    img = bytes.fromhex('4bf900b80000' '4eb900028010' '4e75' '4e71' '2b400038' '4e75')
    res, c = follow(img, base=0x28000)
    check('jsr $28010.l with --base 0x28000 is followed to offset 16',
          any(a[2] == 0xB80038 for r in res for a in r[3]))
    res, c = follow(img)
    check('the same jsr without --base stops the path (jsr-absolute 1)',
          not any(a[2] == 0xB80038 for r in res for a in r[3]) and res[0][4]['jsr-absolute'] == 1)
    # the byte scan sees neither of the two files as a $B80038 pattern
    _, _, counts = scan(data=bytes.fromhex('4bf900b80000' '2b400038' '4e75'))
    check('byte scan: 00 B8 00 38 absent from the positive control (why --follow exists)',
          counts['B80038'] == 0)
    # empty input
    res, c = follow(b'')
    check('empty input: nothing found, no crash', res == [] and c == [])
    # loop does not hang: lea ; bra self
    a, c = hits(bytes.fromhex('4bf900b80000' '60fe'))
    check('a branch to itself terminates', True)
    # the absolute scan still finds all eight registers
    for w, rn in LEA.items():
        _, loads, _ = scan(data=w.to_bytes(2, 'big') + (0xB80000).to_bytes(4, 'big') + b'\x4e\x75')
        check('absolute scan: lea $B80000,%s found' % rn, bool(loads) and loads[0][1] == rn)
    print('%d checks, %d failures' % (14 + len(LEA), fails))
    return fails


def main():
    args = sys.argv[1:]
    if args and args[0] == '--selftest':
        sys.exit(1 if selftest() else 0)
    if args and args[0] == '--follow':
        tc2p = tc = 0
        base = None
        files = args[1:]
        if files and files[0] == '--base':
            base = int(files[1], 0)
            files = files[2:]
        for p in files:
            c2p, cands = report_follow(os.path.basename(p), open(p, 'rb').read(), base=base)
            tc2p += c2p
            tc += cands
        print('TOTAL  C2P reached from an Akiko load: %d   $38/$3C candidates on any register: %d' % (tc2p, tc))
        return
    total = collections.Counter()
    allloads = []
    for p in args:
        b, loads, counts = scan(p)
        for k, v in counts.items():
            total[k] += v
        for o, reg, v in loads:
            allloads.append((os.path.basename(p), o, reg, v))
    print('=== Akiko base/pointer loads (all 8 address registers) ===')
    if not allloads:
        print('  none')
    for name, o, reg, v in allloads:
        print('  %-24s off %6d  lea/movea $%08X, %s' % (name, o, v, reg))
    print()
    print('=== byte-pattern counts (context only) ===')
    for k in ('B80038', 'B8003C', 'C0DE0000', 'bare 00B800xx'):
        print('  %-14s %d' % (k, total[k]))


if __name__ == '__main__':
    main()
