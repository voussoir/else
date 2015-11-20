# https://en.wikipedia.org/wiki/ICO_(file_format)

# All values in ICO/CUR files are represented in little-endian byte order.

# Header
#
# ICONDIR structure
#  _________________________________________________________________________________
# | Offset | Size (in bytes) | Purpose                                              |
# |--------|-----------------|------------------------------------------------------|
# |      0 |               2 | Reserved. Must always be 0.                          |
# |--------|-----------------|------------------------------------------------------|
# |      2 |               2 | Specifies image type: 1 for icon (.ICO) image,       |
# |        |                 | 2 for cursor (.CUR) image. Other values are invalid. |
# |--------|-----------------|------------------------------------------------------|
# |      4 |               2 | Specifies number of images in the file.              |
# |________|_________________|______________________________________________________|

# Structure of image directory
#  _______________________________________
# | Image #1 | Entry for the first image  |
# |----------|----------------------------|
# | Image #2 | Entry for the second image |
# |----------|----------------------------|
# | ...      |                            |
# |----------|----------------------------|
# | Image #n | Entry for the last image   |
# |__________|____________________________|

# Image entry
#
# ICONDIRENTRY structure
#  _________________________________________________________________________________
# | Offset | Size (in bytes) | Purpose                                              |
# |--------|-----------------|------------------------------------------------------|
# | 0 (06) |               1 | Specifies image width in pixels. Can be any number   |
# |        |                 | between 0 and 255. Value 0 means image width is 256  |
# |        |                 | pixels.                                              |
# |--------|-----------------|------------------------------------------------------|
# | 1 (07) |               1 | Specifies image height in pixels. Can be any number  |
# |        |                 | between 0 and 255. Value 0 means image height is 256 |
# |        |                 | pixels.                                              |
# |--------|-----------------|------------------------------------------------------|
# | 2 (08) |               1 | Specifies number of colors in the color palette.     |
# |        |                 | Should be 0 if the image does not use a color palette|
# |--------|-----------------|------------------------------------------------------|
# | 3 (09) |               1 | Reserved. Should be 0.                               |
# |--------|-----------------|------------------------------------------------------|
# | 4 (10) |               2 | In ICO format: Specifies color planes.               |
# |        |                 | Should be 0 or 1.                                    |
# |        |                 | In CUR format: Specifies the horizontal coordinates  |
# |        |                 | of the hotspot in number of pixels from the left.    |
# |--------|-----------------|------------------------------------------------------|
# | 6 (12) |               2 | In ICO format: Specifies bits per pixel.             |
# |        |                 | In CUR format: Specifies the vertical coordinates of |
# |        |                 | the hotspot in number of pixels from the top.        |
# |--------|-----------------|------------------------------------------------------|
# | 8 (14) |               4 | Specifies the size of the image's data in bytes      |
# |--------|-----------------|------------------------------------------------------|
# |12 (18) |               4 | Specifies the offset of BMP or PNG data from the     |
# |        |                 | beginning of the ICO/CUR file                        |
# |________|_________________|______________________________________________________|

import binascii
import sys
from PIL import Image
import os
print(os.getcwd())
try:
    INPUTFILE = sys.argv[1]
except:
    print('Please provide an image file')
    quit()

def little_endian(hexstring):
    #print(hexstring)
    assert len(hexstring) % 2 == 0
    doublets = [hexstring[x*2:(x*2)+2] for x in range(len(hexstring)//2)]
    #print(doublets)
    doublets.reverse()
    hexstring = ''.join(doublets)
    return hexstring

def fit_into_bounds(self, iw, ih, fw, fh):
    '''
    Given the w+h of the image and the w+h of the frame,
    return new w+h that fits the image into the frame
    while maintaining the aspect ratio and leaving blank space
    everywhere else
    '''
    ratio = min(fw/iw, fh/ih)

    w = int(iw * ratio)
    h = int(ih * ratio)
    return (w, h)

def image_to_ico(filename):
    print('Icofying %s' % filename)
    image = Image.open(filename)
    if min(image.size) > 256:
        w = image.size[0]
        h = image.size[1]
        image = image.resize((256, 256))
    image = image.convert('RGBA')

    print('Building ico header')
    output_bytes = ''
    output_bytes += '00' '00'  # reserved 0
    output_bytes += '01' '00'  # 1 = ico
    output_bytes += '01' '00'  # number of images
    #### ICO HEADER ####

    print('Building image entry')
    # width and height. 00 acts as 256
    output_bytes += '%02x' % image.size[0] if image.size[0] < 256 else '00'
    output_bytes += '%02x' % image.size[1] if image.size[1] < 256 else '00'
    output_bytes += '00'    # colors in palette
    output_bytes += '00'    # reserved 0
    output_bytes += '01' '00'  # color planes
    output_bytes += '20' '00'  # bits per pixel (32)
    output_bytes += little_endian('%08x' % ((image.size[0] * image.size[1] * 4)+8192))  # image bytes size
    output_bytes += '16' '00' '00' '00'  # image offset from start of file (begins right after this)
    #### IMAGE ENTRY ####

    print('Building image header')
    output_bytes += '28' '00' '00' '00'  # BMP DIB header size (always 40)
    output_bytes += little_endian('%08x' % image.size[0])
    output_bytes += little_endian('%08x' % (image.size[1] * 2))  # I'm not sure why * 2
    output_bytes += '01' '00'  # color planes
    output_bytes += '20' '00'  # bits per pixel (32)
    output_bytes += '00' '00' '00' '00'  # Compression (None)
    image_bytesize = image.size[0] * image.size[1] * 4
    # BMP pixel array must always end on a 4th byte.
    image_nullpadding = 4 - (image_bytesize % 4)
    image_nullpadding = 0 if image_nullpadding == 4 else image_nullpadding
    output_bytes += little_endian('%08x' % (image_bytesize + image_nullpadding))  # BMP file size
    output_bytes += '00' '00' '00' '00'  # Print width (unnecessary)
    output_bytes += '00' '00' '00' '00'  # Print height (unecessary)
    output_bytes += '00' '00' '00' '00'  # colors in palette
    output_bytes += '00' '00' '00' '00'  # "important colors" 
    #### IMAGE HEADER ####

    print('Writing pixels')
    image_data = ''
    for y in range(image.size[1]-1, -1, -1):
        for x in range(image.size[0]):
            pixel = image.getpixel( (x, y) )
            #print(pixel)
            r = '%02x' % pixel[0]
            g = '%02x' % pixel[1]
            b = '%02x' % pixel[2]
            o = '%02x' % pixel[3]
            image_data += b + g + r + o

    image_data += '00' * 8192
    output_bytes += image_data
    output_bytes = binascii.a2b_hex(output_bytes)
    name = filename.split('.')[0] + '.ico'
    output_file = open(name, 'wb')
    output_file.write(output_bytes)
    output_file.close()
    print('Finished %s.' % name)


image_to_ico(INPUTFILE)