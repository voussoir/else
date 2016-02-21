from PIL import Image
import os
import sys

close_enough_threshold = 90
filename = sys.argv[1]
try:
    close_enough_threshold = int(sys.argv[2])
except:
    pass

def close_enough(a, b):
    for (a_channel, b_channel) in zip(a, b):
        if abs(a_channel - b_channel) > close_enough_threshold:
            return False
    return True

def deletterbox(filename):
    image = Image.open(filename)
    trim_top(image)
    for x in range(4):
        image = trim_top(image)
        image = image.rotate(90)
    #(base, ext) = os.path.splitext(filename)
    #filename = base + 'X' + ext
    image.save(filename, quality=100)

def trim_top(image):
    letterbox_color = image.getpixel((0, 0))
    for y in range(image.size[1]):
        solid = True
        for x in range(image.size[0]):
            pixel = image.getpixel((x, y))
            #print(pixel)
            if not close_enough(letterbox_color, pixel):
                solid = False
                #print(y,pixel)
                break
        if not solid:
            break
    bounds = (0, y, image.size[0], image.size[1])
    print(bounds)
    image = image.crop(bounds)
    return image



deletterbox(filename)

