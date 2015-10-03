'''
Drag multiple files on top of this .py file. The first file will have its
name randomly scrambled into 12 digits. The others will increment that number b
1.
'''

import os
import random
import string
import sys

argv = sys.argv[1:]
print(argv)

randname = [random.choice(string.digits) for x in range(12)]
randname = int(''.join(randname))
for originalname in argv:
    folder = os.path.dirname(originalname)
    basename = os.path.basename(originalname)
    extension = basename.split('.')[-1]
    newname = randname
    randname += 1
    newname = '%s/%d.%s' % (folder, newname, extension)
    print('%s -> %s' % (originalname, newname))
    os.rename(originalname, newname)