'''
Drag multiple files on top of this .py file. The first file will have its
name randomly scrambled into 12 digits. The others will increment that number b
1.
'''

print('hi')
import os
import random
import string
import sys

argv = sys.argv[1:]
print(''.join(c for c in argv if c in string.printable))

randname = [random.choice(string.digits) for x in range(12)]
randname = int(''.join(randname))
for filepath in argv:
    folder = os.path.dirname(filepath)
    basename = os.path.basename(filepath)
    extension = os.path.splitext(basename)[1]
    newname = str(randname).rjust(12, '0')
    randname += 1
    newname = '%s\\%s%s' % (folder, newname, extension)
    os.rename(filepath, newname)
    print('%s -> %s' % (filepath, newname))