#!/usr/bin/env python3
"""Repair tools/rawsectors.py after a shell heredoc ate a backslash escape.

Writing the patch as a file rather than passing it inline is the lesson the Myth
session left: this shell mangles long heredocs, and a `\\x00` written inline
arrived in the file as a literal NUL byte, which Python then refused to parse.
Both anchors are asserted unique; if either is not, nothing is written.
"""
import io

P = 'tools/rawsectors.py'
data = io.open(P, 'rb').read()

# 1. the literal NUL that the heredoc produced, back to an escape
bad = b"    tail = b[:off] if b is not None else b'\x00' * off\n"
good = b"    tail = b[:off] if b is not None else bytes(off)\n"
assert data.count(bad) == 1, "NUL anchor is not unique (%d)" % data.count(bad)
data = data.replace(bad, good)

# 2. count sector modes in the single-sector fallback path too, so that a run
#    that falls back for every sector does not report an empty mode census
bad2 = b"""                a = analyse(b1, lba + j)
                if fh:
                    fh.write(a['user'] if cmd == 'dump' else a['full'])
"""
good2 = b"""                a = analyse(b1, lba + j)
                modes[a['mode']] = modes.get(a['mode'], 0) + 1
                if not a['sync']:
                    bad_sync += 1
                if not a['edc_ok']:
                    bad_edc += 1
                if not a['lba_ok']:
                    bad_lba += 1
                if fh:
                    fh.write(a['user'] if cmd == 'dump' else a['full'])
"""
assert data.count(bad2) == 1, "fallback anchor is not unique (%d)" % data.count(bad2)
data = data.replace(bad2, good2)

# 3. bad_sync/bad_edc/bad_lba are assigned in the fallback, so they must be
#    module-level-free locals of main(); they already are.  Nothing to do.

io.open(P, 'wb').write(data)
print("patched %s: %d bytes" % (P, len(data)))
