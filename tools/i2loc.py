#!/usr/bin/env python3
"""i2loc.py -- the text of a Unity game that keeps it in ONE MonoBehaviour:
I2 Localization's LanguageSource, read from a hex dump at format 22 and
closed twice.

WHAT THE LAYOUT IS, AND WHERE IT WAS READ
-----------------------------------------
On pc-celltosingularity-doc every string of the game -- 10,249 terms in 19
languages, 23,160,144 bytes -- sits in one MonoBehaviour named `I2Languages`
in `resources.assets`. There is no type tree in a player build, so the layout
below is what `_work/hexobj.py` showed, field by field, and what this reader
walks; nothing of it comes from I2's source code. Offsets are from the start
of the object's body:

    +0    PPtr   m_GameObject        i32 fileID, i64 pathID (12 bytes, zero)
    +12   u8     m_Enabled           1, then 3 bytes of alignment
    +16   PPtr   m_Script            i32 fileID, i64 pathID
    +28   astr   m_Name              `I2Languages` (aligned string: i32 length,
                                     bytes, pad to 4)
    +44   u32 x3 three words         0, 0, 1 on this object -- read, not named
    +56   i32    term count          10,249
          TERM x count:
            astr   key               `tech_steam_engine`, `dino_...`, ...
            i32    term type         0 on every one of the 10,249
            i32    n1 = 19, then n1 aligned strings: the translations, in
                                     the order of the language list below
            i32    n2 = 19, then n2 bytes (flags), padded to 4
            u32    a trailing word   0 on every term
          u32 x2 two words           1, 1 on this object
          astr   a term key          (`app_title`)
          i32    language count      19
          LANGUAGE x count:
            astr   name              `English` ... `Vietnamese`
            astr   code              `en` ... `vi`
            u32    a word            0 on all 19
          u32    a word              0
          i32    a count             2 (of the strings that follow?) -- read,
                                     not named
          astr   a web-service URL   COUNTED AND REDACTED by this tool
          astr   a key               COUNTED AND REDACTED by this tool
          astr   a title             the sync sheet's title
          astr   a number            13 decimal digits: a Unix time in ms
          u32 x3, f32, u32           1, 1, 1, 5.0, 0 -- read, not named
    = end of the body, exactly

TWO CLOSURES: the term count is reached with every term parsed at the same
shape (the type, n1, n2 and trailing-word histograms are printed so that a
term of another shape would show), and the last field ends on the body's last
byte. A body that does not close both ways is refused.

WHAT IT PRINTS AND WHAT IT DOES NOT
-----------------------------------
`census` prints counts: terms, languages by name and code, cells filled and
empty per language, terms by key prefix (the family before the first `_`),
the translators' notes (the terms whose key begins `I2_colorcode`: they are
notes about the process, not the game), length statistics. `sample` prints
a few terms with their English cell, chosen by rule (the first term of each
of the N largest families), so that a reader sees what a term is without the
table. `table --out FILE` writes the whole 10,249 x 19 table as TSV -- to
`_work/`, never to the repository: the table IS the game's text and is the
studio's. The web-service URL and the key in the tail are never printed:
their lengths are.

    python tools/i2loc.py census FILE.assets [--name I2Languages | --pathid N]
    python tools/i2loc.py sample FILE.assets [--families 12]
    python tools/i2loc.py table  FILE.assets --out _work/i2-table.tsv
    python tools/i2loc.py selftest

The object is selected by the SerializedFile's own header (unityfs.py) and
then by the MonoBehaviour's m_Name; `--pathid` names it directly.
"""
import argparse
import collections
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dirguard   # noqa: E402
import nameguard  # noqa: E402
import unityfs    # noqa: E402


class LayoutError(ValueError):
    pass


