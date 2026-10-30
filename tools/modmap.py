#!/usr/bin/env python3
"""Recover the source-module map of /cosm from its HUNK_DEBUG blocks.

/cosm carries 78 debug blocks: one HEADDBGV01 index and 77 HCLN line-number
tables, one per assembler source file.  Each HCLN body is

    ULONG  count            number of line-table entries
    UBYTE  first_line       first source line that produced code
    UBYTE  0
    UWORD  start | 1        module start offset, low bit set as an end marker;
                            if this word reads 0 a ULONG start | 1 follows
    (UBYTE line_delta, UBYTE byte_delta) ...

An offset below 0x19ef8 (the CODE hunk's length) is an offset into hunk 0; a
larger one is an offset into hunk 1, the 119,780-byte chip DATA hunk, and is
hunk-relative rather than cumulative -- verified by decoding the copper lists
at those addresses with tools/copper.py.

The offset recorded is the FIRST byte the module emitted, not its extent: the
line tables show modules are not strictly contiguous, so the trailing figure
below is the distance to the next module's start, not a module size.

The start offsets were verified against the disassembly: MAIN/NVL.S lands on
the nonvolatile.library calls, FUNCTIONS/READJOYPORT.S on the
lowlevel.library ReadJoyPort call.  Modules that emit no CODE-hunk bytes
(copper lists, equate files, tables) store 0.
"""
import sys, struct

d = open(sys.argv[1] if len(sys.argv) > 1 else '_work/files/cosm', 'rb').read()
n = struct.unpack_from('>I', d, 0x3c)[0]
idx = [struct.unpack_from('>I', d, 0x40 + 4 * i)[0] for i in range(n)]
mods = []
for o in idx:
    ln = struct.unpack_from('>I', d, o + 4)[0] * 4
    p = o + 8
    nl = struct.unpack_from('>I', d, p + 8)[0]
    name = d[p + 12:p + 12 + 4 * nl].rstrip(b'\0').decode()
    b = d[p + 12 + 4 * nl:p + ln]
    cnt = struct.unpack_from('>I', b, 0)[0]
    line0 = b[4]
    w = struct.unpack_from('>H', b, 6)[0]
    start = w if w else struct.unpack_from('>I', b, 8)[0]
    mods.append({'name': name, 'entries': cnt, 'first_line': line0,
                 'start': start & ~1, 'dbg_off': o})
CODE_END = 0x19ef8
print('%d modules' % len(mods))
print('%-36s %6s %6s %10s %s' % ('source file', 'lines', 'line0', 'first byte',
                                 '  gap to next'))
placed = sorted(mods, key=lambda m: m['start'])
for i, m in enumerate(placed):
    end = placed[i + 1]['start'] if i + 1 < len(placed) else None
    h = 'code' if m['start'] < CODE_END else 'chip'
    print('%-36s %6d %6d  %s 0x%05x%s' % (m['name'], m['entries'], m['first_line'],
          h, m['start'], '  %d' % (end - m['start']) if end else ''))
