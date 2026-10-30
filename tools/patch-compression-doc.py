#!/usr/bin/env python3
"""Add the cross-file duplication coverage figure to docs/06-compression.md, and
say plainly which duplication figures are exhaustive and which are lower bounds.

The exhaustive stride-1 comparison of `alfred` against `intro` was started and
did not finish within the session; rather than quote a number it did not
produce, the document quotes the strided scan's coverage (a lower bound, and
labelled as one) alongside the two duplications that were verified by hand and
are exact.
"""
import io

P = 'docs/06-compression.md'
s = io.open(P, encoding='utf-8').read()

old = """* **`alfred` and `intro` share large runs of identical bytes**, the longest
  verified by hand being **94,417 bytes** (`alfred` 0x03BE9E, `intro` 0x01E5A6)
  — shared engine data between two builds of one code base."""

new = """* **`alfred` and `intro` share large runs of identical bytes**, the longest
  verified by hand being **94,417 bytes** (`alfred` 0x03BE9E, `intro` 0x01E5A6)
  — shared engine data between two builds of one code base, and the region
  containing the raw 8-bit PCM described in `docs/08-audio.md`.

Cross-file duplication coverage, from a window scan at stride 128 restricted to
matches between *different* files:

| file | bytes | shared with another file | share |
|---|---|---|---|
| `/alfred` | 816,616 | ≥ 76,146 | ≥ 9.32 % |
| `/intro` | 255,376 | ≥ 6,423 | ≥ 2.52 % |
| **total** | 1,261,776 | **≥ 82,569** | **≥ 6.54 %** |

Every one of those figures is a **lower bound**, and the reason is the stride
limitation described below: the scan provably misses the largest run on the disc,
so the true coverage is at least 94,417 bytes in `alfred` alone. The two exact
figures on this page are the ones measured directly: `frontend.pak`'s 9,920
bytes, and the 94,417-byte `alfred`/`intro` run. An exhaustive stride-1
comparison was started and did not complete, and no number from it is quoted."""

assert s.count(old) == 1, "duplication anchor not unique"
s = s.replace(old, new, 1)
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print("patched %s" % P)
