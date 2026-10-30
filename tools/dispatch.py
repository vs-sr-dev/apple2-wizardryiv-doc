#!/usr/bin/env python3
"""Find Universe's bytecode dispatch tables and count their opcodes.

The engine's interpreters all have the same shape, and it is the shape a
dispatch table has when the table is *inline*, immediately after the code that
jumps into it:

    lea.l   $12(pc), a6      ; a6 = the table, 0x12 bytes ahead
    neg.b   d0               ; opcode byte -> index (the opcodes are stored
    subq.w  #1, d0           ;   complemented, so 0xFF is index 0)
    andi.w  #$ff, d0
    asl.w   #2, d0           ; four bytes per entry
    jsr     (a6, d0.w)
    rts
    bra.w   handler0         ; <- the table starts here
    bra.w   handler1
    ...

So the opcode count is not stored anywhere: it is the length of the run of
`bra.w` instructions that follows the table's address, and it ends at the first
word that is not `0x6000`.  That is exact -- every entry in every table found
here is a `bra.w`, with no padding and no filler entry.

Usage: python3 tools/dispatch.py <file> [--base N]
"""
import sys, argparse

LEA_PC = {0x41fa: 'a0', 0x43fa: 'a1', 0x45fa: 'a2', 0x47fa: 'a3',
          0x49fa: 'a4', 0x4bfa: 'a5', 0x4dfa: 'a6'}
IDX_JSR = {0x4eb0: 'a0', 0x4eb1: 'a1', 0x4eb2: 'a2', 0x4eb3: 'a3',
           0x4eb4: 'a4', 0x4eb5: 'a5', 0x4eb6: 'a6', 0x4eb7: 'a7'}
IDX_JMP = {0x4ef0: 'a0', 0x4ef1: 'a1', 0x4ef2: 'a2', 0x4ef3: 'a3',
           0x4ef4: 'a4', 0x4ef5: 'a5', 0x4ef6: 'a6', 0x4ef7: 'a7'}


def u16(b, o):
    return int.from_bytes(b[o:o + 2], 'big')


def s16(v):
    return v - 65536 if v > 32767 else v


def table_len(b, at):
    """Length of the run of bra.w entries starting at `at`."""
    n = 0
    while at + 4 <= len(b) and u16(b, at) == 0x6000:
        n += 1
        at += 4
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file')
    ap.add_argument('--base', type=lambda s: int(s, 0), default=0,
                    help='address of byte 0, for printing')
    args = ap.parse_args()
    b = open(args.file, 'rb').read()

    found = []
    for o in range(0, len(b) - 8, 2):
        w = u16(b, o)
        if w not in LEA_PC:
            continue
        reg = LEA_PC[w]
        disp = s16(u16(b, o + 2))
        target = o + 2 + disp
        # look ahead a few instructions for an indexed jsr/jmp on this register
        for k in range(o + 4, min(o + 40, len(b) - 2), 2):
            w2 = u16(b, k)
            hit = (IDX_JSR.get(w2) == reg and 'jsr') or \
                  (IDX_JMP.get(w2) == reg and 'jmp')
            if not hit:
                continue
            n = table_len(b, target)
            if n >= 4:
                ext = u16(b, k + 2)
                idxreg = 'd%d' % ((ext >> 12) & 7)
                found.append((o, k, hit, reg, idxreg, target, n))
            break

    print('%-8s %-8s %-4s %-3s %-3s %-8s %s' %
          ('lea@', 'jump@', 'kind', 'An', 'Dn', 'table@', 'opcodes'))
    for o, k, hit, reg, idxreg, target, n in found:
        print('%08x %08x %-4s %-3s %-3s %08x %d' %
              (args.base + o, args.base + k, hit, reg, idxreg,
               args.base + target, n))
    print()
    print('=== every run of >=6 consecutive bra.w, found without reference to')
    print('    the code that jumps into it ===')
    runs = []
    o = 0
    while o < len(b) - 4:
        if u16(b, o) == 0x6000:
            s0, n = o, 0
            while o < len(b) - 4 and u16(b, o) == 0x6000:
                n += 1
                o += 4
            if n >= 6:
                runs.append((s0, n))
        else:
            o += 2
    for s0, n in runs:
        tg = set(s0 + 4 * i + 2 + s16(u16(b, s0 + 4 * i + 2)) for i in range(n))
        print('  table %08x  %3d entries  %3d distinct handlers' %
              (args.base + s0, n, len(tg)))
    print()
    print('dispatch tables: %d' % len(found))
    print('opcodes total  : %d' % sum(f[6] for f in found))
    for o, k, hit, reg, idxreg, target, n in found:
        tgts = sorted(set(target + 4 * i + 2 + s16(u16(b, target + 4 * i + 2))
                          for i in range(n)))
        print('table %08x: %d entries, %d distinct handlers' %
              (args.base + target, n, len(tgts)))


if __name__ == '__main__':
    main()
