#!/usr/bin/env python3
"""rawcd.py -- read a physical CD from a Windows optical drive, at the level
below the mounted file system.

Written for the Alfred Chicken (CD32) pipeline, which is the first disc of the
set that is a physical disc rather than an image file.  Everything the mounted
ISO 9660 view on E:\\ hides -- the TOC, the MCN and ISRC subchannel fields, the
system area, the real sector mode, the physical length of the disc, and read
errors -- is only reachable through DeviceIoControl on \\\\.\\E:.

The drive is opened READ ONLY and nothing is ever written to it.

Subcommands:
    toc              read and print the TOC (both LBA and MSF), plus FULL TOC
    q                read MCN (media catalog) and per-track ISRC
    mode LBA [N]     read N sectors raw (2352 B) and report the sector mode
    dumpdata OUT     dump the data track at 2048 B/sector, logging read errors
    dumpaudio OUT T  dump audio track T at 2352 B/sector
    verify A B       byte-compare two dumps and report the first difference

Every number this tool prints comes from a device read.  Nothing is inherited
from a .cue file written by someone else.
"""
import sys, os, ctypes, json, hashlib
from ctypes import wintypes

# ---------------------------------------------------------------- Win32 glue

GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

# CTL_CODE(FILE_DEVICE_CD_ROM=0x2, function, method, FILE_READ_ACCESS=1)
def ctl_code(function, method=0, access=1):
    return (0x2 << 16) | (access << 14) | (function << 2) | method

IOCTL_CDROM_READ_TOC_EX     = ctl_code(0x15)          # 0x24054
IOCTL_CDROM_READ_Q_CHANNEL  = ctl_code(0x0B)          # 0x2402C
IOCTL_CDROM_RAW_READ        = ctl_code(0x0F, 2)       # 0x2403E, METHOD_OUT_DIRECT
IOCTL_CDROM_GET_LAST_SESSION= ctl_code(0x0E)
IOCTL_STORAGE_GET_MEDIA_TYPES_EX = (0x2D << 16) | (0 << 14) | (0x0301 << 2) | 0

k32 = ctypes.WinDLL('kernel32', use_last_error=True)
k32.CreateFileW.restype = wintypes.HANDLE
k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                            ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
                            wintypes.HANDLE]
k32.DeviceIoControl.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p,
                                wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD,
                                ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
k32.ReadFile.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                         ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
k32.SetFilePointerEx.argtypes = [wintypes.HANDLE, ctypes.c_longlong,
                                 ctypes.POINTER(ctypes.c_longlong), wintypes.DWORD]


def open_drive(letter):
    path = "\\\\.\\%s:" % letter
    h = k32.CreateFileW(path, GENERIC_READ,
                        FILE_SHARE_READ | FILE_SHARE_WRITE,
                        None, OPEN_EXISTING, 0, None)
    if h == INVALID_HANDLE_VALUE or h is None:
        err = ctypes.get_last_error()
        raise SystemExit(
            "CreateFileW(%s) failed, GetLastError=%d%s" % (
                path, err,
                "  -- access denied: raw device reads need an elevated shell."
                if err == 5 else ""))
    return h


def ioctl(h, code, inbuf, outlen):
    out = ctypes.create_string_buffer(outlen)
    ret = wintypes.DWORD(0)
    ib = ctypes.create_string_buffer(inbuf) if inbuf else None
    ok = k32.DeviceIoControl(h, code, ib, len(inbuf) if inbuf else 0,
                             out, outlen, ctypes.byref(ret), None)
    if not ok:
        return None, ctypes.get_last_error()
    return out.raw[:ret.value], 0


# ---------------------------------------------------------------------- TOC

def msf(b0, b1, b2):
    return "%02d:%02d:%02d" % (b0, b1, b2)


def msf_to_lba(m, s, f):
    return (m * 60 + s) * 75 + f - 150


