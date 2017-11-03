# https://en.wikipedia.org/wiki/ICO_(file_format)

# All values in ICO/CUR files are represented in little-endian byte order.

# Broad file structure:
#  _______________________
# | ICO header            |
# |-----------------------|
# | Icon directories 1..n |
# |-----------------------|
# | Image data 1..n       |
# |_______________________|

# ICO header:
#  _______________________________________________________________________________
# | Offset | Size (bytes) | Purpose                                               |
# |--------|--------------|-------------------------------------------------------|
# |      0 |            2 | Reserved. Must always be 0.                           |
# |--------|--------------|-------------------------------------------------------|
# |      2 |            2 | Specifies image type: 1 for icon (.ICO) image,        |
# |        |              | 2 for cursor (.CUR) image. Other values are invalid.  |
# |--------|--------------|-------------------------------------------------------|
# |      4 |            2 | Specifies number of images in the file.               |
# |________|______________|_______________________________________________________|

# Icon directory structure:
#  _______________________________________________________________________________
# | Offset | Size (bytes) | Purpose                                               |
# |--------|--------------|-------------------------------------------------------|
# |  0     |            1 | Specifies image width in pixels. Can be any number    |
# |        |              | between 0 and 255. Value 0 means image width is 256   |
# |        |              | pixels.                                               |
# |--------|--------------|-------------------------------------------------------|
# |  1     |            1 | Specifies image height in pixels. Can be any number   |
# |        |              | between 0 and 255. Value 0 means image height is 256  |
# |        |              | pixels.                                               |
# |--------|--------------|-------------------------------------------------------|
# |  2     |            1 | Specifies number of colors in the color palette.      |
# |        |              | Should be 0 if the image does not use a color palette |
# |--------|--------------|-------------------------------------------------------|
# |  3     |            1 | Reserved. Should be 0.                                |
# |--------|--------------|-------------------------------------------------------|
# |  4     |            2 | In ICO format: Specifies color planes.                |
# |        |              | Should be 0 or 1.                                     |
# |        |              | In CUR format: Specifies the horizontal coordinates   |
# |        |              | of the hotspot in number of pixels from the left.     |
# |--------|--------------|-------------------------------------------------------|
# |  6     |            2 | In ICO format: Specifies bits per pixel.              |
# |        |              | In CUR format: Specifies the vertical coordinates of  |
# |        |              | the hotspot in number of pixels from the top.         |
# |--------|--------------|-------------------------------------------------------|
# |  8     |            4 | Specifies the size of the image's data in bytes       |
# |--------|--------------|-------------------------------------------------------|
# | 12     |            4 | Specifies the offset of BMP or PNG data from the      |
# |        |              | beginning of the ICO/CUR file                         |
# |________|______________|_______________________________________________________|

# Image data structure
# BMP, starting from the BITMAPINFOHEADER, ignoring normal file header:
#  _______________________________________________________________________________
# | Offset | Size (bytes) | Purpose                                               |
# |--------|--------------|-------------------------------------------------------|
# |  0     |            4 | The size of this header. Always 40.                   |
# |--------|--------------|-------------------------------------------------------|
# |  4     |            4 | Image width in pixels, signed.                        |
# |--------|--------------|-------------------------------------------------------|
# |  8     |            4 | Image height in pixels, signed.                       |
# |--------|--------------|-------------------------------------------------------|
# | 12     |            2 | Number of color planes. Always 1.                     |
# |--------|--------------|-------------------------------------------------------|
# | 14     |            2 | Bits per pixel aka color depth.                       |
# |--------|--------------|-------------------------------------------------------|
# | 16     |            4 | Compression method. 0 for None aka BI_RGB.            |
# |--------|--------------|-------------------------------------------------------|
# | 20     |            4 | Image bytes length. 0 for BI_RGB because inferred.    |
# |--------|--------------|-------------------------------------------------------|
# | 24     |            4 | Horizontal print resolution.                          |
# |--------|--------------|-------------------------------------------------------|
# | 28     |            4 | Vertical print resolution                             |
# |--------|--------------|-------------------------------------------------------|
# | 32     |            4 | Number of colors in palette. 0 for 2^n.               |
# |--------|--------------|-------------------------------------------------------|
# | 36     |            4 | Number of important colors. 0 for all.                |
# |--------|--------------|-------------------------------------------------------|
# | 40     |            n | Pixel bytes, r, g, b, a.                              |
# |________|______________|_______________________________________________________|

import os
import sys
from PIL import Image


ICO_HEADER_LENGTH = 6
ICON_DIRECTORY_ENTRY_LENGTH = 16
BMP_HEADER_LENGTH = 40


