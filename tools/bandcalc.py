#!/usr/bin/env python3
"""The three figures for the band (platform notes, section 10), by category.

  on disc    bytes of the file in the ISO 9660 volume
  resident   bytes after every packed stream inside it is unpacked, all levels
  used       resident minus the trailing zeros of each blob -- buffer slack

The band measures the GAME, so the categories matter: streamed CDXL video and
the bundled second title have to come out before the figure is comparable with
the other fourteen discs.  Slack is reported per file as well as in total,
because on Universe a 0.5% total hid two files at 48% and 49%.

Usage:  python3 tools/bandcalc.py <iso-dir> <unpacked-dir>
"""
import sys, os, collections

VIDEO = {"cdintro.xl", "INTRO.XL", "piratesgold.intro.xl"}
PIRATES = {"pirates", "pirates_german", "Pirates.font", "pirates.demo",
           "piratesgold.intro.xl"}
OS_FILES = {"setpatch", "Assign", "avail", "Status", "Break", "execute", "wait",
            "filteron", "filteroff", "getlang", "diskfont.library",
            "iffparse.library", "locale.library", "cdgsxl", "CDGSXL"}


def used_of(b):
    i = len(b)
    while i and b[i - 1] == 0:
        i -= 1
    return i


def main():
    iso, unp = sys.argv[1], sys.argv[2]
    # resident bytes contributed by unpacking, per top-level file name
    gain = collections.defaultdict(int)
    for d in sorted(os.listdir(unp)) if os.path.isdir(unp) else []:
        sub = os.path.join(unp, d)
        if not os.path.isdir(sub):
            continue
        for dp, dn, fn in os.walk(sub):
            for f in fn:
                if ".gap" in f:
                    continue
                gain[d] += os.path.getsize(os.path.join(dp, f))

    rows = []
    for dp, dn, fn in os.walk(iso):
        for f in sorted(fn):
            p = os.path.join(dp, f)
            b = open(p, "rb").read()
            name = f
            rel = os.path.relpath(p, iso).replace(os.sep, "/")
            packed_out = gain.get(name, 0)
            if packed_out:
                # resident = raw parts + unpacked parts.  Approximate the raw part as
                # the file minus its packed streams; bandcalc reports the sum, which
                # is what "resident" means for a container.
                resident = len(b) + packed_out
            else:
                resident = len(b)
            used = used_of(b) + packed_out
            cat = "video" if name in VIDEO else ("pirates" if name in PIRATES else
                                                 ("os" if name in OS_FILES else "game"))
            rows.append((rel, name, cat, len(b), resident, used))

    print("%-9s %5s %12s %12s %12s  %s" % ("category", "files", "on disc", "resident", "used", ""))
    agg = collections.defaultdict(lambda: [0, 0, 0, 0])
    for rel, name, cat, d0, r0, u0 in rows:
        a = agg[cat]
        a[0] += 1; a[1] += d0; a[2] += r0; a[3] += u0
    for cat in ("game", "os", "video", "pirates"):
        a = agg[cat]
        print("%-9s %5d %12d %12d %12d" % (cat, a[0], a[1], a[2], a[3]))
    tot = [sum(agg[c][i] for c in agg) for i in range(4)]
    print("%-9s %5d %12d %12d %12d" % ("TOTAL", tot[0], tot[1], tot[2], tot[3]))
    print()

    g = agg["game"]
    go = agg["os"]
    print("GAME ONLY (excludes streamed video, the bundled Pirates! Gold demo,")
    print("           and the stock Commodore/OS binaries):")
    print("   on disc  %10d bytes = %.2f MiB" % (g[1], g[1] / 1048576.0))
    print("   resident %10d bytes = %.2f MiB" % (g[2], g[2] / 1048576.0))
    print("   used     %10d bytes = %.2f MiB" % (g[3], g[3] / 1048576.0))
    print("   slack    %10d bytes = %.2f%% of resident"
          % (g[2] - g[3], 100.0 * (g[2] - g[3]) / max(1, g[2])))
    print()
    print("GAME + OS binaries:")
    print("   on disc  %10d bytes = %.2f MiB" % (g[1] + go[1], (g[1] + go[1]) / 1048576.0))
    print("   resident %10d bytes = %.2f MiB" % (g[2] + go[2], (g[2] + go[2]) / 1048576.0))
    print()
    print("per-file slack, worst 15 (resident vs used):")
    sl = [(r0 - u0, 100.0 * (r0 - u0) / max(1, r0), rel, r0)
          for rel, name, cat, d0, r0, u0 in rows if r0 > 1024]
    sl.sort(reverse=True)
    print("%12s %7s %12s  %s" % ("slack bytes", "pct", "resident", "file"))
    for nb, pct, rel, r0 in sl[:15]:
        print("%12d %6.1f%% %12d  %s" % (nb, pct, r0, rel))


if __name__ == "__main__":
    main()
