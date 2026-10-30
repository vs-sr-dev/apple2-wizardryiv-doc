"""The manual-lookup copy protection of the CD32 release, reimplemented.

The number the game asks for is not stored anywhere on the disc.  It is
computed from the table letter, row and column by the routine at offset
0xA624 of the decrunched Speris-Options overlay, from 42 coefficient bytes
at 0xA694 -- six per table, seven tables:

    s = A*(r^2 * c) + B*(c^2 * r) + C*(r*c) + D*r + E*c + F
    code = 999 - (s mod 700)

r is the printed row (1..50) and c the printed column letter (A..Q -> 1..17).
Every multiply is a 68000 MULU.W, so each intermediate is truncated to 16
bits before the next one; reproducing that truncation is what makes the
numbers come out right.  The range 300..999 falls straight out of the
constants 700 and 999.
"""
import sys

def coefficients(path='_work/unpacked/Speris-Options', base=0xA694):
    b = open(path, 'rb').read()[base:base+42]
    return [[b[k*7 + i] for k in range(6)] for i in range(7)]

def code(coef, tbl, row, col):
    A, B, C, D, E, F = coef[tbl]
    m = lambda x, y: (x & 0xFFFF) * y
    s  = m(m(row * row, col), A)
    s += m(m(col * col, row), B)
    s += m(row * col, C)
    s += D * row
    s += E * col
    s += F
    rem = (s >> 16) & 0xFFFF if s // 700 > 0xFFFF else s % 700   # DIVU.W overflow
    return 999 - rem

def table(coef, tbl):
    return [[code(coef, tbl, r, c) for c in range(1, 18)] for r in range(1, 51)]

if __name__ == '__main__':
    coef = coefficients()
    which = sys.argv[1] if len(sys.argv) > 1 else 'A'
    for w in (which if which != 'all' else 'ABCDEFG'):
        t = 'ABCDEFG'.index(w)
        print('TABLE %s   coefficients A..F = %s' % (w, ' '.join(map(str, coef[t]))))
        print('     ' + ' '.join('%4s' % c for c in 'ABCDEFGHIJKLMNOPQ'))
        for r, row in enumerate(table(coef, t), 1):
            print('%3d  ' % r + ' '.join('%4d' % v for v in row))
        print()
