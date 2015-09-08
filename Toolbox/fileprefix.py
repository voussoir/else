'''
When you run this file from the commandline given a single argument, all
of the files in the current working directory will be renamed in the format
{argument}_{count} where argument is your cmd input and count is a zero-padded
integer that counts each file in the folder.
'''

import os
import random
import string
import re
import sys

assert len(sys.argv) == 2

prefix = sys.argv[1]
files = [os.path.abspath(x) for x in os.listdir()]
files = [item for item in files if os.path.isfile(item)]
if __file__ in files:
    files.remove(__file__)

# trust me on this.
zeropadding = len(str(len(files)))
zeropadding = max(2, zeropadding)
zeropadding = str(zeropadding)

format = '%s_%0{pad}d%s'.format(pad=zeropadding)
print(format)

def natural_sort(l):
    '''
    http://stackoverflow.com/a/11150413
    '''
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)] 
    return sorted(l, key=alphanum_key)

files = natural_sort(files)
for (fileindex, filename) in enumerate(files):
    if '.' in filename:
        extension = '.' + filename.split('.')[-1]
    else:
        extension = ''
    newname = format % (prefix, fileindex, extension)
    print(''.join([c for c in filename if c in string.printable]), '->', newname)
    os.rename(filename, newname)