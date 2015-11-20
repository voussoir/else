from PIL import Image
import sys

imagename = sys.argv[1]
image = Image.open(imagename)
image = image.convert('RGBA')
w = image.size[0] - 1
h = image.size[1] - 1
for i in range(5):
    image.putpixel( (0, i), (0, 0, 0, 0))
    image.putpixel( (0, h-i), (0, 0, 0, 0))
    image.putpixel( (w, i), (0, 0, 0, 0))
    image.putpixel( (w, h-i), (0, 0, 0, 0))
for i in range(3):
    image.putpixel( (1, i), (0, 0, 0, 0))
    image.putpixel( (1, h-i), (0, 0, 0, 0))
    image.putpixel( (w-1, i), (0, 0, 0, 0))
    image.putpixel( (w-1, h-i), (0, 0, 0, 0))
for i in range(2):
    image.putpixel( (2, i), (0, 0, 0, 0))
    image.putpixel( (2, h-i), (0, 0, 0, 0))
    image.putpixel( (w-2, i), (0, 0, 0, 0))
    image.putpixel( (w-2, h-i), (0, 0, 0, 0))

image.putpixel( (3, 0), (0, 0, 0, 0))
image.putpixel( (3, h), (0, 0, 0, 0))
image.putpixel( (w-3, 0), (0, 0, 0, 0))
image.putpixel( (w-3, h), (0, 0, 0, 0))
image.putpixel( (4, 0), (0, 0, 0, 0))
image.putpixel( (4, h), (0, 0, 0, 0))
image.putpixel( (w-4, 0), (0, 0, 0, 0))
image.putpixel( (w-4, h), (0, 0, 0, 0))
image.save(imagename)