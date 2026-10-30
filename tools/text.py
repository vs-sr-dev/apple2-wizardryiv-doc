"""Parse the compiled text files' record structure.

    0xD7  UWORD id  UWORD length  '[' ... ']'

`length` counts from the `[` to the `]` inclusive plus one, padded to even,
so the next record starts at `here + 5 + length - 1`.  `0xD7 0xFFFF 0x0000`
closes a nested block.  Inside a record, `0xB1` + UWORD plays the speech clip
of that index in the directory's `.LOG`, and the ASCII caret introduces the
generator's control codes.

  text.py FILE            record statistics, and the speech indices used
  text.py FILE --records  every record header, with the first 60 characters

The `--records` form prints game text; it exists so a reader can check the
statistics, not so the script can be lifted.
"""
import sys, struct, collections

REC = 0xD7
SPEECH = 0xB1
END = 0xFFFF


def records(d):
    o = 0
    while True:
        o = d.find(bytes([REC]), o)
        if o < 0 or o + 5 > len(d):
            return
        rid, ln = struct.unpack_from('>HH', d, o + 1)
        if rid == END:
            yield o, rid, ln, b''
            o += 5
            continue
        body = d[o + 5:o + 5 + max(0, ln - 1)]
        if not body.startswith(b'['):
            o += 1                       # a 0xD7 inside a body, not a header
            continue
        yield o, rid, ln, body
        o += 5


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    recs = list(records(d))
    real = [r for r in recs if r[1] != END]
    speech = []
    for o, rid, ln, body in real:
        i = 0
        while True:
            i = body.find(bytes([SPEECH]), i)
            if i < 0 or i + 3 > len(body):
                break
            speech.append(struct.unpack_from('>H', body, i + 1)[0])
            i += 3
    if len(sys.argv) > 2 and sys.argv[2] == '--records':
        for o, rid, ln, body in recs:
            txt = ''.join(chr(c) if 32 <= c < 127 else '.'
                          for c in body[:60])
            print('%08X  id=%-6d len=%-6d %s' % (o, rid, ln, txt))
        sys.exit()
    ids = collections.Counter(r[1] for r in real)
    print('%s  %d bytes' % (sys.argv[1], len(d)))
    print('  %d records, %d block terminators' % (len(real), len(recs) - len(real)))
    print('  ids %d..%d, %d distinct, %d used more than once'
          % (min(ids), max(ids), len(ids),
             sum(1 for v in ids.values() if v > 1)))
    print('  lengths %d..%d, total %d bytes'
          % (min(r[2] for r in real), max(r[2] for r in real),
             sum(r[2] for r in real)))
    print('  %d speech markers, indices %s..%s, %d distinct'
          % (len(speech), min(speech) if speech else '-',
             max(speech) if speech else '-', len(set(speech))))
    carets = d.count(b'^')
    print('  %d caret control introducers, %d "|" alternation separators'
          % (carets, d.count(b'|')))
