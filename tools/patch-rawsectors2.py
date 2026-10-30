#!/usr/bin/env python3
"""Make tools/rawsectors.py verify every sector's identity and retry.

Why.  Two consecutive dumps of the same 918 sectors produced two different
results.  The first reported sixteen all-zero sectors at LBA 0..15; the second
reported LBA 0..4 carrying the headers of LBA 241..245.  Neither is a property
of the disc: the descrambled MODE1 header contains the sector's own address, and
in both runs it disagreed with the address that had been asked for.  The drive
is returning stale or misplaced data on the first transfer after a seek.

A dumper that writes 2048 bytes per sector without looking cannot see this at
all, which is the point: on this disc the header check is available for free
because the sectors have to be descrambled anyway, so every sector can prove its
own identity.  This patch makes the tool

  * check sync, header LBA and EDC on every sector, and
  * re-read any sector that fails, singly, up to RETRIES times, and
  * record what needed retrying, so the retries appear in the notes as a
    property of the read rather than being silently smoothed away.

Anchors are asserted unique; nothing is written if they are not.
"""
import io

P = 'tools/rawsectors.py'
s = io.open(P, encoding='utf-8').read()

anchor = """def main():"""
assert s.count(anchor) == 1, "main() anchor not unique"

helper = '''RETRIES = 8


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


def main():'''

s = s.replace(anchor, helper, 1)

# route every failing sector through read_verified in the chunked path
old = """        for j in range(n):
            a = analyse(blk[j * 2352:(j + 1) * 2352], lba + j)
            modes[a['mode']] = modes.get(a['mode'], 0) + 1
            if not a['sync']:
                bad_sync += 1
            if not a['edc_ok']:
                bad_edc += 1
                if bad_edc <= 10:
                    print("LBA %-6d EDC MISMATCH stored=%08X calc=%08X"
                          % (lba + j, a['edc_stored'], a['edc_calc']))
            if not a['lba_ok']:
                bad_lba += 1
                print("LBA %-6d header says %d (%s)" % (lba + j, a['lba'], a['msf']))
            if cmd == 'scan' and (lba + j) % 128 == 0:
                print("LBA %-6d %s mode=%d edc=%s" % (lba + j, a['msf'], a['mode'],
                                                     "OK" if a['edc_ok'] else "BAD"))
            if fh:
                fh.write(a['user'] if cmd == 'dump' else a['full'])
        lba += n"""
new = """        for j in range(n):
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
        lba += n"""
assert s.count(old) == 1, "chunk loop anchor not unique"
s = s.replace(old, new, 1)

# the single-sector fallback path gets the same treatment
old2 = """            for j in range(n):
                b1 = read_sectors(h, lba + j, 1, off)
                if b1 is None:
                    print("LBA %d UNREADABLE" % (lba + j))
                    if fh:
                        fh.write(b'\\x00' * (2048 if cmd == 'dump' else 2352))
                    continue
                a = analyse(b1, lba + j)
                modes[a['mode']] = modes.get(a['mode'], 0) + 1
                if not a['sync']:
                    bad_sync += 1
                if not a['edc_ok']:
                    bad_edc += 1
                if not a['lba_ok']:
                    bad_lba += 1
                if fh:
                    fh.write(a['user'] if cmd == 'dump' else a['full'])
            lba += n
            continue"""
new2 = """            for j in range(n):
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
            continue"""
assert s.count(old2) == 1, "fallback anchor not unique"
s = s.replace(old2, new2, 1)

old3 = """    bad_sync = bad_edc = bad_lba = 0
    modes = {}"""
new3 = """    retried, unreadable = [], []
    modes = {}"""
assert s.count(old3) == 1, "counter anchor not unique"
s = s.replace(old3, new3, 1)

old4 = """    print("  bad sync: %d   header LBA mismatches: %d   EDC failures: %d"
          % (bad_sync, bad_lba, bad_edc))"""
new4 = """    print("  every sector verified on sync, header address and EDC")
    print("  sectors that needed a re-read: %d%s"
          % (len(retried), (" -> " + ", ".join(
              "%d(x%d)" % (r['lba'], r['attempts']) for r in retried[:20]))
             if retried else ""))
    print("  sectors unreadable after %d attempts: %d%s"
          % (RETRIES, len(unreadable),
             (" -> " + ", ".join(str(u['lba']) for u in unreadable[:20]))
             if unreadable else ""))"""
assert s.count(old4) == 1, "summary anchor not unique"
s = s.replace(old4, new4, 1)

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print("patched %s" % P)
