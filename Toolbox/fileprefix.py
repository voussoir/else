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

assert len(sys.argv) in range(2, 4)

ctime = '-c' in sys.argv
dry = '--dry' in sys.argv

IGNORE_EXTENSIONS = ['.py', '.lnk']

prefix = sys.argv[1]
if prefix != '':
    prefix += '_'
files = [os.path.abspath(x) for x in os.listdir()]
files = [item for item in files if os.path.isfile(item)]
if __file__ in files:
    files.remove(__file__)

# trust me on this.
zeropadding = len(str(len(files)))
zeropadding = max(2, zeropadding)
zeropadding = str(zeropadding)

format = '%s%0{pad}d%s'.format(pad=zeropadding)

def natural_sort(l):
    '''
    http://stackoverflow.com/a/11150413
    '''
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)] 
    return sorted(l, key=alphanum_key)

if ctime:
    print('Sorting by time')
    files.sort(key=os.path.getctime)
else:
    print('Sorting by name')
    files = natural_sort(files)
for (fileindex, filename) in enumerate(files):
    if '.' in filename:
        extension = '.' + filename.split('.')[-1]
        if extension in IGNORE_EXTENSIONS:
            continue
    else:
        extension = ''
    newname = format % (prefix, fileindex, extension)
    if os.path.basename(filename) != newname:
        print(''.join([c for c in (filename + ' -> ' + newname) if c in string.printable]))
        if not dry:
            os.rename(filename, newname)
if dry:
    print('Dry. No files renamed.')