def chunk_sequence(sequence, chunk_length, allow_incomplete=True):
    '''
    Given a sequence, divide it into sequences of length `chunk_length`.

    allow_incomplete:
        If True, allow the final chunk to be shorter if the
        given sequence is not an exact multiple of `chunk_length`.
        If False, the incomplete chunk will be discarded.
    '''
    (complete, leftover) = divmod(len(sequence), chunk_length)
    if not allow_incomplete:
        leftover = 0

    chunk_count = complete + min(leftover, 1)

    chunks = []
    for x in range(chunk_count):
        left = chunk_length * x
        right = left + chunk_length
        chunks.append(sequence[left:right])

    return chunks

def fit_into_bounds(iw, ih, fw, fh):
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

def little(x, length):
    return x.to_bytes(length, byteorder='little')

def load_image(filename):
    image = Image.open(filename)
    if min(image.size) > 256:
        (w, h) = image.size
        image = image.resize(fit_into_bounds(w, h, 256, 256), resample=Image.ANTIALIAS)
    image = image.convert('RGBA')
    return image

def build_ico_header_blob(image_count):
    datablob = (b''
        + little(0, 2)  # reserved
        + little(1, 2)  # 1 = ico type
        + little(image_count, 2)
    )
    return datablob

def build_icon_directory_blob(image, offset_from_start):
    (width, height) = image.size
    datablob = (b''
        + little(width if width < 256 else 0, 1)
        + little(height if height < 256 else 0, 1)
        + little(0, 1)  # colors in palette
        + little(0, 1)  # reserved
        + little(1, 2)  # color planes
        + little(32, 2)  # bit depth
        + little((width * height * 4) + BMP_HEADER_LENGTH, 4)  # image bytes length
        + little(offset_from_start, 4)
    )
    return datablob

def build_image_data_blob(image):
    datablob = (b''
        + little(40, 4)  # header size
        + little(image.size[0], 4)
        # "Even if the AND mask is not supplied, if the image is in Windows BMP
        # format, the BMP header must still specify a doubled height." - wikipedia
        + little(image.size[1] * 2, 4)
        + little(1, 2)  # color planes
        + little(32, 2)  # bit depth
        + little(0, 4)  # no compression
        + little(0, 4)  # bytes length, inferred
        + little(0, 4)  # hor print
        + little(0, 4)  # ver print
        + little(0, 4)  # palette
        + little(0, 4)  # important palette
    )
    pixeldata = []
    # Image.getdata() is a list of (r, g, b, a) channels
    # But the BMP are written (b, g, r, a)
    # Also they are written from bottom to top.
    pixels = list(image.getdata())
    pixels = reversed(chunk_sequence(pixels, image.size[0]))
    pixels = [line for chunk in pixels for line in chunk]
    for pixel in pixels:
        (r, g, b, a) = pixel
        pixeldata.extend((b, g, r, a))
    datablob += bytes(pixeldata)
    return datablob

def images_to_ico(images):
    # For some reason Windows reads the icons in reverse order.
    images.reverse()

    # The directory entries need to know their image's address, so therefore
    # we must know the lengths of all the image binaries before we can write
    # any directory entries.
    # We will calculate the image blobs first, store them separately,
    # and then put them after the directory blobs.
    datablobs = []
    imageblobs = []

    ico_header_blob = build_ico_header_blob(image_count=len(images))
    datablobs.append(ico_header_blob)

    for (index, image) in enumerate(images):
        imageblob = build_image_data_blob(image)
        imageblobs.append(imageblob)

    # Since the ICO header and directory entries are of fixed length, we know
    # the location of the first image.
    # After that, the offset just gains the size of the previous image.
    offset_from_start = ICO_HEADER_LENGTH + (len(images) * ICON_DIRECTORY_ENTRY_LENGTH)
    for (index, (image, imageblob)) in enumerate(zip(images, imageblobs)):
        directoryblob = build_icon_directory_blob(image, offset_from_start=offset_from_start)
        datablobs.append(directoryblob)
        offset_from_start += len(imageblob)

    datablobs.extend(imageblobs)

    final_data = b''.join(datablobs)
    return final_data


if __name__ == '__main__':
    try:
        inputfiles = sys.argv[1:]
    except:
        print('Please provide an image file')
        raise SystemExit
    print('Iconifying', inputfiles)
    images = [load_image(filename) for filename in inputfiles]
    final_data = images_to_ico(images)
    name = os.path.splitext(inputfiles[0])[0] + '.ico'
    output_file = open(name, 'wb')
    output_file.write(final_data)
    output_file.close()
    print('Finished %s.' % name)
