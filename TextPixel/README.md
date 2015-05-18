TextPixel
==============

Encode / Decode between strings and PNG images. Can be imported or used on the commandline. Since it uses one channel to store each character, this program is only compatible with characters between 0 and 255 in unicode.

One channel is used to store the character, and the other two are randomized, so the output looks different every time.

When used from the commandline, encoding and decoding looks like this:

	> textpixel.py encode text filename
	> textpixel.py decode filename

In the commandline, the parameter `text` can be the filename of a .txt file, and its contents will become the text. This is not the case for python usage.

python example:

    encoded_string = textpixel.encode_string('Wow, look!')
    textpixel.write_pixels(encoded_string, 'wowlook.png')

    decoded_string = textpixel.decode_image('wowlook.png')
    print(decoded_string)


commandline example:

	> textpixel encode bears.txt bears
	Done.
	
	> textpixel decode bears
	Once upon a time there
	was a book.
	
	It was about bears.
	So many bears.