#!/usr/bin/env python3
"""rawsectors.py -- read MODE1 sectors from a physical CD through the CDDA raw
path, descramble them, and check EDC.

Why this exists.  On the drive used for this disc, IOCTL_CDROM_RAW_READ refuses
TrackMode YellowMode2 and XAForm2 (both return ERROR_INVALID_FUNCTION), and
plain ReadFile on \\\\.\\E: stops at the end of the *logical volume* Windows
mounts -- which on this disc is 227 sectors short of the end of the data track.
Everything past the declared volume is therefore invisible to both of the easy
paths, and that region is exactly what the pipeline exists to look at.

TrackMode CDDA does work, and returns the 2352 bytes as they physically sit on
the disc.  For a data track those bytes are scrambled (ECMA-130 annex B): the
12-byte sync is stored in the clear, everything from byte 12 on is XORed with
the output of a 15-bit LFSR.  Undoing that gives the real sector: header, 2048
bytes of user data, EDC and ECC.

Two drive-level facts this tool measures rather than assumes:

  * read offset.  The buffer returned for LBA N does not start at LBA N.  On
    this drive the sync pattern appears at byte 24, so the drive hands back 24
    bytes of the previous sector first.  The tool finds that offset by looking
    for the sync pattern instead of hardcoding it, and prints it.
  * sector mode.  The descrambled header's fourth byte is the mode.  It is
    checked on every sector, not sampled.

Usage:
  rawsectors.py E scan  FIRST LAST      report sync/header/mode/EDC per sector
  rawsectors.py E dump  FIRST LAST OUT  write 2048 B/sector user data
  rawsectors.py E dumpraw FIRST LAST OUT  write full 2352 B descrambled sectors
"""
import sys, ctypes, hashlib
sys.path.insert(0, __file__.rsplit('\\', 1)[0].rsplit('/', 1)[0])
import rawcd

SYNC = b'\x00' + b'\xff' * 10 + b'\x00'


def scrambler():
    """ECMA-130 annex B: x^15 + x^1 + 1, preset 0x0001, applied from byte 12."""
    reg = 1
    out = bytearray()
    for _ in range(2340):
        b = 0
        for k in range(8):
            b |= (reg & 1) << k
            fb = (reg & 1) ^ ((reg >> 1) & 1)
            reg = (reg >> 1) | (fb << 14)
        out.append(b)
    return bytes(out)


SCR = scrambler()

# EDC: CRC-32 with polynomial x^32+x^31+x^16+x^15+x^4+x^3+x+1, reflected,
# over bytes 0..2063 of a MODE1 sector, stored little-endian at 2064..2067.
def _edc_table():
    t = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = (c >> 1) ^ (0xD8018001 if (c & 1) else 0)
        t.append(c)
    return t


EDCT = _edc_table()


def edc(data):
    c = 0
    for b in data:
        c = (c >> 8) ^ EDCT[(c ^ b) & 0xFF]
    return c


def bcd(b):
    return (b >> 4) * 10 + (b & 0xF)


def find_offset(h, lba=16):
    """Locate the sync pattern in the drive's raw buffer for a known data LBA."""
    r, e = rawcd.raw_read(h, lba, 2, 'CDDA')
    if r is None:
        raise SystemExit("CDDA raw read failed at LBA %d, err=%d" % (lba, e))
    i = r.find(SYNC)
    if i < 0:
        raise SystemExit("sync pattern not found in raw buffer at LBA %d" % lba)
    return i


def read_sectors(h, first, count, off):
    """Return `count` complete 2352-byte raw sectors starting at `first`.

    The drive returns the buffer shifted by `off` bytes, so `count + 1` sectors
    are requested to cover the tail.  Where that crosses a boundary the drive
    refuses (the data-track/pregap edge does exactly this), fall back to two
    independent single-sector reads and splice them."""
    r, e = rawcd.raw_read(h, first, count + 1, 'CDDA')
    if r is not None and len(r) >= off + 2352 * count:
        return r[off:off + 2352 * count]
    if count != 1:
        return None
    a, _ = rawcd.raw_read(h, first, 1, 'CDDA')
    b, _ = rawcd.raw_read(h, first + 1, 1, 'CDDA')
    if a is None:
        return None
    tail = b[:off] if b is not None else bytes(off)
    return (a[off:] + tail)[:2352]


def descramble(sec):
    return sec[:12] + bytes(a ^ b for a, b in zip(sec[12:], SCR))