def read_toc(h, fmt=0, msf_flag=0, session_track=0):
    """CDROM_READ_TOC_EX: Format:4 Reserved1:3 Msf:1 | SessionTrack | 2 rsvd"""
    b0 = (fmt & 0x0F) | ((msf_flag & 1) << 7)
    inbuf = bytes([b0, session_track, 0, 0])
    return ioctl(h, IOCTL_CDROM_READ_TOC_EX, inbuf, 4096)


def parse_toc(raw):
    length = (raw[0] << 8) | raw[1]
    first, last = raw[2], raw[3]
    tracks = []
    off = 4
    while off + 8 <= len(raw):
        rsvd, adrctl, num, rsvd1 = raw[off], raw[off+1], raw[off+2], raw[off+3]
        addr = raw[off+4:off+8]
        tracks.append(dict(adr=(adrctl >> 4) & 0xF, control=adrctl & 0xF,
                           track=num, addr=list(addr)))
        off += 8
    return dict(length=length, first=first, last=last, tracks=tracks)


def control_words(c):
    w = []
    w.append("data" if (c & 0x4) else "audio")
    if c & 0x1:
        w.append("pre-emphasis" if not (c & 0x4) else "incremental")
    else:
        w.append("no pre-emphasis" if not (c & 0x4) else "uninterrupted")
    w.append("copy permitted" if (c & 0x2) else "copy prohibited")
    if not (c & 0x4):
        w.append("four-channel" if (c & 0x8) else "two-channel")
    return ", ".join(w)


def cmd_toc(h, args):
    out = {}
    raw_lba, err = read_toc(h, 0, 0)
    if raw_lba is None:
        raise SystemExit("READ_TOC_EX(format 0, LBA) failed, err=%d" % err)
    raw_msf, _ = read_toc(h, 0, 1)
    t = parse_toc(raw_lba)
    tm = parse_toc(raw_msf)
    print("TOC: length field %d, first track %d, last track %d"
          % (t['length'], t['first'], t['last']))
    print()
    print("  trk  ADR CTRL  LBA        MSF        kind")
    rows = []
    for a, b in zip(t['tracks'], tm['tracks']):
        lba = int.from_bytes(bytes(a['addr']), 'big', signed=True)
        m, s, f = b['addr'][1], b['addr'][2], b['addr'][3]
        name = "lead-out" if a['track'] == 0xAA else str(a['track'])
        print("  %-4s %d   0x%X   %-10d %s  %s"
              % (name, a['adr'], a['control'], lba, msf(m, s, f),
                 control_words(a['control'])))
        rows.append(dict(track=name, adr=a['adr'], control=a['control'],
                         lba=lba, msf=msf(m, s, f),
                         msf_lba=msf_to_lba(m, s, f)))
    out['toc'] = rows
    out['toc_raw_lba'] = raw_lba.hex()
    out['toc_raw_msf'] = raw_msf.hex()

    for fmt, nm in ((1, 'session'), (2, 'full_toc'), (3, 'pma'),
                    (4, 'atip'), (5, 'cdtext')):
        r, e = read_toc(h, fmt, 0)
        if r is None:
            print("\n%s: not available (err %d)" % (nm, e))
            out[nm] = None
        else:
            print("\n%s: %d bytes" % (nm, len(r)))
            print("  " + r.hex())
            out[nm] = r.hex()
    print()
    print(json.dumps(out))
    return out


# ------------------------------------------------------------ subchannel Q

