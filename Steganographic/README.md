Steganographic
==============

    2015 01 15:
        Now supports variable "bitness", the number of bits per color channel to overwrite.
        Previously, bitness was always 1, to maximize transparency.
        Now, bitness can be 1-8 to favor transparency or information density.

&nbsp;

Let's be honest, this was really just an excuse to make big Terminal headers out of hashmarks.

&nbsp;

Requires `pip install pillow`

&nbsp;

Hide files in images!

For each color channel of each pixel in an Image, modify the least significant bit to represent a bit of the Secret file.  
This changes the RGB value of the pixel by a usually-imperceptible amount.  
The first 32 bits (10.66 pixels) will be used to store the length of the Secret content in big endian.  
Then, the Secret's extension is stored. A null byte indicates the end of the extension. This section is of variable length.  
A file with no extension requires only that null byte. A file with an extension requires 1 additional byte per character.  

Smallest image possible = 16 pixels with 48 bit secret: 32 for header; 8 for null extension; 8 for data.  
Each Image pixel holds 3 Secret bits, so the Image must have at least `((secretbytes * (8 / 3)) + 14)` pixels.  
An Image can hold `((3 * (pixels - 14)) / 8)` Secret bytes.  

    Usage:
    > steganographic.py encode imagefilename.png secretfilename.ext bitness
    > steganographic.py decode lacedimagename.png bitness

where bitness defaults to 1 in both cases.


Reference table for files with NO EXTENSION and bitness of 1.
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

<p align="center">
    <img src="https://github.com/voussoir/else/blob/master/.GitImages/steganographic_logo.png?raw=true" alt="steganographic"/>
</p>