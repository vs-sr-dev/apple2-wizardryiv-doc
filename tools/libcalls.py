"""Resolve  jsr d(a6)  calls to the library that is actually in A6.

`captiveII` keeps every library base in one A5-relative globals block, so a
call site reads

    movea.l  $3350(a5),a6        ; the base
    jsr      -30(a6)             ; the vector

and the base displacement identifies the library.  This walks the code
linearly, remembers the last thing loaded into A6 (an A5 displacement, an
absolute address, or `$4.w` for exec) and attributes each vector call to it.
Calls whose A6 was set out of view are reported as unknown, which is the
honest answer rather than a guess.

Usage: libcalls.py <hunkfile> [name=disp ...]
       libcalls.py captiveII dos=0x150 exec=0x154 ...
"""
import sys, struct, collections
from hunk import parse
from lvo import LIBS

MOVEA_A5_A6 = 0x2C6D     # movea.l  d16(a5),a6
MOVEA_ABS_A6 = 0x2C79    # movea.l  abs.L,a6
MOVEA_W_A6 = 0x2C78      # movea.l  abs.W,a6   ($4.w -> exec)
LEA_PC_A6 = 0x4DFA       # lea      d16(pc),a6
JSR_A6 = 0x4EAE
JMP_A6 = 0x4EEE


def resolve(body):
    """-> Counter[(base_tag, lvo)] plus a Counter of bases seen."""
    calls = collections.Counter()
    a6 = None
    i = 0
    n = len(body)
    while i + 2 <= n:
        op = struct.unpack_from('>H', body, i)[0]
        if op == MOVEA_A5_A6 and i + 4 <= n:
            a6 = 'a5+0x%X' % (struct.unpack_from('>h', body, i + 2)[0] & 0xFFFF)
            i += 4
            continue
        if op == MOVEA_W_A6 and i + 4 <= n:
            w = struct.unpack_from('>H', body, i + 2)[0]
            a6 = 'exec' if w == 4 else 'abs.w $%X' % w
            i += 4
            continue
        if op == MOVEA_ABS_A6 and i + 6 <= n:
            a6 = 'abs $%X' % struct.unpack_from('>I', body, i + 2)[0]
            i += 6
            continue
        if op in (JSR_A6, JMP_A6) and i + 4 <= n:
            v = struct.unpack_from('>h', body, i + 2)[0]
            if -1200 < v < 0:
                calls[(a6 or '?', v)] += 1
                i += 4
                continue
        i += 2
    return calls


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    h = parse(d)
    body = b''.join(d[k['off']:k['off'] + k['size']] for k in h['hunks']
                    if k['size'])
    names = {}
    for a in sys.argv[2:]:
        k, v = a.split('=')
        names['a5+0x%X' % int(v, 0)] = k
    calls = resolve(body)
    tab = dict(LIBS)
    by_base = collections.Counter()
    for (base, v), c in calls.items():
        by_base[names.get(base, base)] += c
    print('calls by A6 source:')
    for b, c in by_base.most_common():
        print('  %-14s %4d' % (b, c))
    print()
    for base in sorted({names.get(b, b) for b, v in calls}):
        rows = [(v, c) for (b, v), c in calls.items()
                if names.get(b, b) == base]
        print('%s  (%d calls, %d vectors)'
              % (base, sum(c for _, c in rows), len(rows)))
        for v, c in sorted(rows):
            nm = tab.get(base, {}).get(v, '')
            alt = '' if nm else '  '.join(
                '%s:%s' % (n, t[v]) for n, t in LIBS if v in t)
            print('   %5d(a6) x%-4d %s' % (v, c, nm or alt))
