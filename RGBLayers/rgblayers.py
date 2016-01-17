import os
import sys
import PIL.Image

def listget(li, index, fallback=None):
    try:
        return li[index]
    except IndexError:
        return fallback

def onechannel(tu, index):
    ret = [0, 0, 0, 255]
    ret[index] = listget(tu, index, 0)
    ret[3] = listget(tu, 3, 255)
    return tuple(ret)

def splitchannels(filename):
    image = PIL.Image.open(filename)
    (base, extension) = os.path.splitext(filename)
    image_r = PIL.Image.new(image.mode, image.size)
    image_g = PIL.Image.new(image.mode, image.size)
    image_b = PIL.Image.new(image.mode, image.size)
    width = image.size[0]
    height = image.size[1]
    pixels = list(image.getdata())
    print('Extracting R')
    image_r.putdata([onechannel(x, 0) for x in pixels])
    print('Extracting G')
    image_g.putdata([onechannel(x, 1) for x in pixels])
    print('Extracting B')
    image_b.putdata([onechannel(x, 2) for x in pixels])
    #for (index, pixel) in enumerate(iter(image.getdata())):
    #    x = index % width
    #    y = index // height
    #    co = (x, y)
    #    pixel = image.getpixel(co)
    #    r = listget(pixel, 0, 0)
    #    g = listget(pixel, 1, 0)
    #    b = listget(pixel, 2, 0)
    #    o = listget(pixel, 3, 255)
    #    image_r.putpixel(co, (r, 0, 0, o))
    #    image_g.putpixel(co, (0, g, 0, o))
    #    image_b.putpixel(co, (0, 0, b, 0))
    #    if x == 0:
    #        print(y)
    image_r.save('%s_R%s' % (base, extension), quality=100)
    image_g.save('%s_G%s' % (base, extension), quality=100)
    image_b.save('%s_B%s' % (base, extension), quality=100)

filename = sys.argv[1]
splitchannels(filename)
i = PIL.Image.open(filename)