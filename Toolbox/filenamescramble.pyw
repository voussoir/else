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
print(argv)
for originalname in argv:
    folder = os.path.dirname(originalname)
    basename = os.path.basename(originalname)
    extension = basename.split('.')[-1]
    newname = [random.choice(string.ascii_letters) for x in range(16)]
    newname = ''.join(newname)
    newname = '%s/%s.%s' % (folder, newname, extension)
    print('%s -> %s' % (originalname, newname))
    os.rename(originalname, newname)