#!/usr/bin/env python3
"""nrbf.py -- read a .NET BinaryFormatter stream (MS-NRBF) to residue zero.

MS-NRBF is *[MS-NRBF]: .NET Remoting: Binary Format Data Structure*, a
published Microsoft specification. This reader implements the subset that
`OfficialContent\\info.bin` and the `info.bin` inside every `.mdm` actually
use -- the class, library, string, primitive and reference records -- and it
REFUSES anything else rather than skipping it, because a serialisation reader
that skips is a reader that lies about its residue.

The point of the tool on this object is two integers:

    Storage.Publish.PublishInfo._objectsCount
    Storage.Publish.PublishInfo._resourceCount

which are the only two denominators in the object that were written by the
program that built it.

Every run reports the residue: bytes consumed against bytes in the file. A
stream that does not end on a MessageEnd record at exactly the last byte is a
failure and is reported as one.

    python tools/nrbf.py academagia-steam/OfficialContent/info.bin
    python tools/nrbf.py --zip academagia-steam/Mods/Content.mdm --member info.bin
    python tools/nrbf.py --selftest

GROWN ON pc-celltosingularity-doc, where three game saves (`.gd`, the
studio's own convention saves in StreamingAssets) are BinaryFormatter
streams that use what Academagia's did not: member types 5, 6 and 7
(StringArray, ObjectArray, PrimitiveArray), the records ArraySinglePrimitive
(15), ArraySingleObject (16), ArraySingleString (17) and
MemberPrimitiveTyped (8), BinaryArray with offsets, BinaryLibrary records
in the middle of the stream, and inline Char / Decimal / Single / UInt*.
The `--census` mode is what that object publishes:

    python tools/nrbf.py --census SAVE.gd

It prints the closure (bytes read, residue, MessageEnd at the last byte),
the record-type histogram, the libraries, and every class by NAME with its
MEMBER COUNT and the kinds of its members -- and NOTHING ELSE. `--members`
adds the member names and their kinds. NO MODE PRINTS A VALUE of a class
member, and THIS READER DOES NOT WRITE: it has no `--set`, no output file,
no re-serialisation. That is a design decision, not an omission: the object
it was grown on is a live game with purchases, and a document that says
'the field at +N is the currency' is a save editor with the verbs removed.
The reader walks, counts and names; what it counts can be re-counted by
anyone with the same file and this tool, and nobody can alter a save
with it.
"""
import argparse
import collections
import datetime
import io
import os
import struct
import sys
import uuid
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dirguard   # noqa: E402
import nameguard  # noqa: E402

# MS-NRBF section 2.1.2.1, RecordTypeEnumeration.
SERIALIZED_STREAM_HEADER = 0
CLASS_WITH_ID = 1
SYSTEM_CLASS_WITH_MEMBERS = 2
CLASS_WITH_MEMBERS = 3
SYSTEM_CLASS_WITH_MEMBERS_AND_TYPES = 4
CLASS_WITH_MEMBERS_AND_TYPES = 5
BINARY_OBJECT_STRING = 6
BINARY_ARRAY = 7
MEMBER_PRIMITIVE_TYPED = 8
MEMBER_REFERENCE = 9
OBJECT_NULL = 10
MESSAGE_END = 11
BINARY_LIBRARY = 12
OBJECT_NULL_MULTIPLE_256 = 13
OBJECT_NULL_MULTIPLE = 14
ARRAY_SINGLE_PRIMITIVE = 15
ARRAY_SINGLE_OBJECT = 16
ARRAY_SINGLE_STRING = 17

# MS-NRBF section 2.1.2.3, PrimitiveTypeEnumeration. Note that there is no
# value 4: the enumeration runs Boolean=1, Byte=2, Char=3, (gap), Decimal=5,
# Double=6, Int16=7, Int32=8, Int64=9. Getting this table one place out is
# exactly the failure this reader was written to avoid, because a wrong width
# desynchronises the stream and the next record type byte is then garbage --
# which is what a first run of this tool produced, loudly.
PRIMITIVES = {
    1: ("Boolean", 1), 2: ("Byte", 1), 3: ("Char", None),
    5: ("Decimal", None), 6: ("Double", 8), 7: ("Int16", 2),
    8: ("Int32", 4), 9: ("Int64", 8), 10: ("SByte", 1), 11: ("Single", 4),
    12: ("TimeSpan", 8), 13: ("DateTime", 8), 14: ("UInt16", 2),
    15: ("UInt32", 4), 16: ("UInt64", 8), 17: ("Null", 0),
    18: ("String", None),
}
MEMBER_PRIMITIVES = PRIMITIVES


class NrbfError(Exception):
    pass


