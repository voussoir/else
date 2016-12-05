'''
Keep the unique lines coming from stdin and print them.
'''
from voussoirkit import clipext
import sys

if len(sys.argv) > 1:
    text = clipext.resolve(sys.argv[1])
else:
    text = clipext.resolve('!input')

text = text.split('\n')

new_text = []
seen = set()
for item in text:
    if item not in seen:
        new_text.append(item)
        seen.add(item)

new_text = '\n'.join(new_text)
print(new_text)
