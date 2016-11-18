from voussoirkit import bytestring
import downloady
import ratemeter
import requests
import sys
import time

if len(sys.argv) == 2:
    URL = sys.argv[1]
else:
    URL = 'http://cdn.speedof.me/sample32768k.bin?r=0.881750426312'
METER = ratemeter.RateMeter(span=5)
METER_2 = ratemeter.RateMeter(span=None)
class G:
    pass

g = G()
g.total = 0
g.start = None
g.last = time.time()

class P:
    def __init__(self, bytes_total):
        self.bytes_total = bytes_total
    def step(self, bytes_downloaded):
        if g.start is None:
            g.start = time.time()
        percent = 100 * bytes_downloaded / self.bytes_total
        percent = '%07.3f%%:' % percent
        chunk = bytes_downloaded - g.total
        g.total = bytes_downloaded
        METER.digest(chunk)
        METER_2.digest(chunk)
        now = round(time.time(), 1)
        if now > g.last or (bytes_downloaded >= self.bytes_total):
            g.last = now
            percent = percent.rjust(9, ' ')
            rate = bytestring.bytestring(METER.report()[2]).rjust(15, ' ')
            rate2 = bytestring.bytestring(METER_2.report()[2]).rjust(15, ' ')
            elapsed = str(round(now-g.start, 1)).rjust(10, ' ')
            print(percent, rate, rate2, elapsed, end='\r', flush=True)
            #print(METER.report(), METER_2.report())

print(URL)
print('Progress'.rjust(9, ' '), 'bps over 5s'.rjust(15, ' '), 'bps overall'.rjust(15, ' '), 'elapsed'.rjust(10, ' '))
downloady.download_file(URL, 'nul', callback_progress=P)