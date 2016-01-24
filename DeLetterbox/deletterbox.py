from PIL import Image
import os
import sys

CLOSE_ENOUGH_THRESHOLD = 10

def close_enough(a, b):
    for (a_channel, b_channel) in zip(a, b):
        if abs(a_channel - b_channel) > CLOSE_ENOUGH_THRESHOLD:
            return False
    return True

def deletterbox(filename):
    image = Image.open(filename)
    trim_top(image)
    for x in range(4):
        image = trim_top(image)
        image = image.rotate(90)
    (base, ext) = os.path.splitext(filename)
    #filename = base + 'X' + ext
    image.save(filename)

def trim_top(image):
    letterbox_color = image.getpixel((0, 0))
    for y in range(image.size[1]):
        solid = True
        for x in range(image.size[0]):
            pixel = image.getpixel((x, y))
            if not close_enough(letterbox_color, pixel):
                solid = False
                break
        if not solid:
            break
    bounds = (0, y, image.size[0], image.size[1])
    #print(bounds)
    image = image.crop(bounds)
    return image

filenames = sys.argv[1:]
for filename in filenames:
    deletterbox(filename)

