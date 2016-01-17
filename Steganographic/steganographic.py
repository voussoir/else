'''
For each color channel of each pixel in an Image, modify the least significant bit to represent a bit of the Secret file.
This changes the RGB value of the pixel by a usually-imperceptible amount.
The first 32 bits (10.66 pixels) will be used to store the length of the Secret content in big endian.
Then, the Secret's extension is stored. A null byte indicates the end of the extension. This section is of variable length.
A file with no extension requires only that null byte. A file with an extension requires 1 additional byte per character.

Smallest image possible = 16 pixels with 48 bit secret: 32 for header; 8 for null extension; 8 for data.
Each Image pixel holds 3 Secret bits, so the Image must have at least ((secretbytes * (8 / 3)) + 14) pixels.
An Image can hold ((3 * (pixels - 14)) / 8) Secret bytes.

Usage:
> steganographic.py encode imagefilename.png secretfilename.ext
> steganographic.py decode lacedimagename.png


Reference table for files with NO EXTENSION.
For each extension character, subtract 1 byte from secret size

     pixels |       example dimensions | Secret file size
        100 |                  10 x 10 |         32 bytes
        400 |                  20 x 20 |        144 bytes
      2,500 |                  50 x 50 |        932 bytes
     10,000 |                100 x 100 |      3,744 bytes
     40,000 |                200 x 200 |     14,994 bytes
     25,000 |                500 x 500 |     93,744 bytes (91 kb)
  1,000,000 |            1,000 x 1,000 |    374,994 bytes (366 kb)
  4,000,000 |            2,000 x 2,000 |  1,499,994 bytes (1.43 mb)
 25,000,000 |            5,000 x 5,000 |  9,374,994 bytes (8.94 mb)
100,000,000 |          10,000 x 10,000 | 37,499,994 bytes (35.7 mb)

     pixels |       example dimensions | Secret file size
        100 |                  10 x 10 |         32 bytes
        697 |            25 x 28 (700) |        256 bytes
      2,745 |          50 x 55 (2,750) |      1,024 bytes (1 kb)
     21,860 |       142 x 154 (21,868) |      8,192 bytes (8 kb)
     87,396 |       230 x 380 (87,400) |     32,768 bytes (32 kb)
    349,540 |      463 x 755 (349,565) |    131,072 bytes (128 kb)
  1,398,116 |  1146 x 1120 (1,398,120) |    524,288 bytes (512 kb)
  2,796,217 |  1621 x 1725 (2,796,225) |  1,048,576 bytes (1 mb)
 11,184,825 | 3500 x 3200 (11,200,000) |  4,194,304 bytes (4 mb)
 44,739,257 | 6700 x 6700 (44,890,000) | 16,777,216 bytes (16 mb)
 89,478,500 | 9500 x 9500 (90,250,000) | 33,554,432 bytes (32 mb)

'''
from PIL import Image
import binascii
import math
import os
import sys

# 11 pixels for the secret file size
HEADER_SIZE = 11

FILE_READ_SIZE = 4 * 1024

class StegError(Exception):
    pass

class BitsToImage:
    def __init__(self, image, bitness):
        self.image = image
        self.bitness = bitness
        self.width = image.size[0]
        self.pixel_index = -1
        self.channel_index = 0
        self.bit_index = self.bitness - 1
        self.active_pixel = None
        self.x = 0
        self.y = 0

    def _write(self, bit):
        if self.active_pixel is None:
            self.pixel_index += 1
            self.channel_index = 0
            self.bit_index = self.bitness - 1
            (self.x, self.y) = index_to_xy(self.pixel_index, self.width)
            self.active_pixel = list(self.image.getpixel((self.x, self.y)))

        channel = self.active_pixel[self.channel_index]
        channel = set_bit(channel, self.bit_index, int(bit))
        self.active_pixel[self.channel_index] = channel
        self.bit_index -= 1

        if self.bit_index < 0:
            # We have exhausted our bitness for this channel.
            self.bit_index = self.bitness - 1
            self.channel_index += 1
        if self.channel_index == 3:
            # We have exhausted the channels for this pixel.
            self.image.putpixel((self.x, self.y), tuple(self.active_pixel))
            self.active_pixel = None

    def write(self, bits):
        for bit in bits:
            self._write(bit)


