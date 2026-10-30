#!/usr/bin/env python3
"""Every `io_Command` write, attributed to the IORequest it is written into.

Section 8 of the platform checklist: an `io_Command` histogram is only
readable once you know how many devices were opened and which request each
command lands in. This finds

    move.w  #imm, $1c(An)      33 7c iiii 001c        (An = a1 here: 33 7c)
    move.w  #imm, $1c(An)      for every address register
    move.w  Dn,   $1c(An)      33 4n 001c  / 3n 40 ...

and, for the immediate form, prints the three neighbouring field writes
(io_Length $24, io_Data $28, io_Offset $2c) that the CD32 commands use, so a
`CD_PLAYTRACK` can be read as "which track" rather than as a bare number.

cd.device command numbers, per the checklist's own table:
   9 CMD_STOP  10 CMD_START  32 CD_INFO  33 CD_CONFIG  34 CD_TOCMSF
  35 CD_TOCLSN 36 CD_READXL  37 CD_PLAYTRACK  38 CD_PLAYMSF  39 CD_PLAYLSN
  40 CD_PAUSE  41 CD_SEARCH  42 CD_QCODEMSF  43 CD_QCODELSN  44 CD_ATTENUATE
  45 CD_ADDFRAMEINT  46 CD_REMFRAMEINT

Usage:  python tools/iocmd.py <file> [...]
"""
import sys, re, struct, collections

CMD = {1: 'CMD_RESET', 2: 'CMD_READ', 3: 'CMD_WRITE', 4: 'CMD_UPDATE',
       5: 'CMD_CLEAR', 6: 'CMD_STOP', 7: 'CMD_START', 8: 'CMD_FLUSH',
       9: 'IND_ADDHANDLER/CD?', 10: 'IND_REMHANDLER/CD?',
       32: 'CD_INFO', 33: 'CD_CONFIG', 34: 'CD_TOCMSF', 35: 'CD_TOCLSN',
       36: 'CD_READXL', 37: 'CD_PLAYTRACK', 38: 'CD_PLAYMSF',
       39: 'CD_PLAYLSN', 40: 'CD_PAUSE', 41: 'CD_SEARCH',
       42: 'CD_QCODEMSF', 43: 'CD_QCODELSN', 44: 'CD_ATTENUATE'}

# move.w #imm,$1c(An)  =  3?7c iiii 001c   with ? = 8|An for (An) dest d16
# encoding: 0011 rrr 001 111 100  -> 33 7c for a1 ... general: 0x30 | (An<<9) ...
AN = {0x31: 'a0', 0x33: 'a1', 0x35: 'a2', 0x37: 'a3',
      0x39: 'a4', 0x3b: 'a5', 0x3d: 'a6', 0x3f: 'a7'}


def main():
    for p in sys.argv[1:]:
        d = open(p, 'rb').read()
        hits = []
        for hi, an in AN.items():
            pat = re.compile(re.escape(bytes([hi, 0x7c])) + b'(..)' + b'\x00\x1c',
                             re.S)
            for m in pat.finditer(d):
                imm = struct.unpack('>H', m.group(1))[0]
                hits.append((m.start(), an, imm))
        hits.sort()
        print("=== %s : %d immediate io_Command writes ===" % (p, len(hits)))
        h = collections.Counter(x[2] for x in hits)
        for v, n in sorted(h.items()):
            print("   %3d (0x%02x) x%-3d %s" % (v, v, n, CMD.get(v, '')))
        print("   --- sites, with the three fields written near each ---")
        for off, an, imm in hits:
            ctx = d[max(0, off - 40):off + 60]
            fields = {}
            for fo, name in ((0x24, 'io_Length'), (0x28, 'io_Data'),
                             (0x2c, 'io_Offset')):
                # move.l #imm,fo(An)  = 2?7c iiiiiiii 00fo
                mm = re.search(re.escape(bytes([{'a0': 0x21, 'a1': 0x23, 'a2': 0x25,
                                                 'a3': 0x27, 'a4': 0x29, 'a5': 0x2b,
                                                 'a6': 0x2d, 'a7': 0x2f}[an], 0x7c]))
                               + b'(....)' + re.escape(bytes([0x00, fo])), ctx, re.S)
                if mm:
                    fields[name] = "#$%x" % struct.unpack('>I', mm.group(1))[0]
                    continue
                # move.l abs.l,fo(An) = 2?79 aaaaaaaa 00fo
                mm = re.search(re.escape(bytes([{'a0': 0x21, 'a1': 0x23, 'a2': 0x25,
                                                 'a3': 0x27, 'a4': 0x29, 'a5': 0x2b,
                                                 'a6': 0x2d, 'a7': 0x2f}[an], 0x79]))
                               + b'(....)' + re.escape(bytes([0x00, fo])), ctx, re.S)
                if mm:
                    fields[name] = "$%x.l" % struct.unpack('>I', mm.group(1))[0]
                    continue
                # clr.l fo(An) = 42a9 00fo (a1) etc
                mm = re.search(re.escape(bytes([0x42, 0xa8 + {'a0': 0, 'a1': 1, 'a2': 2,
                                                              'a3': 3, 'a4': 4, 'a5': 5,
                                                              'a6': 6, 'a7': 7}[an],
                                                0x00, fo])), ctx)
                if mm:
                    fields[name] = "0"
            print("   0x%06x  %s  cmd %3d %-14s %s"
                  % (off, an, imm, CMD.get(imm, ''),
                     '  '.join("%s=%s" % kv for kv in fields.items())))


if __name__ == '__main__':
    main()