class R(object):
    def __init__(self, b):
        self.b = b
        self.p = 0

    def need(self, n):
        if self.p + n > len(self.b):
            raise LayoutError("read of %d past the body's end at %d (body %d)"
                              % (n, self.p, len(self.b)))

    def i32(self):
        self.need(4)
        v = struct.unpack_from("<i", self.b, self.p)[0]
        self.p += 4
        return v

    def u32(self):
        self.need(4)
        v = struct.unpack_from("<I", self.b, self.p)[0]
        self.p += 4
        return v

    def f32(self):
        self.need(4)
        v = struct.unpack_from("<f", self.b, self.p)[0]
        self.p += 4
        return v

    def align(self):
        self.p = (self.p + 3) & ~3

    def astr(self):
        n = self.i32()
        if n < 0 or n > 1 << 24:
            raise LayoutError("string length %d at %d is not credible"
                              % (n, self.p - 4))
        self.need(n)
        s = self.b[self.p:self.p + n]
        self.p += n
        self.align()
        return s.decode("utf-8", "replace")


class Source(object):
    """One parsed LanguageSource body."""

    def __init__(self, body):
        r = R(body)
        self.body_len = len(body)
        r.p = 28
        self.name = r.astr()
        self.head_words = [r.u32() for _ in range(3)]
        n = r.i32()
        if n < 0 or n > 1 << 20:
            raise LayoutError("term count %d is not credible" % n)
        self.terms = []            # (key, type, [cells], flags bytes, tail)
        self.shape = collections.Counter()
        for i in range(n):
            key = r.astr()
            tt = r.i32()
            n1 = r.i32()
            if n1 < 0 or n1 > 256:
                raise LayoutError("term %d (%s): %d translations is not "
                                  "credible" % (i, key, n1))
            cells = [r.astr() for _ in range(n1)]
            n2 = r.i32()
            if n2 < 0 or n2 > 256:
                raise LayoutError("term %d (%s): %d flags is not credible"
                                  % (i, key, n2))
            r.need(n2)
            flags = bytes(r.b[r.p:r.p + n2])
            r.p += n2
            r.align()
            tail = r.u32()
            self.shape[(tt, n1, n2, tail)] += 1
            self.terms.append((key, tt, cells, flags, tail))
        self.terms_end = r.p
        self.mid_words = [r.u32(), r.u32()]
        self.mid_key = r.astr()
        nl = r.i32()
        if nl < 0 or nl > 256:
            raise LayoutError("language count %d is not credible" % nl)
        self.languages = []        # (name, code, word)
        for _ in range(nl):
            self.languages.append((r.astr(), r.astr(), r.u32()))
        self.tail_word = r.u32()
        self.tail_count = r.i32()
        self.tail_url = r.astr()
        self.tail_key = r.astr()
        self.tail_title = r.astr()
        self.tail_number = r.astr()
        self.tail_words = [r.u32(), r.u32(), r.u32()]
        self.tail_float = r.f32()
        self.tail_last = r.u32()
        self.end = r.p
        if self.end != self.body_len:
            raise LayoutError("the last field ends at %d and the body at %d: "
                              "the layout does not close" % (self.end,
                                                              self.body_len))
        widths = {n1 for _t, n1, _n2, _w in self.shape}
        if widths != {nl}:
            raise LayoutError("terms carry %s translations but the language "
                              "list has %d" % (sorted(widths), nl))

    # -- counts ------------------------------------------------------------
    def per_language(self):
        """(filled, empty) per language column."""
        out = []
        for j in range(len(self.languages)):
            filled = sum(1 for t in self.terms if t[2][j] != "")
            out.append((filled, len(self.terms) - filled))
        return out

    def families(self):
        fam = collections.Counter()
        for key, _t, _c, _f, _w in self.terms:
            fam[key.split("_", 1)[0] if "_" in key else "(no underscore)"] += 1
        return fam

    def notes(self):
        return [(k, c[0]) for k, _t, c, _f, _w in self.terms
                if k.startswith("I2_colorcode")]


