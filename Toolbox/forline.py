import os
import sys

from voussoirkit import clipext

text = sys.argv[1]
command = sys.argv[2:]
command = ['"%s"' % x if (' ' in x or x == '%x') else x for x in command]
command = ' '.join(command)
text = clipext.resolve(text)

for line in text.splitlines():
    thiscomm = command.replace('%x', line)
    os.system(thiscomm)
