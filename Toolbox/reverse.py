import sys

from voussoirkit import clipext

arg = clipext.resolve(sys.argv[1])
arg = ''.join(reversed(arg))
print(arg)