def find_object(sf, name=None, pathid=None):
    if pathid is not None:
        for o in sf.objects:
            if o["path_id"] == pathid:
                return o
        raise LayoutError("no object with path id %d" % pathid)
    hits = []
    for o in sf.objects:
        if sf.class_of(o) != 114:
            continue
        b = sf.body(o)
        if len(b) < 48:
            continue
        n = struct.unpack_from("<i", b, 28)[0]
        if 0 < n < 64 and b[32:32 + n] == name.encode("utf-8"):
            hits.append(o)
    if len(hits) != 1:
        raise LayoutError("%d MonoBehaviours named %r (need exactly one)"
                          % (len(hits), name))
    return hits[0]


def load_source(path, name, pathid):
    dirguard.want_file(path, "i2loc")
    if not unityfs.is_serialized(path):
        sys.exit("i2loc: %s is not a Unity SerializedFile by its header"
                 % os.path.basename(path))
    sf = unityfs.load(path)
    o = find_object(sf, name, pathid)
    return sf, o, Source(sf.body(o))


def cmd_census(a):
    sf, o, s = load_source(a.path, a.name, a.pathid)
    print("file          : %s   format %d" % (os.path.basename(a.path),
                                              sf.version))
    print("object        : path id %d   class %d   body %d bytes   m_Name %s"
          % (o["path_id"], sf.class_of(o), s.body_len, s.name))
    print("head words    : %s" % s.head_words)
    print("terms         : %d   parsed to %d" % (len(s.terms), s.terms_end))
    print("term shapes   : (type, translations, flags, trailing word) -> terms")
    for k, v in sorted(s.shape.items()):
        print("                %s -> %d" % (k, v))
    print("languages     : %d" % len(s.languages))
    print("closure       : terms %d reached; last field ends at %d of %d "
          "body bytes -> %s" % (len(s.terms), s.end, s.body_len,
                                "CLOSED" if s.end == s.body_len else "OPEN"))
    print()
    print("%3s  %-24s %-6s %6s %8s %6s   %s"
          % ("#", "language", "code", "word", "filled", "empty", "share filled"))
    for j, ((nm, code, w), (f, e)) in enumerate(zip(s.languages,
                                                     s.per_language())):
        print("%3d  %-24s %-6s %6d %8d %6d   %6.2f %%"
              % (j, nm, code, w, f, e, 100.0 * f / len(s.terms)))
    cells = len(s.terms) * len(s.languages)
    filled = sum(f for f, _e in s.per_language())
    print("cells         : %d x %d = %d   filled %d   empty %d   (%.2f %% filled)"
          % (len(s.terms), len(s.languages), cells, filled, cells - filled,
             100.0 * filled / cells))
    print()
    fam = s.families()
    print("families      : %d distinct key prefixes (before the first `_`)"
          % len(fam))
    print("%-24s %6s %7s" % ("prefix", "terms", "share"))
    for k, v in fam.most_common():
        print("%-24s %6d %6.2f %%" % (k, v, 100.0 * v / len(s.terms)))
    print()
    notes = s.notes()
    print("translators' notes (terms whose key begins I2_colorcode): %d"
          % len(notes))
    for k, en in notes:
        print("  %-32s %s" % (k, en))
    print()
    en = [len(t[2][0]) for t in s.terms]
    print("English cell lengths : min %d  max %d  mean %.1f  total %d chars"
          % (min(en), max(en), sum(en) / float(len(en)), sum(en)))
    print("flag bytes           : %s" % dict(collections.Counter(
        b for t in s.terms for b in t[3])))
    print()
    print("after the languages  : word %d, count %d, a URL of %d chars "
          "(REDACTED), a key of %d chars (REDACTED), a title %r, a number "
          "of %d digits = %s, words %s, float %g, last %d"
          % (s.tail_word, s.tail_count, len(s.tail_url), len(s.tail_key),
             s.tail_title, len(s.tail_number), _ms_to_utc(s.tail_number),
             s.tail_words, s.tail_float, s.tail_last))
    print("mid words / key      : %s %r" % (s.mid_words, s.mid_key))
    return 0


