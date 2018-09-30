'''
This module is designed to provide a GOOD ENOUGH means of identifying duplicate
files very quickly, so that more in-depth checks can be done on likely matches.
'''

import hashlib
import os
import sys

SEEK_END = 2
CHUNK_SIZE = 2 * 2**20
FORMAT = '{size}_{chunk_size}_{hash}'

def equal(handle1, handle2, *args, **kwargs):
    size1 = handle1.seek(0, SEEK_END)
    size2 = handle2.seek(0, SEEK_END)
    handle1.seek(0)
    handle2.seek(0)
    if size1 != size2:
        return False
    return quickid(handle1, *args, **kwargs) == quickid(handle2, *args, **kwargs)

def equal_file(filename1, filename2, *args, **kwargs):
    filename1 = os.path.abspath(filename1)
    filename2 = os.path.abspath(filename2)
    with open(filename1, 'rb') as handle1, open(filename2, 'rb') as handle2:
        return equal(handle1, handle2, *args, **kwargs)

def quickid(handle, hashclass=None, chunk_size=None):
    if hashclass is None:
        hashclass = hashlib.md5
    if chunk_size is None:
        chunk_size = CHUNK_SIZE

    hasher = hashclass()
    size = handle.seek(0, SEEK_END)
    handle.seek(0)

    if size <= 2 * chunk_size:
        hasher.update(handle.read())
    else:
        hasher.update(handle.read(chunk_size))
        handle.seek(-1 * chunk_size, SEEK_END)
        hasher.update(handle.read())

    return FORMAT.format(size=size, chunk_size=chunk_size, hash=hasher.hexdigest())

def quickid_file(filename, *args, **kwargs):
    filename = os.path.abspath(filename)
    with open(filename, 'rb') as handle:
        return quickid(handle, *args, **kwargs)

def main(argv):
    print(quickid_file(argv[0]))

if __name__ == '__main__':
    main(sys.argv[1:])
