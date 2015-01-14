import random
from PIL import Image
import time

path = "C:/users/owner/desktop/"
name = "image.png"

image = Image.open(path + name)
width = image.size[0]
height = image.size[1]

def determinevalue(pixel):
    r = pixel[0]
    g = pixel[1]
    b = pixel[2]
    try:
        o = pixel[3]
    except:
        o = 0

    r = r ** 3
    g = g ** 2


    total = r+g+b+o
    return total

pixels = []
print('Stealing pixels')
for y in range(height):
    for x in range(width):
        pix = image.getpixel((x, y))
        pixels.append(pix)

print('Sorting pixels')
pixels.sort(key=determinevalue, reverse=True)

print('Creating new image')
newimage = image.copy()
newpixels = newimage.load()

print('Applying new pixels')
pos = 0
for y in range(height):
    for x in range(width):
        newpixels[x, y] = pixels[pos]
        pos += 1
        #pixels = pixels[1:]
    print("%d / %d" % (y, height))

print('Saving new file')
newimage.save(path + name.replace('.', '_sorted.'), quality=100)