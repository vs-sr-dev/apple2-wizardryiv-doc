"""Find ProTracker modules embedded in an executable by their 'M.K.' tag,
then measure each one from its own headers to get its true length."""
import sys, struct, re, os
d = open(sys.argv[1], 'rb').read()
out = sys.argv[2] if len(sys.argv) > 2 else None
for m in re.finditer(rb'M\.K\.', d):
    o = m.start() - 1080
    if o < 0: continue
    slen = [struct.unpack_from('>H', d, o+20+i*30+22)[0]*2 for i in range(31)]
    songlen = d[o+950]
    if not (1 <= songlen <= 128) or d[o+951] != 127: continue
    order = d[o+952:o+1080]
    npat = max(order[:songlen]) + 1
    size = 1084 + npat*1024 + sum(slen)
    if o + size > len(d): continue
    title = d[o:o+20].rstrip(b'\0').decode('latin-1', 'replace')
    print('  @0x%06X  %7d bytes  %2d patterns  %2d samples  title=%r'
          % (o, size, npat, sum(1 for s in slen if s), title))
    if out:
        os.makedirs(out, exist_ok=True)
        open('%s/%s_%06X.mod' % (out, os.path.basename(sys.argv[1]), o), 'wb').write(d[o:o+size])
