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

x = clipext.resolve(sys.argv[1])
transformation = ' '.join(sys.argv[2:])

result = eval(transformation)
print(result)