def cmd_q(h, args):
    res = {}
    # MCN, format 0x02
    r, e = ioctl(h, IOCTL_CDROM_READ_Q_CHANNEL, bytes([0x02, 0]), 64)
    if r is None:
        print("MCN: IOCTL failed, err=%d" % e)
        res['mcn'] = None
    else:
        # SUB_Q_HEADER(4) FormatCode(1) Reserved[3] flags(1) MediaCatalog[15]
        fmtcode = r[4]
        mcval = (r[8] >> 7) & 1
        cat = r[9:24].split(b'\x00')[0].decode('ascii', 'replace')
        print("MCN: raw=%s" % r.hex())
        print("  FormatCode=0x%02X  MCVAL=%d  MediaCatalog=%r" % (fmtcode, mcval, cat))
        res['mcn'] = dict(raw=r.hex(), mcval=mcval, catalog=cat)

    # ISRC per track -- needs the track count
    raw_lba, _ = read_toc(h, 0, 0)
    t = parse_toc(raw_lba)
    res['isrc'] = {}
    for tr in range(t['first'], t['last'] + 1):
        r, e = ioctl(h, IOCTL_CDROM_READ_Q_CHANNEL, bytes([0x03, tr]), 64)
        if r is None:
            print("ISRC track %d: IOCTL failed, err=%d" % (tr, e))
            res['isrc'][tr] = None
            continue
        tcval = (r[8] >> 7) & 1
        isrc = r[9:24].split(b'\x00')[0].decode('ascii', 'replace')
        print("ISRC track %d: raw=%s" % (tr, r.hex()))
        print("  TCVAL=%d  ISRC=%r" % (tcval, isrc))
        res['isrc'][tr] = dict(raw=r.hex(), tcval=tcval, isrc=isrc)
    print()
    print(json.dumps(res))
    return res


# ----------------------------------------------------------------- raw read

TRACK_MODE = dict(YellowMode2=0, XAForm2=1, CDDA=2)


def raw_read(h, lba, count, mode='YellowMode2'):
    """RAW_READ_INFO { LARGE_INTEGER DiskOffset; ULONG SectorCount;
                       TRACK_MODE_TYPE TrackMode; }  -- 16 bytes, packed 8."""
    size = 2352 * count
    inbuf = (ctypes.c_longlong(lba * 2048).value).to_bytes(8, 'little') + \
            count.to_bytes(4, 'little') + \
            TRACK_MODE[mode].to_bytes(4, 'little')
    return ioctl(h, IOCTL_CDROM_RAW_READ, inbuf, size)


def bcd(b):
    return (b >> 4) * 10 + (b & 0xF)


def cmd_mode(h, args):
    lba = int(args[0]); n = int(args[1]) if len(args) > 1 else 4
    print("raw read (2352 B/sector, YellowMode2) from LBA %d, %d sectors\n" % (lba, n))
    for i in range(n):
        r, e = raw_read(h, lba + i, 1)
        if r is None:
            print("  LBA %-7d RAW READ FAILED err=%d" % (lba + i, e))
            continue
        sync = r[0:12]
        hdr = r[12:16]
        ok_sync = sync == b'\x00' + b'\xff' * 10 + b'\x00'
        want = lba + i + 150
        got = (bcd(hdr[0]) * 60 + bcd(hdr[1])) * 75 + bcd(hdr[2]) - 150
        print("  LBA %-7d sync=%s header=%s  MSF=%02d:%02d:%02d (LBA %d) MODE=%d%s"
              % (lba + i, "OK" if ok_sync else sync.hex(), hdr.hex(),
                 bcd(hdr[0]), bcd(hdr[1]), bcd(hdr[2]), got, hdr[3],
                 "" if got == lba + i else "  <-- header LBA mismatch, want %d" % (lba+i)))
        if i == 0:
            print("     first 64 B of user data: %s" % r[16:80].hex())
    return None


# ------------------------------------------------------------------- dumps

