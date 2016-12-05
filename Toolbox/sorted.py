'''
Sort the lines coming from stdin and print them.
'''
from voussoirkit import clipext
import sys

if len(sys.argv) > 1:
    text = clipext.resolve(sys.argv[1])
else:
    text = clipext.resolve('!input')

text = text.split('\n')
if '-l' in sys.argv:
    text.sort(key=lambda x: x.lower())
else:
    text.sort()

new_text = '\n'.join(text)
print(new_text)
