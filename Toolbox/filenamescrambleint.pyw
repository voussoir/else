'''
Drag a file on top of this .py file, and it will have its
filename scrambled into a combination of 12 digits.
'''

import os
import random
import string
import sys

argv = sys.argv[1:]
print(argv)
for originalname in argv:
    folder = os.path.dirname(originalname)
    basename = os.path.basename(originalname)
    extension = basename.split('.')[-1]
    newname = [random.choice(string.digits) for x in range(12)]
    newname = ''.join(newname)
    newname = '%s/%s.%s' % (folder, newname, extension)
    print('%s -> %s' % (originalname, newname))
    os.rename(originalname, newname)