'''
Recompress all jpg images in the current directory.
Add /r to do nested directories as well.
'''

from voussoirkit import bytestring
import io
import os
import PIL.Image
import PIL.ImageFile
import string
import sys

PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True

if '/r' in sys.argv:
    from voussoirkit import spinal
    walker = spinal.walk_generator()
    files = list(walker)
    files = [f.absolute_path for f in files]

else:
    files = os.listdir()
    files = [f for f in files if os.path.isfile(f)]

files = [f for f in files if any(ext in f.lower() for ext in ['.jpg', '.jpeg'])]

bytes_saved = 0
remaining_size = 0
for filename in files:
    print(''.join(c for c in filename if c in string.printable))
    bytesio = io.BytesIO()
    i = PIL.Image.open(filename)
    i.save(bytesio, format='jpeg', quality=80)

    bytesio.seek(0)
    new_bytes = bytesio.read()
    old_size = os.path.getsize(filename)
    new_size = len(new_bytes)
    remaining_size += new_size
    if new_size < old_size:
        bytes_saved += (old_size - new_size)
        f = open(filename, 'wb')
        f.write(new_bytes)
        f.close()

print('Saved', bytestring.bytestring(bytes_saved))
print('Remaining are', bytestring.bytestring(remaining_size))