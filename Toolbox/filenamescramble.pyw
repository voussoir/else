'''
Drag a file on top of this .py file, and it will have its
filename scrambled into a combination of 16 upper and lowercase
letters.
'''

import os
import random
import string
import sys

argv = sys.argv[1:]
print(''.join(c for c in argv if c in string.printable))
for filepath in argv:
    folder = os.path.dirname(filepath)
    basename = os.path.basename(filepath)
    extension = os.path.splitext(basename)[1]
    newname = [random.choice(string.ascii_letters) for x in range(16)]
    newname = ''.join(newname)
    newname = '%s\\%s%s' % (folder, newname, extension)
    os.rename(filepath, newname)
    print('%s -> %s' % (filepath, newname))