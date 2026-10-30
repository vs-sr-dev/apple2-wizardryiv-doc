# -*- coding: utf-8 -*-
"""Third [Myth] patch: the counts this document quotes but did not add.

The instruction that produced this file: re-read the numbers you cite, not only
the ones you insert. A figure frozen two discs ago is indistinguishable from a
measured one.

Usage: python3 tools/patch-myth3.py cd32-platform-notes.md [README.md]
"""
import io, sys

NOTES = [
 ("""next and added to by each. It currently rests on **fifteen discs**, so much of it
is still marked with the title it came from: treat it as a list of things to
*test*, not a list of things that are true of the format.

One of the fifteen is the **CDTV release of a title whose CD32 release is also
here**,""",
  """next and added to by each. It currently rests on **seventeen discs**, so much of
it is still marked with the title it came from: treat it as a list of things to
*test*, not a list of things that are true of the format.

One of the seventeen is the **CDTV release of a title whose CD32 release is also
here**,"""),

 ("""### On CD32-era discs: fourteen discs, the same bytes""",
  """### On CD32-era discs: fifteen discs, the same bytes"""),

 ("""**And one CD32-era disc has none of it.** See the correction below before
treating those three hashes as anything more than ten sightings of one
widely-copied file. The score is now **ten discs with the Commodore banner
and one with the CDTV driver** — which is worth keeping in that form, because
it is the ratio, not the identity, that this section is actually measuring.""",
  """**And one CD32-era disc has none of it.** See the correction below before
treating those three hashes as anything more than fifteen sightings of one
widely-copied file. The score is now **fifteen discs with the Commodore banner
and one with the CDTV driver** — which is worth keeping in that form, because
it is the ratio, not the identity, that this section is actually measuring.
(This line read "ten and one" for four discs after it stopped being true. The
count is now re-derived from the disc list at the top of the document rather
than incremented, and the same should be done to it next time.)"""),

 ("""    | `.TM` block | the common 2,048 B | identical | **identical** | matches, fourteen discs have it |""",
  """    | `.TM` block | the common 2,048 B | identical | **identical** | matches, fifteen discs have it |"""),
]

README = [
 ("""| 10 | Baselines, disc by disc, side by side — **sixteen columns**, and the size band now stated as an on-disc measurement after a same-label pair pinned down which of three numbers it was ever measuring |""",
  """| 10 | Baselines, disc by disc, side by side — **seventeen columns**, and the size band now stated as an on-disc measurement after a same-label pair pinned down which of three numbers it was ever measuring |"""),
]


def apply(path, edits):
    s = io.open(path, encoding='utf-8').read()
    n = len(s)
    for i, (a, b) in enumerate(edits):
        c = s.count(a)
        if c != 1:
            raise SystemExit("%s EDIT %d: anchor found %d times:\n  %r" % (path, i, c, a[:80]))
        s = s.replace(a, b, 1)
        print("  %s edit %d ok" % (path, i))
    io.open(path, 'w', encoding='utf-8', newline='\n').write(s)
    print("  wrote %s: %d -> %d" % (path, n, len(s)))


def main():
    apply(sys.argv[1] if len(sys.argv) > 1 else 'cd32-platform-notes.md', NOTES)
    if len(sys.argv) > 2:
        apply(sys.argv[2], README)


if __name__ == '__main__':
    main()