def analyse(sec, lba):
    d = descramble(sec)
    ok_sync = d[:12] == SYNC
    m, s, f, mode = d[12], d[13], d[14], d[15]
    hdr_lba = (bcd(m) * 60 + bcd(s)) * 75 + bcd(f) - 150
    user = d[16:2064]
    stored = int.from_bytes(d[2064:2068], 'little')
    calc = edc(d[0:2064])
    return dict(sync=ok_sync, msf="%02d:%02d:%02d" % (bcd(m), bcd(s), bcd(f)),
                lba=hdr_lba, lba_ok=(hdr_lba == lba), mode=mode,
                edc_ok=(stored == calc), edc_stored=stored, edc_calc=calc,
                user=user, full=d)


RETRIES = 8


def read_verified(h, lba, off):
    """Read one sector and require it to prove it is the sector asked for.

    Returns (analysis, attempts, history).  `history` lists what each failed
    attempt claimed, so a systematic offset can be told from random noise.
    """
    history = []
    for attempt in range(1, RETRIES + 1):
        sec = read_sectors(h, lba, 1, off)
        if sec is None:
            history.append('read failed')
            continue
        a = analyse(sec, lba)
        if a['sync'] and a['lba_ok'] and a['edc_ok']:
            return a, attempt, history
        history.append('sync=%s hdr=%s edc=%s'
                       % (a['sync'], a['lba'], a['edc_ok']))
    return None, RETRIES, history


def main():
    letter, cmd = sys.argv[1], sys.argv[2]
    first, last = int(sys.argv[3]), int(sys.argv[4])
    out = sys.argv[5] if len(sys.argv) > 5 else None
    h = rawcd.open_drive(letter)
    off = find_offset(h)
    print("drive read offset: sync at byte %d of the returned buffer "
          "(%+d bytes = %+d samples)" % (off, -off, -off // 4), file=sys.stderr)

    retried, unreadable = [], []
    modes = {}
    fh = open(out, 'wb') if out else None
    lba = first
    CH = 26      # this drive refuses raw transfers of 32 sectors or more
    while lba <= last:
        n = min(CH, last - lba + 1)
        blk = read_sectors(h, lba, n, off)
        if blk is None:
            for j in range(n):
                a, attempts, hist = read_verified(h, lba + j, off)
                if a is None:
                    unreadable.append(dict(lba=lba + j, history=hist))
                    print("LBA %-6d UNREADABLE after %d attempts: %s"
                          % (lba + j, RETRIES, "; ".join(hist[:4])))
                    if fh:
                        fh.write(bytes(2048 if cmd == 'dump' else 2352))
                    continue
                if attempts > 1:
                    retried.append(dict(lba=lba + j, attempts=attempts, first='chunk fallback'))
                modes[a['mode']] = modes.get(a['mode'], 0) + 1
                if fh:
                    fh.write(a['user'] if cmd == 'dump' else a['full'])
            lba += n
            continue
        for j in range(n):
            a = analyse(blk[j * 2352:(j + 1) * 2352], lba + j)
            if not (a['sync'] and a['lba_ok'] and a['edc_ok']):
                first_claim = (a['sync'], a['lba'], a['edc_ok'])
                a2, attempts, hist = read_verified(h, lba + j, off)
                if a2 is None:
                    unreadable.append(dict(lba=lba + j, history=hist))
                    print("LBA %-6d UNREADABLE after %d attempts: %s"
                          % (lba + j, RETRIES, "; ".join(hist[:4])))
                    if fh:
                        fh.write(bytes(2048 if cmd == 'dump' else 2352))
                    continue
                retried.append(dict(lba=lba + j, attempts=attempts,
                                    first=str(first_claim)))
                a = a2
            modes[a['mode']] = modes.get(a['mode'], 0) + 1
            if cmd == 'scan' and (lba + j) % 128 == 0:
                print("LBA %-6d %s mode=%d edc=%s" % (lba + j, a['msf'], a['mode'],
                                                     "OK" if a['edc_ok'] else "BAD"))
            if fh:
                fh.write(a['user'] if cmd == 'dump' else a['full'])
        lba += n
    if fh:
        fh.close()
    print("\nsectors %d..%d (%d total)" % (first, last, last - first + 1))
    print("  modes seen: %s" % ", ".join("MODE%d x%d" % (k, v) for k, v in sorted(modes.items())))
    print("  every sector verified on sync, header address and EDC")
    print("  sectors that needed a re-read: %d%s"
          % (len(retried), (" -> " + ", ".join(
              "%d(x%d)" % (r['lba'], r['attempts']) for r in retried[:20]))
             if retried else ""))
    print("  sectors unreadable after %d attempts: %d%s"
          % (RETRIES, len(unreadable),
             (" -> " + ", ".join(str(u['lba']) for u in unreadable[:20]))
             if unreadable else ""))
    if out:
        data = open(out, 'rb').read()
        print("  wrote %s: %d B sha1 %s" % (out, len(data), hashlib.sha1(data).hexdigest()))


if __name__ == '__main__':
    main()
