'''
Drag a file on top of this .py file, and it will
be renamed to the current timestamp.
'''

import datetime
import os
import sys

STRFTIME = '%Y%m%d %H%M%S'
UTC = True

filename = sys.argv[1]
folder = os.path.dirname(filename)
if folder == '':
    folder = os.getcwd()
basename = os.path.basename(filename)
extension = os.path.splitext(basename)[1]

now = datetime.datetime.now(datetime.timezone.utc if UTC else None)
newname = now.strftime(STRFTIME)

newname = '%s\\%s%s' % (folder, newname, extension)
print(filename, '-->', newname)
os.rename(filename, newname)