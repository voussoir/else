TextPixel
==============

Encode / Decode between strings and PNG images. Can be imported or used on the commandline. Since it uses one channel to store each character, this program is only compatible with characters between 0 and 255 in unicode.

One channel is used to store the character, and the other two are randomized, so the output looks different every time.

python example:

    encoded_string = textpixel.encode_string('Wow, look!')
    textpixel.write_pixels(encoded_string, 'wowlook.png')


commandline example:

	> textpixel encode bears.txt bears
	Done.
	
	> textpixel decode bears
	Once upon a time there
	was a book.
	
	It was about bears.
	So many bears.