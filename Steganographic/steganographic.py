'''
For each color channel of each pixel in an Image, modify the least significant bit to represent a bit of the Secret file.
This changes the RGB value of the pixel by a usually-imperceptible amount.
The first 32 bits (10.66 pixels) will be used to store the length of the Secret content in big endian.
Then, the Secret's extension is stored. A null byte indicates the end of the extension. This section is of variable length.
A file with no extension requires only that null byte. A file with an extension requires 1 additional byte per character.

Smallest image possible = 16 pixels with 48 bit secret: 32 for header; 8 for null extension; 8 for data
Each Image pixel holds 3 Secret bits, so the Image must have at least ((secretbytes * (8 / 3)) + 14) pixels
An Image can hold ((3 * (pixels - 14)) / 8) Secret bytes.

Usage:
> 3bitspixel.py encode imagefilename.png secretfilename.ext
> 3bitspixel.py decode lacedimagename.png


Reference table for files with NO EXTENSION.
For each extension character, subtract 1 byte from secret size

     pixels |      example dimensions | Secret file size
        100 |                 10 x 10 |         32 bytes
        400 |                 20 x 20 |        144 bytes
      2,500 |                 50 x 50 |        932 bytes
     10,000 |               100 x 100 |      3,744 bytes
     40,000 |               200 x 200 |     14,994 bytes
     25,000 |               500 x 500 |     93,744 bytes (91 kb)
  1,000,000 |           1,000 x 1,000 |    374,994 bytes (366 kb)
  4,000,000 |           2,000 x 2,000 |  1,499,994 bytes (1.43 mb)
 25,000,000 |           5,000 x 5,000 |  9,374,994 bytes (8.94 mb)
100,000,000 |         10,000 x 10,000 | 37,499,994 bytes (35.7 mb)

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

# 11 for the content length
HEADER_SIZE = 11

class StegError(Exception):
    pass

def binary(i):
    return bin(i)[2:].rjust(8, '0')

def increment_pixel(save=True):
    '''
    Increment the active channel, and roll to the next pixel when appropriate.
    '''
    global pixel
    global pixel_index
    global channel_index
    channel_index += 1
    if channel_index == 3:
        channel_index = 0
        if save:
            image.putpixel((pixel_index % image.size[0], pixel_index // image.size[0]), tuple(pixel))
            #print('wrote', pixel)
        pixel_index += 1
        pixel = list(image.getpixel( (pixel_index % image.size[0], pixel_index // image.size[0]) ))
        #print('opend', pixel)

def bytes_to_pixels(bytes):
    return ((bytes * (8 / 3)) + 14)

def pixels_to_bytes(pixels):
    return ((3 * (pixels - 14)) / 8)

##############    ####      ####        ########          ######        ##########        ##############
  ####      ##    ####      ####      ####    ####      ####  ####        ####  ####        ####      ##
  ####            ######    ####    ####      ####    ####      ####      ####    ####      ####        
  ####    ##      ########  ####    ####              ####      ####      ####    ####      ####    ##  
  ##########      ##############    ####              ####      ####      ####    ####      ##########  
  ####    ##      ####  ########    ####              ####      ####      ####    ####      ####    ##  
  ####            ####    ######    ####      ####    ####      ####      ####    ####      ####        
  ####      ##    ####      ####      ####    ####      ####  ####        ####  ####        ####      ##
##############    ####      ####        ########          ######        ##########        ##############
def encode(imagefilename, secretfilename):
    global image
    global pixel
    global pixel_index
    global channel_index
    pixel_index = 0
    channel_index = 0

    def modify_pixel(bit):
        global pixel
        global channel_index
        #print(channel_index, bit)
        #print(pixel_index, channel_index, bit)
        channel = pixel[channel_index]
        channel = binary(channel)[:7] + bit
        channel = int(channel, 2)
        pixel[channel_index] = channel
        #print(pixel)


    print('Hiding "%s" within "%s"' % (secretfilename, imagefilename))
    image = Image.open(imagefilename)

    totalpixels = image.size[0] * image.size[1]
    if totalpixels < HEADER_SIZE:
        raise StegError('Image cannot have fewer than %d pixels. They are used to store Secret\'s length' % HEADER_SIZE)

    secretfile = open(secretfilename, 'rb')
    secret = secretfile.read()
    secret = list(secret)

    if secret == []:
        raise StegError('The Secret can\'t be 0 bytes.')

    secret_extension = os.path.splitext(secretfilename)[1][1:]
    secret_content_length = (len(secret) * 8) + (len(secret_extension) * 8) + 8
    requiredpixels = math.ceil((secret_content_length + 32) / 3)
    if totalpixels < requiredpixels:
        raise StegError('Image does not have enough pixels to store the Secret'
                        'Must have at least %d pixels' % requiredpixels)

    print('%d available pixels, %d required' % (totalpixels, requiredpixels))

    # --> YOU ARE HERE <--
    pixel = list(image.getpixel((0, 0)))

    # Write secret length
    secret_content_length_b = bin(secret_content_length)[2:].rjust(32, '0')
    for x in range(32):
        modify_pixel(secret_content_length_b[x])
        increment_pixel()

    # Write the secret extension
    for character in (secret_extension + chr(0)):
        character = ord(character)
        character = binary(character)
        for bit in character:
            modify_pixel(bit)
            increment_pixel()

    # Write the secret data
    for (index, byte) in enumerate(secret):
        if index % 1024 == 0:
            percentage = (index + 1) / len(secret)
            percentage = '%07.3f%%\r' % (100 * percentage)
            print(percentage, end='')
        # Convert byte integer to a binary string, and loop through characters
        byte = binary(byte)
        for (bindex, bit) in enumerate(byte):
            modify_pixel(bit)
            if not (index == secret_content_length -1 and bindex == 7):
                # If your Image dimensions are at the extreme limit of the Secret size,
                # this would otherwise raise IndexError as it tries to grab the next pixel
                # off the canvas.
                increment_pixel()
    print('100.000%')  # you know it

    if channel_index != 0:
        # The Secret data has finished, but we still have an unsaved pixel
        # (because channel_index is set to 0 when we save the active pixel above)
        image.putpixel((pixel_index % image.size[0], pixel_index // image.size[0]), tuple(pixel))

    newname = os.path.splitext(imagefilename)[0]
    newname = '%s (%s).png' % (newname, os.path.basename(secretfilename).replace('.', '_'))
    print(newname)
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
def decode(imagefilename):
    global image
    global pixel
    global pixel_index
    global channel_index
    pixel_index = 0
    channel_index = 0
    
    print('Extracting content from "%s"' % imagefilename)
    image = Image.open(imagefilename)

    # determine the content length
    content_length = ''
    for x in range(11):
        pixel = list(image.getpixel( (pixel_index % image.size[0], pixel_index // image.size[0]) ))
        pixel = pixel[:3]
        #print(pixel)
        content_length += ''.join([bin(i)[-1] for i in pixel])
        pixel_index += 1
    content_length = content_length[:-1]
    content_length = int(content_length, 2)
    print('Content bits:', content_length)
    
    # Continue from the end of the header
    # This would have been automatic if I used `increment_pixel`
    pixel_index = 10
    channel_index = 2

    # determine secret extension
    extension = ''
    while extension[-8:] != '00000000' or len(extension) % 8 != 0:
        channel = pixel[channel_index]
        channel = binary(channel)
        channel = channel[-1]
        extension += channel
        increment_pixel(save=False)
    extension = extension[:-8]
    extension = [extension[8*x: (8*x)+8] for x in range(len(extension)//8)]
    extension = [chr(int(x, 2)) for x in extension]
    extension = ''.join(extension)
    print('Extension:', extension)

    # Remove the extension length
    content_length -= 8
    content_length -= 8 * len(extension)

    # Prepare writes
    newname = os.path.splitext(imagefilename)[0]
    if extension != '':
        extension = '.' + extension
    newname = '%s (extracted)%s' % (newname, extension)
    outfile = open(newname, 'wb')

    # extract data
    content_bytes = content_length // 8
    for byte in range(content_bytes):
        if byte % 1024 == 0:
            percentage = (byte + 1) / content_bytes
            percentage = '%07.3f%%\r' % (100 * percentage)
            print(percentage, end='')

        activebyte = ''
        for bit in range(8):
            channel = pixel[channel_index]
            channel = binary(channel)[-1]
            activebyte += channel
            if not (byte == content_bytes - 1 and bit == 7):
                # If your Image dimensions are at the extreme limit of the Secret size,
                # this would otherwise raise IndexError as it tries to grab the next pixel
                # off the canvas.
                increment_pixel(save=False)
        activebyte = '%02x' % int(activebyte, 2)
        outfile.write(binascii.a2b_hex(activebyte))
    print('100.000%')  # I'm on fire
    print(newname)
    outfile.close()

if __name__ == '__main__':
    if (len(sys.argv) == 1) or (sys.argv[1] not in ['encode', 'decode']):
        print('Usage:')
        print('> 3bitspixel.py encode imagefilename.png secretfilename.ext')
        print('> 3bitspixel.py decode lacedimagename.png')

    imagefilename = sys.argv[2]

    if sys.argv[1] == 'encode':
        secretfilename = sys.argv[3]
        encode(imagefilename, secretfilename)
    else:
        decode(imagefilename)