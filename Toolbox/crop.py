import os
import sys
from PIL import Image

filename = sys.argv[1]
(name, extension) = os.path.splitext(filename)
newname = '%s_cropped%s' % (name, extension)

crops = sys.argv[2:]
crops = ' '.join(crops)
crops = crops.replace(',', ' ')
crops = crops.replace('  ', ' ')
crops = crops.split(' ')
crops = [int(x) for x in crops]
crops = list(crops)
print(crops)
i = Image.open(filename)
if len(crops) == 2:
    crops.extend(i.size)
i = i.crop(crops)
i.save(newname, quality=100)
