import sys, re
d = open(sys.argv[1], 'rb').read()
pat = bytes.fromhex(sys.argv[2].replace(' ', ''))
hits = [m.start() for m in re.finditer(re.escape(pat), d)]
print('%d hits: %s' % (len(hits), ', '.join('0x%X' % h for h in hits[:40])))