def _ms_to_utc(digits):
    import datetime
    if not digits.isdigit():
        return "not a number"
    ms = int(digits)
    try:
        return (datetime.datetime(1970, 1, 1)
                + datetime.timedelta(milliseconds=ms)).strftime(
                    "%Y-%m-%d %H:%M:%S UTC")
    except OverflowError:
        return "out of range"


def cmd_sample(a):
    _sf, _o, s = load_source(a.path, a.name, a.pathid)
    fam = s.families()
    first = {}
    for key, _t, cells, _f, _w in s.terms:
        p = key.split("_", 1)[0] if "_" in key else "(no underscore)"
        if p not in first:
            first[p] = (key, cells[0])
    print("the first term of each of the %d largest families, with its "
          "English cell (a sample of %d of %d terms, by rule):"
          % (a.families, a.families, len(s.terms)))
    for p, n in fam.most_common(a.families):
        key, en = first[p]
        en = en.replace("\n", " / ")
        print("  %-8s %5d  %-36s %s" % (p, n, key, en[:80]))
    return 0


def cmd_table(a):
    _sf, _o, s = load_source(a.path, a.name, a.pathid)
    out = os.path.abspath(a.out)
    if os.sep + "_work" + os.sep not in out + os.sep:
        sys.exit("i2loc: the table is the game's text; write it under _work/ "
                 "(refusing %s)" % a.out)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("key\ttype\t" + "\t".join(c for _n, c, _w in s.languages)
                 + "\n")
        for key, tt, cells, _f, _w in s.terms:
            fh.write(key + "\t" + str(tt) + "\t"
                     + "\t".join(c.replace("\t", " ").replace("\r", "\\r")
                                 .replace("\n", "\\n") for c in cells) + "\n")
    print("wrote %d terms x %d languages to %s" % (len(s.terms),
                                                  len(s.languages), a.out))
    return 0


# -- selftest, on a body built in memory ------------------------------------
def _astr(s):
    b = s.encode("utf-8")
    return struct.pack("<i", len(b)) + b + bytes((-len(b)) % 4)


def _body(terms, langs, tail_ok=True):
    b = bytes(12) + b"\x01\0\0\0" + struct.pack("<iq", 2, 831) + _astr("I2Languages")
    b += struct.pack("<III", 0, 0, 1) + struct.pack("<i", len(terms))
    for key, cells in terms:
        b += _astr(key) + struct.pack("<i", 0) + struct.pack("<i", len(cells))
        for c in cells:
            b += _astr(c)
        b += struct.pack("<i", len(cells)) + bytes(len(cells)) + bytes((-len(cells)) % 4)
        b += struct.pack("<I", 0)
    b += struct.pack("<II", 1, 1) + _astr("app_title") + struct.pack("<i", len(langs))
    for nm, code in langs:
        b += _astr(nm) + _astr(code) + struct.pack("<I", 0)
    b += struct.pack("<Ii", 0, 2) + _astr("https://example.invalid/x") + _astr("K" * 44)
    b += _astr("a title") + _astr("1787078125462")
    b += struct.pack("<IIIfI", 1, 1, 1, 5.0, 0)
    if not tail_ok:
        b += b"\0"
    return b


