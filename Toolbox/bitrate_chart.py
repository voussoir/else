'''
   bitrate |          01 |        1:00 |       30:00 |     1:00:00 |     1:30:00 |     2:00:00
        -: |          -: |          -: |          -: |          -: |          -: |          -:
  128 kbps |  16.000 KiB | 960.000 KiB |  28.125 MiB |  56.250 MiB |  84.375 MiB | 112.500 MiB
  256 kbps |  32.000 KiB |   1.875 MiB |  56.250 MiB | 112.500 MiB | 168.750 MiB | 225.000 MiB
  320 kbps |  40.000 KiB |   2.344 MiB |  70.312 MiB | 140.625 MiB | 210.938 MiB | 281.250 MiB
  500 kbps |  62.500 KiB |   3.662 MiB | 109.863 MiB | 219.727 MiB | 329.590 MiB | 439.453 MiB
  640 kbps |  80.000 KiB |   4.688 MiB | 140.625 MiB | 281.250 MiB | 421.875 MiB | 562.500 MiB
  738 kbps |  92.250 KiB |   5.405 MiB | 162.158 MiB | 324.316 MiB | 486.475 MiB | 648.633 MiB
 1024 kbps | 128.000 KiB |   7.500 MiB | 225.000 MiB | 450.000 MiB | 675.000 MiB | 900.000 MiB
 2048 kbps | 256.000 KiB |  15.000 MiB | 450.000 MiB | 900.000 MiB |   1.318 GiB |   1.758 GiB
 2330 kbps | 291.271 KiB |  17.067 MiB | 512.000 MiB |   1.000 GiB |   1.500 GiB |   2.000 GiB
 3072 kbps | 384.000 KiB |  22.500 MiB | 675.000 MiB |   1.318 GiB |   1.978 GiB |   2.637 GiB
 4096 kbps | 512.000 KiB |  30.000 MiB | 900.000 MiB |   1.758 GiB |   2.637 GiB |   3.516 GiB
 4660 kbps | 582.543 KiB |  34.133 MiB |   1.000 GiB |   2.000 GiB |   3.000 GiB |   4.000 GiB
 6144 kbps | 768.000 KiB |  45.000 MiB |   1.318 GiB |   2.637 GiB |   3.955 GiB |   5.273 GiB
 8192 kbps |   1.000 MiB |  60.000 MiB |   1.758 GiB |   3.516 GiB |   5.273 GiB |   7.031 GiB
12288 kbps |   1.500 MiB |  90.000 MiB |   2.637 GiB |   5.273 GiB |   7.910 GiB |  10.547 GiB
16384 kbps |   2.000 MiB | 120.000 MiB |   3.516 GiB |   7.031 GiB |  10.547 GiB |  14.062 GiB
'''
import sys
import kbps

from voussoirkit import bytestring

times = ['01', '1:00', '30:00', '1:00:00', '1:30:00', '2:00:00']
rates = [128, 256, 320, 500, 640, 738, 1024, 2048, 3072, 4096, 6144, 8192, 12288, 16384, 2330.17, 4660.34]

times.sort(key=lambda x: kbps.hms_s(x))
rates.sort()

table = []
table.append('bitrate | ' + ' | '.join(times))
table.append('-: | ' * (len(times)+1))
for r in rates:
    l = []
    l.append('%d kbps' % r)
    for t in times:
            l.append(kbps.kbps(time=t, kbps=r))
    l = ' | '.join(l)
    table.append(l)

#print('\n'.join(table))
columns = [[b.strip() for b in a] for a in zip(*[x.split('|') for x in table])]
for (index, column) in enumerate(columns):
  width = max((len(x) for x in column))
  columns[index] = [x.rjust(width, ' ') for x in column]
table = [' | '.join(a) for a in zip(*columns)]
#print(columns)
print('\n'.join(table))