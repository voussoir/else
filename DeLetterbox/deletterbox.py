from PIL import Image
import os
import sys

close_enough_threshold = 10
filename = sys.argv[1]
try:
    close_enough_threshold = int(sys.argv[2])
except:
    pass

def close_enough(a, b):
    #print(a, b)
    for (a_channel, b_channel) in zip(a, b):
        if abs(a_channel - b_channel) > close_enough_threshold:
            return False
    return True

def deletterbox(filename):
    image = Image.open(filename)
    (base, ext) = os.path.splitext(filename)
    for x in range(4):
        image = trim_top(image)
        print('size', image.size)
        #image.save('%s_%d%s' % (base, x, ext))

        rotated = image.rotate(90, expand=True)
        # There is currently a bug in PIL which causes rotated images
        # to have a 1 px black border on the top and left
        if rotated.size != image.size:
            rotated = rotated.crop([1, 1, rotated.size[0], rotated.size[1]])

        image = rotated
        print()
    filename = base + '_crop' + ext
    image.save(filename, quality=100)

def trim_top(image):
    letterbox_color = image.getpixel((0, 0))
    print('letterbox color', letterbox_color)
    for y in range(image.size[1]):
        solid = True
        for x in range(image.size[0]):
            pixel = image.getpixel((x, y))
            #print(pixel)
            if not close_enough(letterbox_color, pixel):
                solid = False
                print('broke at', y,pixel)
                break
        if not solid:
            break
    bounds = (0, y, image.size[0], image.size[1])
    print('bounds', bounds)
    image = image.crop(bounds)
    return image



deletterbox(filename)

