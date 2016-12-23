'''
Search for a target string within the lines of files.

For example:
fileswith.py *.py "import random"
'''

import fnmatch
import glob
import re
import sys

from voussoirkit import safeprint
from voussoirkit import spinal

filepattern = sys.argv[1]
searchpattern = sys.argv[2]

for filename in spinal.walk_generator():
    filename = filename.absolute_path
    if not fnmatch.fnmatch(filename, filepattern):
        continue
    matches = []
    handle = open(filename, 'r', encoding='utf-8')
    try:
        with handle:
            for (index, line) in enumerate(handle):
                if re.search(searchpattern, line, flags=re.IGNORECASE):
                    line = '%d | %s' % (index, line.strip())
                    matches.append(line)
    except:
        pass
    if matches:
        print(filename)
        safeprint.safeprint('\n'.join(matches))
        print()
