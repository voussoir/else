import math
import random
import sys
import bytestring
CHUNK_SIZE = 512 * (2 ** 10)
def listget(li, index, fallback=None):
    try:
        return li[index]
    except IndexError:
        return fallback

def rid(length=8):
    import random
    bits = length * 4
    bits = random.getrandbits(bits)
    identifier = '{:02x}'.format(bits).rjust(length, '0')
    return identifier

def make_randomfile(length, filename=None):
    if filename is None:
        filename = rid(8) + '.txt'
    chunks = math.ceil(length / CHUNK_SIZE)
    written = 0
    f = open(filename, 'w')
    for x in range(chunks):
        b = min(CHUNK_SIZE, length-written)
        f.write(rid(b))
        written += b
    f.close()
    print('Created %s' % filename)


bytes = listget(sys.argv, 1, None)
if bytes is None:
    bytes = 2 ** 10
else:
    bytes = bytestring.parsebytes(bytes)

filecount = 1
filename = listget(sys.argv, 2, None)
if filename is not None and filename.isdigit():
    filecount = int(filename)
    filename = None

for x in range(filecount):
    make_randomfile(bytes, filename)