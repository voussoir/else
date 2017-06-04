'''
Great for applying Python post-processing to the output of some other command.
Provide an input string (!i for stdin) and an eval string using `x` as the
variable name of the input.
'''
from voussoirkit import clipext
import math
import os
import random
import string
import sys
import time

if '--lines' in sys.argv:
    by_lines = True
    sys.argv.remove('--lines')
else:
    by_lines = False
text = clipext.resolve(sys.argv[1], split_lines=by_lines)
transformation = ' '.join(sys.argv[2:])

if by_lines:
    for line in text:
        x = line
        result = eval(transformation)
        print(result)
else:
    x = text
    result = eval(transformation)
    print(result)