def cmd_selftest(_a):
    checks = []
    langs = [("English", "en"), ("Italian", "it"), ("Thai", "th")]
    terms = [("tech_a", ["A", "", "ก"]), ("dino_b", ["B", "Bi", ""]),
             ("I2_colorcode_x", ["note", "", ""]), ("plain", ["P", "P", "P"])]
    s = Source(_body(terms, langs))
    checks.append(("a hand-built body of 4 terms x 3 languages closes on the "
                   "term count and on the last byte",
                   len(s.terms) == 4 and len(s.languages) == 3
                   and s.end == s.body_len, ""))
    checks.append(("the languages are read as (name, code, word)",
                   s.languages[2] == ("Thai", "th", 0), str(s.languages)))
    checks.append(("filled / empty cells are counted per language column",
                   s.per_language() == [(4, 0), (2, 2), (2, 2)],
                   str(s.per_language())))
    checks.append(("families are the key prefix before the first `_`",
                   s.families() == {"tech": 1, "dino": 1, "I2": 1,
                                    "(no underscore)": 1}, str(s.families())))
    checks.append(("the translators' notes are the I2_colorcode terms",
                   s.notes() == [("I2_colorcode_x", "note")], ""))
    # 1787078125 s = 20,683 days + 66,925 s after the epoch; 2026-01-01 is
    # day 20,454 (56 years, 14 leap days); day 230 of 2026 is August 18
    checks.append(("the 13-digit number decodes as a Unix time in ms",
                   _ms_to_utc("1787078125462") == "2026-08-18 18:35:25 UTC",
                   _ms_to_utc("1787078125462")))
    checks.append(("a UTF-8 cell survives (Thai)",
                   s.terms[0][2][2] == "ก", ""))
    try:
        Source(_body(terms, langs, tail_ok=False))
        checks.append(("a body one byte longer than the layout is REFUSED",
                       False, "accepted"))
    except LayoutError as e:
        checks.append(("a body one byte longer than the layout is REFUSED",
                       "does not close" in str(e), str(e)))
    try:
        Source(_body(terms, langs)[:-40])
        checks.append(("a body cut short is REFUSED", False, "accepted"))
    except LayoutError:
        checks.append(("a body cut short is REFUSED", True, ""))
    try:
        Source(_body(terms, langs[:2]))
        checks.append(("terms with 3 cells against a list of 2 languages is "
                       "REFUSED", False, "accepted"))
    except LayoutError as e:
        checks.append(("terms with 3 cells against a list of 2 languages is "
                       "REFUSED", "language list" in str(e), str(e)))
    # the census must not print the URL or the key
    import io
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        _print_tail(s)
    finally:
        sys.stdout = old
    checks.append(("the census prints the URL's and the key's LENGTH, not "
                   "their text",
                   "example.invalid" not in buf.getvalue()
                   and "KKKK" not in buf.getvalue()
                   and "25 chars" in buf.getvalue(), buf.getvalue().strip()))
    width = max(len(c[0]) for c in checks)
    bad = 0
    for label, ok, note in checks:
        print("  %-*s  %s  %s" % (width, label, "ok  " if ok else "FAIL", note))
        bad += not ok
    print()
    print("%d checks, %d failures" % (len(checks), bad))
    return 1 if bad else 0


def _print_tail(s):
    print("after the languages  : word %d, count %d, a URL of %d chars "
          "(REDACTED), a key of %d chars (REDACTED), a title %r, a number "
          "of %d digits = %s"
          % (s.tail_word, s.tail_count, len(s.tail_url), len(s.tail_key),
             s.tail_title, len(s.tail_number), _ms_to_utc(s.tail_number)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nm in ("census", "sample", "table"):
        p = sub.add_parser(nm)
        p.add_argument("path")
        p.add_argument("--name", default="I2Languages")
        p.add_argument("--pathid", type=int)
        if nm == "sample":
            p.add_argument("--families", type=int, default=12)
        if nm == "table":
            p.add_argument("--out", required=True)
    sub.add_parser("selftest")
    a = ap.parse_args()
    nameguard.guard()
    try:
        return {"census": cmd_census, "sample": cmd_sample,
                "table": cmd_table, "selftest": cmd_selftest}[a.cmd](a)
    except LayoutError as e:
        sys.exit("i2loc: REFUSED -- %s" % e)


if __name__ == "__main__":
    sys.exit(main())
