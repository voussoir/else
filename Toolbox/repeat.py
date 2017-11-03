'''
Repeat the input as many times as you want

> repeat "hello" 8
> echo hi | repeat !i 4
'''

import sys

from voussoirkit import clipext

text = clipext.resolve(sys.argv[1])
repeat_times = int(sys.argv[2])

for t in range(repeat_times):
    print(text)