class Reader(object):
    def __init__(self, data):
        self.d = data
        self.p = 0

    def u8(self):
        if self.p + 1 > len(self.d):
            raise NrbfError("u8 past end at %d" % self.p)
        v = self.d[self.p]
        self.p += 1
        return v

    def i32(self):
        if self.p + 4 > len(self.d):
            raise NrbfError("i32 past end at %d" % self.p)
        v = struct.unpack_from("<i", self.d, self.p)[0]
        self.p += 4
        return v

    def raw(self, n):
        if self.p + n > len(self.d):
            raise NrbfError("read of %d past end at %d" % (n, self.p))
        v = self.d[self.p:self.p + n]
        self.p += n
        return v

    def string(self):
        """LengthPrefixedString: 7-bit encoded length, then UTF-8 bytes."""
        n = 0
        shift = 0
        while True:
            b = self.u8()
            n |= (b & 0x7F) << shift
            if not (b & 0x80):
                break
            shift += 7
            if shift > 35:
                raise NrbfError("string length prefix too long at %d" % self.p)
        return self.raw(n).decode("utf-8")


def _dt(ticks_word):
    """A .NET DateTime as MS-NRBF writes it: 62 bits of ticks, 2 of Kind."""
    kind = (ticks_word >> 62) & 3
    ticks = ticks_word & ((1 << 62) - 1)
    base = datetime.datetime(1, 1, 1)
    return base + datetime.timedelta(microseconds=ticks // 10), kind


def _guid_from_members(vals):
    """System.Guid serialises as _a.._k: int32, int16, int16, then 8 bytes."""
    a, b, c = vals[0], vals[1], vals[2]
    rest = bytes((v & 0xFF) for v in vals[3:11])
    return uuid.UUID(bytes=struct.pack(">IHH", a & 0xFFFFFFFF, b & 0xFFFF,
                                       c & 0xFFFF) + rest)


class Stream(object):
    """A parsed MS-NRBF stream. Objects are kept by id; classes by id."""

    def __init__(self, data):
        self.r = Reader(data)
        self.layouts = {}      # objectId -> (name, [memberName], [(kind, extra)])
        self.classes = {}      # objectId -> class name
        self.objects = {}      # objectId -> dict or value
        self.libraries = {}
        self.records = 0
        self.ended = False
        self.arrays = []       # (objectId, total, items) for every array record
        self.rectypes = collections.Counter()   # record type byte -> count
        self.instances = collections.Counter()  # class name -> instances
        self._parse()

    # -- record dispatch ---------------------------------------------------
    def _parse(self):
        r = self.r
        t = r.u8()
        if t != SERIALIZED_STREAM_HEADER:
            raise NrbfError("first record is %d, not a stream header" % t)
        root, header, major, minor = r.i32(), r.i32(), r.i32(), r.i32()
        self.root, self.major, self.minor = root, major, minor
        self.records = 1
        if major != 1:
            raise NrbfError("major version %d is not 1" % major)
        self.rectypes[SERIALIZED_STREAM_HEADER] += 1
        while not self.ended:
            t = r.u8()
            self.records += 1
            self.rectypes[t] += 1
            self._record(t)

    def _record(self, t):
        r = self.r
        if t == BINARY_LIBRARY:
            lid = r.i32()
            self.libraries[lid] = r.string()
        elif t == MESSAGE_END:
            self.ended = True
        elif t == CLASS_WITH_MEMBERS_AND_TYPES:
            self._class(r, system=False)
        elif t == SYSTEM_CLASS_WITH_MEMBERS_AND_TYPES:
            self._class(r, system=True)
        elif t == CLASS_WITH_ID:
            self._class_with_id(r)
        elif t == BINARY_ARRAY:
            self._binary_array(r)
        elif t == ARRAY_SINGLE_PRIMITIVE:
            self._array_single(r, "prim")
        elif t == ARRAY_SINGLE_OBJECT:
            self._array_single(r, "object")
        elif t == ARRAY_SINGLE_STRING:
            self._array_single(r, "str")
        elif t == BINARY_OBJECT_STRING:
            oid = r.i32()
            self.objects[oid] = r.string()
        elif t == OBJECT_NULL:
            pass
        else:
            raise NrbfError("record type %d at offset %d is not implemented; "
                            "this reader refuses rather than skips"
                            % (t, r.p - 1))

    def _extra(self, r, k):
        """AdditionalInfo for one BinaryTypeEnum, MS-NRBF 2.3.1.2: what
        follows the type byte in a class's MemberTypeInfo or an array's
        type. 0 Primitive (a PrimitiveTypeEnum byte), 1 String, 2 Object,
        3 SystemClass (a name), 4 Class (a name and a LibraryId), 5
        StringArray, 6 ObjectArray, 7 PrimitiveArray (a PrimitiveTypeEnum
        byte). The three array kinds are the ones Academagia's streams
        never used and a Unity game's saves use everywhere."""
        if k == 0:
            return ("prim", r.u8())
        if k == 1:
            return ("str", None)
        if k == 2:
            return ("object", None)
        if k == 3:
            return ("sysclass", r.string())
        if k == 4:
            return ("class", (r.string(), r.i32()))
        if k == 5:
            return ("strarr", None)
        if k == 6:
            return ("objarr", None)
        if k == 7:
            return ("primarr", r.u8())
        raise NrbfError("BinaryTypeEnum %d is not implemented" % k)

    def _class(self, r, system):
        oid = r.i32()
        name = r.string()
        count = r.i32()
        if count < 0 or count > 4096:
            raise NrbfError("member count %d for %s is not credible"
                            % (count, name))
        members = [r.string() for _ in range(count)]
        kinds = [r.u8() for _ in range(count)]
        info = [self._extra(r, k) for k in kinds]
        if not system:
            r.i32()                         # LibraryId
        self.layouts[oid] = (name, members, info)
        vals = []
        for kind, extra in info:
            vals.append(self._value(kind, extra))
        self.classes[oid] = name
        self.instances[name] += 1
        self.objects[oid] = dict(zip(members, vals))
        self.objects[oid]["__class__"] = name
        return oid

    def _element(self, t):
        """One element of an array, or one nested member value, by its
        record type byte -- the record has already been counted. Returns
        (consumed, value): `consumed` is how many elements it stands for
        (0 for a BinaryLibrary, which may sit before any class record and
        is not an element; n for an ObjectNullMultiple run)."""
        r = self.r
        if t == BINARY_LIBRARY:
            lid = r.i32()
            self.libraries[lid] = r.string()
            return 0, None
        if t == OBJECT_NULL:
            return 1, None
        if t == OBJECT_NULL_MULTIPLE_256:
            return r.u8(), None
        if t == OBJECT_NULL_MULTIPLE:
            return r.i32(), None
        if t == MEMBER_REFERENCE:
            return 1, ("ref", r.i32())
        if t == BINARY_OBJECT_STRING:
            oid = r.i32()
            s = r.string()
            self.objects[oid] = s
            return 1, s
        if t in (CLASS_WITH_MEMBERS_AND_TYPES,
                 SYSTEM_CLASS_WITH_MEMBERS_AND_TYPES):
            return 1, ("obj", self._class(
                r, system=(t == SYSTEM_CLASS_WITH_MEMBERS_AND_TYPES)))
        if t == CLASS_WITH_ID:
            return 1, ("obj", self._class_with_id(r))
        if t == BINARY_ARRAY:
            return 1, ("arr", self._binary_array(r))
        if t == ARRAY_SINGLE_PRIMITIVE:
            return 1, ("arr", self._array_single(r, "prim"))
        if t == ARRAY_SINGLE_OBJECT:
            return 1, ("arr", self._array_single(r, "object"))
        if t == ARRAY_SINGLE_STRING:
            return 1, ("arr", self._array_single(r, "str"))
        if t == MEMBER_PRIMITIVE_TYPED:
            return 1, self._value("prim", r.u8())
        raise NrbfError("record type %d at offset %d is not implemented as "
                        "an element or member value" % (t, r.p - 1))

    def _elements(self, total, extra):
        """`total` elements of an array whose type is `extra`: inline
        primitives, or records. ObjectNullMultiple runs fill a List's
        spare capacity, which is why a List of 2,423 items occupies an
        array of 4,096."""
        items = []
        while len(items) < total:
            if extra[0] == "prim":
                items.append(self._value("prim", extra[1]))
                continue
            t = self.r.u8()
            self.records += 1
            self.rectypes[t] += 1
            n, v = self._element(t)
            if n == 0:
                continue
            if n == 1:
                items.append(v)
            else:
                items.extend([None] * n)
        if len(items) != total:
            raise NrbfError("array declared %d elements and %d were read"
                            % (total, len(items)))
        return items

    def _array_single(self, r, what):
        """ArraySinglePrimitive (15), ArraySingleObject (16),
        ArraySingleString (17): MS-NRBF 2.4.3.3-5. ArrayInfo is objectId
        and length; the primitive one then names its PrimitiveTypeEnum."""
        oid = r.i32()
        total = r.i32()
        if total < 0:
            raise NrbfError("array length %d is negative" % total)
        if what == "prim":
            extra = ("prim", r.u8())
        elif what == "str":
            extra = ("str", None)
        else:
            extra = ("object", None)
        items = self._elements(total, extra)
        self.objects[oid] = items
        self.arrays.append((oid, total, items))
        return oid

    def _binary_array(self, r):
        """BinaryArray, MS-NRBF 2.4.3.1. `deleted.bin` inside a .mdm is a
        serialised List<Guid>, so the array of System.Guid has to be walked
        element by element -- including the ObjectNullMultiple runs that fill
        a List's spare capacity, which are the reason a List of 2,423 items
        occupies an array of 4,096."""
        oid = r.i32()
        atype = r.u8()
        rank = r.i32()
        if atype not in (0, 1, 2, 3, 4, 5) or rank < 1 or rank > 32:
            raise NrbfError("array type %d rank %d is not implemented"
                            % (atype, rank))
        lengths = [r.i32() for _ in range(rank)]
        if any(n < 0 for n in lengths):
            raise NrbfError("array length %r is negative" % (lengths,))
        if atype in (3, 4, 5):
            [r.i32() for _ in range(rank)]     # LowerBounds
        extra = self._extra(r, r.u8())
        total = 1
        for n in lengths:
            total *= n
        items = self._elements(total, extra)
        self.objects[oid] = items
        self.arrays.append((oid, total, items))
        return oid

    def _class_with_id(self, r):
        """ClassWithId: a second instance of a class whose layout was already
        written. MS-NRBF 2.3.2.5. Without this a stream holding two objects of
        the same class cannot be read, which is exactly what a mod's info.bin
        does and the base game's does not."""
        oid = r.i32()
        mid = r.i32()
        if mid not in self.layouts:
            raise NrbfError("ClassWithId %d refers to unknown metadata id %d"
                            % (oid, mid))
        name, members, info = self.layouts[mid]
        vals = [self._value(kind, extra) for kind, extra in info]
        self.classes[oid] = name
        self.instances[name] += 1
        self.objects[oid] = dict(zip(members, vals))
        self.objects[oid]["__class__"] = name
        return oid

    def _value(self, kind, extra):
        r = self.r
        if kind == "prim":
            if extra not in MEMBER_PRIMITIVES:
                raise NrbfError("PrimitiveTypeEnum %d is not one the "
                                "specification names" % extra)
            pname, size = MEMBER_PRIMITIVES[extra]
            if pname == "Decimal" or pname == "String":
                return r.string()          # LengthPrefixedString, 2.1.1.6
            if pname == "Char":
                # one UTF-8 code point: the lead byte says its length
                lead = r.u8()
                n = (0 if lead < 0x80 else 1 if lead >> 5 == 6
                     else 2 if lead >> 4 == 14 else 3 if lead >> 3 == 30
                     else None)
                if n is None:
                    raise NrbfError("Char lead byte 0x%02x is not UTF-8" % lead)
                return (bytes([lead]) + r.raw(n)).decode("utf-8")
            b = r.raw(size)
            if pname == "Int32":
                return struct.unpack("<i", b)[0]
            if pname == "Int64":
                return struct.unpack("<q", b)[0]
            if pname == "Int16":
                return struct.unpack("<h", b)[0]
            if pname == "Double":
                return struct.unpack("<d", b)[0]
            if pname == "Single":
                return struct.unpack("<f", b)[0]
            if pname == "UInt16":
                return struct.unpack("<H", b)[0]
            if pname == "UInt32":
                return struct.unpack("<I", b)[0]
            if pname == "UInt64":
                return struct.unpack("<Q", b)[0]
            if pname in ("Byte", "SByte", "Boolean"):
                return b[0]
            if pname == "DateTime":
                return _dt(struct.unpack("<Q", b)[0])
            return b
        # Everything else is a nested record: read it and return a marker.
        # A BinaryLibrary may stand before it (2.6.2: 'before any record
        # that refers to it'), and is not the value.
        while True:
            t = r.u8()
            self.records += 1
            self.rectypes[t] += 1
            n, v = self._element(t)
            if n == 0:
                continue
            if n == 1:
                return v
            return ("nulls", n)

    # -- the two integers --------------------------------------------------
    def publish_info(self):
        for oid, o in self.objects.items():
            if isinstance(o, dict) and o.get("__class__", "").endswith(
                    "PublishInfo"):
                return o
        raise NrbfError("no PublishInfo object in this stream")

    def db_info(self):
        for oid, o in self.objects.items():
            if isinstance(o, dict) and o.get("__class__", "") == "Storage.DBInfo":
                return o
        return None

    def guid(self):
        for oid, o in self.objects.items():
            if isinstance(o, dict) and o.get("__class__") == "System.Guid":
                vals = [o["_a"], o["_b"], o["_c"]] + [o["_" + c] for c in
                                                      "defghijk"]
                return _guid_from_members(vals)
        return None


RECORD_NAMES = {
    0: "SerializationHeader", 1: "ClassWithId", 2: "SystemClassWithMembers",
    3: "ClassWithMembers", 4: "SystemClassWithMembersAndTypes",
    5: "ClassWithMembersAndTypes", 6: "BinaryObjectString", 7: "BinaryArray",
    8: "MemberPrimitiveTyped", 9: "MemberReference", 10: "ObjectNull",
    11: "MessageEnd", 12: "BinaryLibrary", 13: "ObjectNullMultiple256",
    14: "ObjectNullMultiple", 15: "ArraySinglePrimitive",
    16: "ArraySingleObject", 17: "ArraySingleString",
}
KIND_NAMES = {"prim": "primitive", "str": "string", "object": "object",
              "sysclass": "system class", "class": "class",
              "strarr": "string[]", "objarr": "object[]",
              "primarr": "primitive[]"}


def _kind_label(kind, extra):
    if kind == "prim" or kind == "primarr":
        return "%s<%s>" % (KIND_NAMES[kind],
                           PRIMITIVES.get(extra, ("?%d" % extra,))[0])
    return KIND_NAMES[kind]


def _short(name):
    """A class name without its generic arguments' assembly-qualified
    tails: `Dictionary`2[[System.String, mscorlib, Version=...],[X,
    Assembly-CSharp, Version=...]]` -> `Dictionary`2[System.String,X]`."""
    import re
    s = re.sub(r",\s*[^\[\],]+,\s*Version=[^\]]*", "", name)
    return s.replace("[[", "[").replace("],[", ",").replace("]]", "]")


def census(data, label):
    """THE STRUCTURE OF ONE STREAM, AND NO VALUE FROM IT.

    Closure, record histogram, libraries, then every class by name with
    its member count, the kinds of its members (how many primitives,
    strings, classes, arrays -- not which member is which) and how many
    instances the stream holds. The member NAMES are printed only with
    `--members`, and no mode prints what any member holds. See the module
    docstring for why.
    """
    try:
        s = Stream(data)
    except NrbfError as e:
        print("stream        : %s" % label)
        print("REFUSED       : %s" % e)
        return 1
    used = s.r.p
    print("stream        : %s" % label)
    print("bytes         : %d read of %d   residue %d"
          % (used, len(data), len(data) - used))
    print("records       : %d   ends on MessageEnd : %s   at the last byte : %s"
          % (s.records, s.ended, s.ended and used == len(data)))
    print("header        : RootId %d  MajorVersion %d  MinorVersion %d"
          % (s.root, s.major, s.minor))
    print()
    print("record types  :")
    for t, n in sorted(s.rectypes.items()):
        print("  %2d %-32s %8d" % (t, RECORD_NAMES.get(t, "?"), n))
    print()
    for lid, lname in sorted(s.libraries.items()):
        print("library %-5d : %s" % (lid, lname))
    print()
    nstr = sum(1 for o in s.objects.values() if isinstance(o, str))
    nobj = sum(1 for o in s.objects.values() if isinstance(o, dict))
    narr = len(s.arrays)
    nelem = sum(t for _o, t, _i in s.arrays)
    print("objects       : %d class instances, %d strings, %d arrays holding "
          "%d elements" % (nobj, nstr, narr, nelem))
    print("classes       : %d distinct layouts" % len(s.layouts))
    print()
    rows = {}
    for _oid, (name, members, info) in s.layouts.items():
        if name in rows:
            continue
        kinds = collections.Counter(_kind_label(k, e) for k, e in info)
        rows[name] = (len(members), s.instances[name], kinds, members, info)
    w = max([len(_short(n)) for n in rows] + [5])
    print("%-*s %7s %9s  %s" % (w, "class", "members", "instances",
                                 "member kinds"))
    for name in sorted(rows, key=lambda n: (-rows[n][0], n)):
        cnt, inst, kinds, _m, _i = rows[name]
        print("%-*s %7d %9d  %s"
              % (w, _short(name), cnt, inst,
                 ", ".join("%s x%d" % (k, v) for k, v in
                           sorted(kinds.items(), key=lambda kv: -kv[1]))))
    print()
    print("members       : %d over %d classes"
          % (sum(r[0] for r in rows.values()), len(rows)))
    if census.members:
        print()
        print("member names, by class (names and kinds; no offsets, no values):")
        for name in sorted(rows, key=lambda n: (-rows[n][0], n)):
            _c, _n, _k, members, info = rows[name]
            print("  %s" % _short(name))
            for m, (k, e) in zip(members, info):
                print("      %-48s %s" % (m, _kind_label(k, e)))
    if not s.ended or used != len(data):
        print()
        print("FAILURE: the stream does not end on MessageEnd at its last byte")
        return 1
    return 0


census.members = False


def report(data, label):
    s = Stream(data)
    used = s.r.p
    print("stream        : %s" % label)
    print("bytes         : %d read of %d   residue %d"
          % (used, len(data), len(data) - used))
    print("records       : %d   ends on MessageEnd : %s"
          % (s.records, s.ended))
    for lid, lname in sorted(s.libraries.items()):
        print("library %-5d : %s" % (lid, lname))
    lists = [o for o in s.objects.values()
             if isinstance(o, dict) and o.get("__class__", "").startswith(
                 "System.Collections.Generic.List")]
    if lists:
        lo = lists[0]
        print("class          : %s" % lo["__class__"].split("[[")[0])
        print("  _size          : %d" % lo["_size"])
        arr = s.objects.get(lo["_items"][1]) if isinstance(
            lo["_items"], tuple) else None
        if arr is not None:
            live = [x for x in arr if x is not None]
            print("  array capacity : %d   non-null elements : %d"
                  % (len(arr), len(live)))
            gs = []
            for x in live:
                if isinstance(x, tuple) and x[0] == "obj":
                    o = s.objects.get(x[1], {})
                    if o.get("__class__") == "System.Guid":
                        gs.append(_guid_from_members(
                            [o["_a"], o["_b"], o["_c"]] +
                            [o["_" + c] for c in "defghijk"]))
            print("  System.Guid    : %d   distinct : %d"
                  % (len(gs), len(set(gs))))
            if gs:
                print("  first          : %s" % gs[0])
        if len(data) - used:
            print("FAILURE: residue is not zero")
            return 1
        return 0
    pi = s.publish_info()
    print("PublishInfo")
    print("  _objectsCount  : %d" % pi["_objectsCount"])
    print("  _resourceCount : %d" % pi["_resourceCount"])
    db = s.db_info()
    if db:
        print("DBInfo")
        print("  _name          : %r" % db["_name"])
        print("  _author        : %r" % db["_author"])
        print("  _maxId         : %d" % db["_maxId"])
        for f in ("_creationDate", "_modificationDate"):
            v = db[f]
            if isinstance(v, tuple):
                print("  %-14s : %s  (DateTimeKind %d)"
                      % (f, v[0].isoformat(sep=" "), v[1]))
        g = s.guid()
        if g:
            print("  _guid          : %s" % g)
        mi = db["_modInfo"]
        if isinstance(mi, tuple) and mi and mi[0] in ("obj", "ref"):
            mo = s.objects.get(mi[1], {})
            print("  _modInfo       : %s" % mo.get("__class__"))
            for k in sorted(mo):
                if k == "__class__":
                    continue
                v = mo[k]
                if isinstance(v, tuple) and len(v) == 2 and hasattr(
                        v[0], "isoformat"):
                    v = "%s (Kind %d)" % (v[0].isoformat(sep=" "), v[1])
                print("      %-16s : %s" % (k, v))
        else:
            print("  _modInfo       : %s" % (mi,))
    ver = [o for o in s.objects.values()
           if isinstance(o, dict) and o.get("__class__") == "System.Version"]
    if ver:
        v = ver[0]
        print("version        : %d.%d.%d.%d"
              % (v["_Major"], v["_Minor"], v["_Build"], v["_Revision"]))
    if len(data) - used:
        print("FAILURE: residue is not zero")
        return 1
    return 0


def _hdr():
    return (b"\x00\x01\x00\x00\x00\xff\xff\xff\xff"
            b"\x01\x00\x00\x00\x00\x00\x00\x00")


def _lps(s):
    b = s.encode("utf-8")
    n = len(b)
    out = b""
    while True:
        if n < 0x80:
            return out + bytes([n]) + b
        out += bytes([(n & 0x7f) | 0x80])
        n >>= 7


def selftest_grown():
    """The records grown on pc-celltosingularity-doc, on hand-built
    streams -- each one refused by the reader as inherited."""
    checks = []

    def parses(blob):
        s = Stream(blob)
        return s if (s.ended and s.r.p == len(blob)) else None

    # a class with a PrimitiveArray member (type 7) holding an
    # ArraySinglePrimitive of three Int32
    blob = (_hdr() + b"\x0c\x02\x00\x00\x00" + _lps("Assembly-CSharp")
            + b"\x05\x01\x00\x00\x00" + _lps("Save") + b"\x01\x00\x00\x00"
            + _lps("counts") + b"\x07\x08" + b"\x02\x00\x00\x00"
            + b"\x09\x03\x00\x00\x00"
            + b"\x0f\x03\x00\x00\x00\x03\x00\x00\x00\x08"
            + struct.pack("<iii", 1, 2, 3) + b"\x0b")
    s = parses(blob)
    checks.append(("a PrimitiveArray member (BinaryTypeEnum 7) and an "
                   "ArraySinglePrimitive (15) of three Int32 close on the last byte",
                   s is not None and s.objects[3] == [1, 2, 3]
                   and s.rectypes[15] == 1, ""))
    # a StringArray member (5) -> ArraySingleString (17) with a null run
    blob = (_hdr() + b"\x0c\x02\x00\x00\x00" + _lps("Assembly-CSharp")
            + b"\x05\x01\x00\x00\x00" + _lps("Save") + b"\x01\x00\x00\x00"
            + _lps("names") + b"\x05" + b"\x02\x00\x00\x00"
            + b"\x09\x03\x00\x00\x00"
            + b"\x11\x03\x00\x00\x00\x04\x00\x00\x00"
            + b"\x06\x04\x00\x00\x00" + _lps("a") + b"\x0d\x02"
            + b"\x06\x05\x00\x00\x00" + _lps("b") + b"\x0b")
    s = parses(blob)
    checks.append(("a StringArray member (5) -> ArraySingleString (17) with an "
                   "ObjectNullMultiple256 run of 2 reads 4 elements",
                   s is not None and s.objects[3] == ["a", None, None, "b"], ""))
    # an ObjectArray member (6) -> ArraySingleObject (16) holding a
    # MemberPrimitiveTyped (8) Double and a null
    blob = (_hdr() + b"\x0c\x02\x00\x00\x00" + _lps("Assembly-CSharp")
            + b"\x05\x01\x00\x00\x00" + _lps("Save") + b"\x01\x00\x00\x00"
            + _lps("objs") + b"\x06" + b"\x02\x00\x00\x00"
            + b"\x09\x03\x00\x00\x00"
            + b"\x10\x03\x00\x00\x00\x02\x00\x00\x00"
            + b"\x08\x06" + struct.pack("<d", 2.5) + b"\x0a" + b"\x0b")
    s = parses(blob)
    checks.append(("an ObjectArray member (6) -> ArraySingleObject (16) with a "
                   "MemberPrimitiveTyped (8) Double and an ObjectNull",
                   s is not None and s.objects[3] == [2.5, None], ""))
    # a BinaryLibrary in the MIDDLE of the stream, before a nested class
    blob = (_hdr() + b"\x0c\x02\x00\x00\x00" + _lps("Assembly-CSharp")
            + b"\x05\x01\x00\x00\x00" + _lps("Save") + b"\x01\x00\x00\x00"
            + _lps("inner") + b"\x04" + _lps("Other") + b"\x03\x00\x00\x00"
            + b"\x02\x00\x00\x00"
            + b"\x0c\x03\x00\x00\x00" + _lps("OtherLib")
            + b"\x05\x04\x00\x00\x00" + _lps("Other") + b"\x01\x00\x00\x00"
            + _lps("x") + b"\x00\x08" + b"\x03\x00\x00\x00"
            + struct.pack("<i", 7) + b"\x0b")
    s = parses(blob)
    checks.append(("a BinaryLibrary (12) standing before a nested class is not "
                   "a member value; two libraries are named",
                   s is not None and len(s.libraries) == 2
                   and s.objects[4]["x"] == 7, ""))
    # a rank-2 BinaryArray (Rectangular, 2) of 2x3 Byte
    blob = (_hdr() + b"\x07\x01\x00\x00\x00\x02\x02\x00\x00\x00"
            + struct.pack("<ii", 2, 3) + b"\x00\x02" + bytes(range(6)) + b"\x0b")
    s = parses(blob)
    checks.append(("a rank-2 rectangular BinaryArray of 2x3 Byte reads six "
                   "elements", s is not None and len(s.objects[1]) == 6, ""))
    # inline Char, Decimal, Single, UInt32 members
    blob = (_hdr() + b"\x0c\x02\x00\x00\x00" + _lps("Assembly-CSharp")
            + b"\x05\x01\x00\x00\x00" + _lps("Save") + b"\x04\x00\x00\x00"
            + _lps("c") + _lps("d") + _lps("f") + _lps("u")
            + b"\x00\x00\x00\x00" + b"\x03\x05\x0b\x0f" + b"\x02\x00\x00\x00"
            + "\u00e9".encode("utf-8") + _lps("1.5") + struct.pack("<f", 0.5)
            + struct.pack("<I", 0xffffffff) + b"\x0b")
    s = parses(blob)
    checks.append(("inline Char (UTF-8), Decimal (string), Single and UInt32 "
                   "members are read at their widths",
                   s is not None and s.objects[1]["c"] == "\u00e9"
                   and s.objects[1]["d"] == "1.5" and s.objects[1]["f"] == 0.5
                   and s.objects[1]["u"] == 0xffffffff, ""))
    # the census prints no value: a class member holding 424242 must not
    # appear in the census text
    blob = (_hdr() + b"\x0c\x02\x00\x00\x00" + _lps("Assembly-CSharp")
            + b"\x05\x01\x00\x00\x00" + _lps("Save") + b"\x01\x00\x00\x00"
            + _lps("entropy") + b"\x00\x08" + b"\x02\x00\x00\x00"
            + struct.pack("<i", 424242) + b"\x0b")
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        census.members = True
        rc = census(blob, "specimen")
    finally:
        sys.stdout = old
        census.members = False
    text = buf.getvalue()
    checks.append(("the census names the class and the member, and prints NO "
                   "value (424242 is absent from its text)",
                   rc == 0 and "Save" in text and "entropy" in text
                   and "424242" not in text, ""))
    checks.append(("a truncated grown stream (array longer than the file) is "
                   "refused, not read short",
                   _refuses(_hdr() + b"\x0f\x01\x00\x00\x00\x09\x00\x00\x00\x08"
                            + struct.pack("<ii", 1, 2)), ""))
    checks.append(("the census on a stream that does not reach MessageEnd "
                   "reports REFUSED and rc 1",
                   _census_rc(_hdr() + b"\x0f\x01\x00\x00\x00\x09\x00\x00\x00\x08"
                              + struct.pack("<ii", 1, 2)) == 1, ""))
    checks.append(("an assembly-qualified generic name is shortened to its type "
                   "arguments",
                   _short("System.Collections.Generic.Dictionary`2[[System.String, "
                          "mscorlib, Version=4.0.0.0, Culture=neutral, "
                          "PublicKeyToken=b77a5c561934e089],[ItemSaveData, "
                          "Assembly-CSharp, Version=0.0.0.0, Culture=neutral, "
                          "PublicKeyToken=null]]")
                   == "System.Collections.Generic.Dictionary`2[System.String,ItemSaveData]",
                   ""))
    checks.append(("the magic main() selects by is record 0 + MajorVersion 1 at "
                   "bytes 9..12, and a RootId other than 1 still passes it",
                   _is_nrbf_head(_hdr()) and _is_nrbf_head(
                       b"\x00\x07\x00\x00\x00\xff\xff\xff\xff\x01\x00\x00\x00"
                       b"\x00\x00\x00\x00\x0b")
                   and not _is_nrbf_head(b"\x00\x01\x00\x00" + bytes(13)), ""))
    width = max(len(c[0]) for c in checks)
    bad = 0
    for label, ok, note in checks:
        print("  %-*s  %s  %s" % (width, label, "ok  " if ok else "FAIL", note))
        bad += not ok
    print()
    print("%d grown checks, %d failures" % (len(checks), bad))
    return 1 if bad else 0


def _is_nrbf_head(data):
    return (len(data) >= 17 and data[0] == 0
            and data[9:13] == b"\x01\x00\x00\x00")


def _refuses(blob):
    try:
        Stream(blob)
    except NrbfError:
        return True
    return False


def _census_rc(blob):
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        return census(blob, "specimen")
    finally:
        sys.stdout = old


def selftest():
    """Specimens built in memory. Most of them must be refused."""
    ok = 0
    fail = []

    def must_fail(name, blob):
        try:
            Stream(blob)
        except NrbfError:
            return True
        fail.append(name)
        return False

    # 1..6: things that are not this format, or are truncated, or lie.
    cases = [
        ("empty", b""),
        ("wrong first record", b"\x0c" + b"\x00" * 32),
        ("truncated header", b"\x00\x01\x00\x00\x00"),
        ("major version 2", b"\x00\x01\x00\x00\x00\xff\xff\xff\xff"
                            b"\x02\x00\x00\x00\x00\x00\x00\x00"),
        ("unimplemented record", b"\x00\x01\x00\x00\x00\xff\xff\xff\xff"
                                 b"\x01\x00\x00\x00\x00\x00\x00\x00\x07"),
        ("absurd member count", b"\x00\x01\x00\x00\x00\xff\xff\xff\xff"
                                b"\x01\x00\x00\x00\x00\x00\x00\x00"
                                b"\x05\x01\x00\x00\x00\x01A"
                                b"\xff\xff\x00\x00"),
    ]
    for name, blob in cases:
        if must_fail(name, blob):
            ok += 1

    # 7: one specimen that MUST parse -- a header, a string, a message end.
    good = (b"\x00\x01\x00\x00\x00\xff\xff\xff\xff"
            b"\x01\x00\x00\x00\x00\x00\x00\x00"
            b"\x06\x01\x00\x00\x00\x03" + b"1.0" + b"\x0b")
    try:
        s = Stream(good)
        assert s.ended and s.r.p == len(good), "residue on the good specimen"
        assert s.objects[1] == "1.0"
        ok += 1
    except Exception as e:                                    # noqa: BLE001
        fail.append("good specimen: %s" % e)

    # 8: a 7-bit length prefix over 127 bytes, which the naive reader gets
    #    wrong and which this object's own streams do not exercise.
    long_s = "x" * 300
    blob = (b"\x00\x01\x00\x00\x00\xff\xff\xff\xff"
            b"\x01\x00\x00\x00\x00\x00\x00\x00"
            b"\x06\x01\x00\x00\x00\xac\x02" + long_s.encode() + b"\x0b")
    try:
        s = Stream(blob)
        assert s.objects[1] == long_s and s.r.p == len(blob)
        ok += 1
    except Exception as e:                                    # noqa: BLE001
        fail.append("300-byte string: %s" % e)

    print("selftest: %d of 8 specimens behaved as required "
          "(6 of the 8 must be refused)" % ok)
    for f in fail:
        print("  FAILED: %s" % f)
    print()
    grown = selftest_grown()
    return 0 if (not fail and grown == 0) else 1


NRBF_MAGIC = b"\x00\x01\x00\x00\x00\xff\xff\xff\xff\x01\x00\x00\x00\x00\x00\x00\x00"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path", nargs="?")
    ap.add_argument("--zip", dest="zippath")
    ap.add_argument("--member", default="info.bin")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--census", action="store_true",
                    help="structure and counts only: classes, member counts, "
                         "kinds, closure -- no values")
    ap.add_argument("--members", action="store_true",
                    help="with --census: member names and kinds too")
    a = ap.parse_args()
    nameguard.guard()
    if a.selftest:
        return selftest()
    if a.zippath:
        with zipfile.ZipFile(a.zippath) as z:
            data = z.read(a.member)
        return report(data, "%s :: %s" % (os.path.basename(a.zippath),
                                          a.member))
    if not a.path:
        ap.error("give a path, or --zip, or --selftest")
    dirguard.want_file(a.path, "nrbf")
    with open(a.path, "rb") as f:
        data = f.read()
    # record type 0 at byte 0, MajorVersion 1 at bytes 9..12 (RootId and
    # HeaderId sit between and are not part of the magic)
    if not _is_nrbf_head(data):
        sys.exit("nrbf: %s does not begin with an [MS-NRBF] "
                 "SerializationHeaderRecord (record 0, MajorVersion 1)"
                 % os.path.basename(a.path))
    if a.census:
        census.members = a.members
        return census(data, os.path.basename(a.path))
    try:
        return report(data, a.path)
    except NrbfError as e:
        sys.exit("nrbf: REFUSED %s -- %s" % (os.path.basename(a.path), e))


if __name__ == "__main__":
    sys.exit(main())
