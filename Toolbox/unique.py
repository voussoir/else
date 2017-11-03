'''
Keep the unique lines coming from stdin and print them.
'''
from voussoirkit import clipext
import sys

if len(sys.argv) > 1:
    source = sys.argv[1]
else:
    source = '!input'
lines = clipext.resolve(source, split_lines=True)

new_text = []
seen = set()
for line in lines:
    if line not in seen:
        #new_text.append(line)
        seen.add(line)
        print(line)