class ImageToBits:
    def __init__(self, image, bitness):
        self.image = image
        self.width = image.size[0]
        self.pixel_index = -1
        self.active_byte = []

    def _read(self):
        if len(self.active_byte) == 0:
            self.pixel_index += 1
            (x, y) = index_to_xy(self.pixel_index, self.width)
            self.active_byte = list(self.image.getpixel((x, y)))
            self.active_byte = self.active_byte[:3]
            self.active_byte = [binary(channel) for channel in self.active_byte]
            self.active_byte = [channel[-bitness:] for channel in self.active_byte]
            self.active_byte = ''.join(self.active_byte)
            self.active_byte = list(self.active_byte)

        ret = self.active_byte.pop(0)
        return ret

    def read(self, bits=1):
        return ''.join(self._read() for x in range(bits)) 


def binary(i):
    return bin(i)[2:].rjust(8, '0')

def chunk_iterable(iterable, chunk_length, allow_incomplete=True):
    '''
    Given an iterable, divide it into chunks of length `chunk_length`.
    If `allow_incomplete` is True, the final element of the returned list may be shorter
    than `chunk_length`. If it is False, those items are discarded.
    '''
    if len(iterable) % chunk_length != 0 and allow_incomplete:
        overflow = 1
    else:
        overflow = 0

    steps = (len(iterable) // chunk_length) + overflow
    return [iterable[chunk_length * x : (chunk_length * x) + chunk_length] for x in range(steps)]

def index_to_xy(index, width):
    x = index % width
    y = index // width
    return (x, y)

def bytes_to_pixels(bytes):
    return ((bytes * (8 / 3)) + 14)

def pixels_to_bytes(pixels):
    return ((3 * (pixels - 14)) / 8)

def set_bit(number, index, newvalue):
    # Thanks unwind
    # http://stackoverflow.com/a/12174051/5430534
    mask = 1 << index
    number &= ~mask
    if newvalue:
        number |= mask
    return number    

##############    ####      ####        ########          ######        ##########        ##############
  ####      ##    ####      ####      ####    ####      ####  ####        ####  ####        ####      ##
  ####            ######    ####    ####      ####    ####      ####      ####    ####      ####        
  ####    ##      ########  ####    ####              ####      ####      ####    ####      ####    ##  
  ##########      ##############    ####              ####      ####      ####    ####      ##########  
  ####    ##      ####  ########    ####              ####      ####      ####    ####      ####    ##  
  ####            ####    ######    ####      ####    ####      ####      ####    ####      ####        
  ####      ##    ####      ####      ####    ####      ####  ####        ####  ####        ####      ##
##############    ####      ####        ########          ######        ##########        ##############
def encode(imagefilename, secretfilename, bitness=1):
    global image
    global pixel
    global pixel_index
    global channel_index
    pixel_index = 0
    channel_index = 0

    if bitness < 1:
        raise ValueError('Cannot modify less than 1 bit per channel')
    if bitness > 8:
        raise ValueError('Cannot modify more than 8 bits per channel')

    print('Hiding "%s" within "%s"' % (secretfilename, imagefilename))
    secret_size = os.path.getsize(secretfilename)
    if secret_size == 0:
        raise StegError('The Secret can\'t be 0 bytes.')

    image = Image.open(imagefilename)
    image_steg = BitsToImage(image, bitness)

    totalpixels = image.size[0] * image.size[1]
    if totalpixels < HEADER_SIZE:
        raise StegError('Image cannot have fewer than %d pixels. They are used to store Secret\'s length' % HEADER_SIZE)

    secret_extension = os.path.splitext(secretfilename)[1][1:]
    secret_content_length = (secret_size) + (len(secret_extension)) + 1
    requiredpixels = math.ceil(((secret_content_length * 8) + 32) / (3 * bitness))
    if totalpixels < requiredpixels:
        raise StegError('Image does not have enough pixels to store the Secret'
                        'Must have at least %d pixels' % requiredpixels)

    print('%d pixels available, %d required' % (totalpixels, requiredpixels))

    # --> YOU ARE HERE <--

    # Because bitness may be between 1 and 8, we need to create a writing buffer
    # called `binary_write_buffer`, so that we're always writing the same amount
    # of data per color channel.
    # If we were to write the secret length / extension on the fly, we might end
    # up using the wrong number of bits for the final channel of some pixel.
    # Example: 10010101 broken into groups of 3 is [100, 101, 01]
    # Note that the last group is not the same size as the desired bitness, and
    # will cause decode errors.

    pixel = list(image.getpixel((0, 0)))
    binary_write_buffer = ''

    # Write secret length
    secret_content_length_b = binary(secret_content_length).rjust(32, '0')
    print('Content bytes:', secret_content_length)
    image_steg.write(secret_content_length_b)

    # Write the secret extension
    for character in (secret_extension + chr(0)):
        image_steg.write(binary(ord(character)))

    # Write the secret data
    bytes_written = 0
    done = False
    secretfile = open(secretfilename, 'rb')
    while not done:
        if bytes_written % 1024 == 0:
            percentage = (bytes_written + 1) / secret_size
            percentage = '%07.3f%%\r' % (100 * percentage)
            print(percentage, end='')

        bytes = secretfile.read(FILE_READ_SIZE)

        done = len(bytes) == 0

        bytes = list(bytes)
        bytes = [binary(byte) for byte in bytes]
        bytes_written += len(bytes)
        bytes = ''.join(bytes)
        image_steg.write(bytes)

    # haha
    print('100.000%')

    if channel_index != 0:
        # The Secret data has finished, but we still have an unsaved pixel
        # (because channel_index is set to 0 when we save the active pixel above)
        (x, y) = index_to_xy(pixel_index, image.size[0])
        image.putpixel((x, y), tuple(pixel))

    new_name = os.path.splitext(imagefilename)[0]
    original_name = os.path.basename(secretfilename).replace('.', '_')
    newname = '%s (%s) (%d).png' % (new_name, original_name, bitness)
    print('Writing:', newname)
    image.save(newname)



##########        ##############        ########          ######        ##########        ##############
  ####  ####        ####      ##      ####    ####      ####  ####        ####  ####        ####      ##
  ####    ####      ####            ####      ####    ####      ####      ####    ####      ####        
  ####    ####      ####    ##      ####              ####      ####      ####    ####      ####    ##  
  ####    ####      ##########      ####              ####      ####      ####    ####      ##########  
  ####    ####      ####    ##      ####              ####      ####      ####    ####      ####    ##  
  ####    ####      ####            ####      ####    ####      ####      ####    ####      ####        
  ####  ####        ####      ##      ####    ####      ####  ####        ####  ####        ####      ##
##########        ##############        ########          ######        ##########        ##############
def decode(imagefilename, bitness=1):

    print('Extracting content from "%s"' % imagefilename)
    image = Image.open(imagefilename)
    image_steg = ImageToBits(image, bitness)

    # determine the content length
    content_length = image_steg.read(32)
    content_length = int(content_length, 2)
    print('Content bytes:', content_length)

    # determine secret extension
    extension = ''
    while extension[-8:] != '00000000' or len(extension) % 8 != 0:
        extension += image_steg.read()

    extension = chunk_iterable(extension, 8)
    extension.remove('00000000')
    extension = [chr(int(x, 2)) for x in extension]
    extension = ''.join(extension)
    print('Extension:', extension)

    # Remove the extension length, and null byte
    content_length -= 1
    content_length -= len(extension)

    # Prepare writes
    newname = os.path.splitext(imagefilename)[0]
    if extension != '':
        extension = '.' + extension
    newname = '%s (extracted)%s' % (newname, extension)
    outfile = open(newname, 'wb')

    # extract data
    bytes_written = 0
    while bytes_written < content_length:
        if bytes_written % 1024 == 0:
            percentage = (bytes_written + 1) / content_length
            percentage = '%07.3f%%\r' % (100 * percentage)
            print(percentage, end='')

        byte = image_steg.read(8)
        byte = '%02x' % int(byte, 2)
        outfile.write(binascii.a2b_hex(byte))
        bytes_written += 1

    # I'm on fire
    print('100.000%')
    print('Wrote', newname)
    outfile.close()

def listget(li, index, fallback=None):
    try:
        return li[index]
    except IndexError:
        return fallback

if __name__ == '__main__':
    command = listget(sys.argv, 1, '').lower()
    if command not in ['encode', 'decode']:
        print('Usage:')
        print('> steganographic.py encode imagefilename.png secretfilename.ext')
        print('> steganographic.py decode lacedimagename.png')
        quit()

    imagefilename = sys.argv[2]

    if command == 'encode':
        secretfilename = sys.argv[3]
        bitness = int(listget(sys.argv, 4, 1))
        encode(imagefilename, secretfilename, bitness)
    else:
        bitness = int(listget(sys.argv, 3, 1))
        decode(imagefilename, bitness)