def cmd_dumpdata(h, args):
    out = args[0]
    start = int(args[1]) if len(args) > 1 else 0
    end = int(args[2])           # exclusive
    chunk = 64
    errors = []
    got = 0
    with open(out, 'wb') as f:
        lba = start
        while lba < end:
            n = min(chunk, end - lba)
            off = ctypes.c_longlong(lba * 2048)
            k32.SetFilePointerEx(h, off, None, 0)
            buf = ctypes.create_string_buffer(n * 2048)
            rd = wintypes.DWORD(0)
            ok = k32.ReadFile(h, buf, n * 2048, ctypes.byref(rd), None)
            if ok and rd.value == n * 2048:
                f.write(buf.raw[:rd.value]); got += n; lba += n
                if (lba - start) % 8192 == 0:
                    sys.stderr.write("  %d/%d sectors\r" % (lba - start, end - start))
                continue
            # fall back to one sector at a time to localise the failure
            for j in range(n):
                s = lba + j
                data = None
                tries = 0
                for tries in range(1, 4):
                    off = ctypes.c_longlong(s * 2048)
                    k32.SetFilePointerEx(h, off, None, 0)
                    b1 = ctypes.create_string_buffer(2048)
                    rd = wintypes.DWORD(0)
                    if k32.ReadFile(h, b1, 2048, ctypes.byref(rd), None) and rd.value == 2048:
                        data = b1.raw[:2048]
                        break
                if data is None:
                    err = ctypes.get_last_error()
                    errors.append(dict(lba=s, tries=tries, err=err))
                    sys.stderr.write("  LBA %d UNREADABLE after %d tries (err %d)\n"
                                     % (s, tries, err))
                    f.write(b'\x00' * 2048)
                else:
                    if tries > 1:
                        errors.append(dict(lba=s, tries=tries, err=0,
                                           note="recovered on retry %d" % tries))
                    f.write(data); got += 1
            lba += n
    sys.stderr.write("\n")
    print("wrote %s: %d sectors requested, %d read clean, %d error entries"
          % (out, end - start, got, len(errors)))
    if errors:
        print(json.dumps(errors))
    h_ = hashlib.sha1(open(out, 'rb').read()).hexdigest()
    print("sha1 %s  size %d" % (h_, os.path.getsize(out)))
    return errors


def cmd_dumpaudio(h, args):
    out = args[0]; start = int(args[1]); end = int(args[2])
    errors = []
    with open(out, 'wb') as f:
        lba = start
        while lba < end:
            n = min(16, end - lba)
            r, e = raw_read(h, lba, n, 'CDDA')
            if r is not None and len(r) == n * 2352:
                f.write(r); lba += n; continue
            for j in range(n):
                r1, e1 = raw_read(h, lba + j, 1, 'CDDA')
                if r1 is None or len(r1) != 2352:
                    errors.append(dict(lba=lba + j, err=e1))
                    f.write(b'\x00' * 2352)
                else:
                    f.write(r1)
            lba += n
    print("wrote %s: %d sectors, %d errors" % (out, end - start, len(errors)))
    if errors:
        print(json.dumps(errors[:50]))
    return errors


def cmd_verify(h, args):
    a, b = args[0], args[1]
    da = open(a, 'rb').read(); db = open(b, 'rb').read()
    print("%s: %d B sha1 %s" % (a, len(da), hashlib.sha1(da).hexdigest()))
    print("%s: %d B sha1 %s" % (b, len(db), hashlib.sha1(db).hexdigest()))
    if da == db:
        print("IDENTICAL: the two passes agree byte for byte")
        return
    n = min(len(da), len(db))
    diffs = [i for i in range(n) if da[i] != db[i]]
    print("DIFFER: %d byte positions, first at %d (sector %d)"
          % (len(diffs), diffs[0], diffs[0] // 2048))
    secs = sorted(set(i // 2048 for i in diffs))
    print("sectors affected: %d -> %s" % (len(secs), secs[:40]))


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    letter, cmd, args = sys.argv[1], sys.argv[2], sys.argv[3:]
    if cmd == 'verify':
        return cmd_verify(None, args)
    h = open_drive(letter)
    try:
        return dict(toc=cmd_toc, q=cmd_q, mode=cmd_mode, dumpdata=cmd_dumpdata,
                    dumpaudio=cmd_dumpaudio)[cmd](h, args)
    finally:
        ctypes.windll.kernel32.CloseHandle(h)


if __name__ == '__main__':
    main()
