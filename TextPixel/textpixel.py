import sys
from PIL import Image as PILImage
import random
import string

ARGS_ENCODE = ['encode', 'save', 'write']
ARGS_DECODE = ['decode', 'read']
# Alternate operation names for commandline use.

def png_filename(filename):
	if filename[-4:].lower() != '.png':
		filename += '.png'
	return filename

def encode_character(text, densitymin=0, densitymax=300):
	'''
	Given a character, take its ord() value and return an
	RGB pixel representation.

	The RGB channels will become the ord value, a number
	lower than the ord value, and a number higher than the
	ord value, though the order will be randomized.

	`densitymin` and `densitymax` control how much lower and higher
	the additional values will be relative to the ord value, in %.

	Returns a tuple (R,G,B)
	'''

	densitymin = abs(densitymin)
	densitymax = abs(densitymax)

	asciivalue = ord(text)
	percentmin = int((asciivalue * densitymin) / 100)
	percentmax = int((asciivalue * densitymax) / 100)
	
	lowerfill = random.randint(asciivalue - percentmax, asciivalue - percentmin)
	upperfill = random.randint(asciivalue + percentmin, asciivalue + percentmax)

	lowerfill = max(0, lowerfill)
	upperfill = min(255, upperfill)

	rgb = [lowerfill, asciivalue, upperfill]
	random.shuffle(rgb)
	return tuple(rgb)

def encode_string(text, densitymin=0, densitymax=300):
	'''
	Given a string `text`, map each character to an RGB
	pixel, and return these pixels so they can be written to a file.

	`densitymin` and `densitymax` are passed to encode_character

	Returns a list where
	[0] is (width,height),
	[1] is a dict of pixels: {(x,y) : (R,G,B)}
	'''
	text = text.strip()

	lines = text.split('\n')
	encoded_height = len(lines)
	encoded_width = max([len(line) for line in lines])
	encoded_pixels = {}

	for y in range(encoded_height):
		line = lines[y]
		for x in range(len(line)):
			character = line[x]
			pixel = encode_character(character, densitymin, densitymax)
			encoded_pixels[(x,y)] = pixel

	dim = (encoded_width, encoded_height)
	out = [dim, encoded_pixels]
	return out

def write_pixels(dimout, filename):
	'''
	Given pixel data of the form returned by `encode_string()`,
	write it to a PNG file named `filename`.
	'''

	filename = png_filename(filename)

	dim = dimout[0]
	encoded_pixels = dimout[1]
	
	image = PILImage.new('RGBA', dim)

	for pixel in encoded_pixels:
		image.putpixel(pixel, encoded_pixels[pixel])

	image.save(filename)

##############################################################################

def decode_pixel(pixel):
	'''
	Given a tuple (R,G,B), return the decoded text character.

	The character is the str() for the middle value of the tuple.
	("middle" referring to numeric value, not index)
	'''

	pixel = sorted(list(pixel))
	character = chr(pixel[1])
	return character

def decode_image(image):
	'''
	Given an image, return the decoded string

	`image` may be a string representing the filename
	or a PIL Image object
	'''

	if isinstance(image, str):
		if image[-4:].lower() != '.png':
			image += '.png'
		image = png_filename(image)
		image = PILImage.open(image)

	width = image.size[0]
	height = image.size[1]

	decoded_string = ''

	for y in range(height):
		for x in range(width):
			pixel = image.getpixel((x,y))
			if pixel[3] == 0:
				break
			decoded_string += decode_pixel(pixel)
		decoded_string += '\n'
	decoded_string = decoded_string.strip()
	return decoded_string

def argsfail():
	print('\ninvalid parameters.')
	print('> textpixel.py encode text filename')
	print('> textpixel.py decode filename')
	quit()

if __name__ == '__main__':
	if len(sys.argv) < 3:
		argsfail()

	op = sys.argv[1].lower()

	if op in ARGS_ENCODE and len(sys.argv) == 4:
		text = sys.argv[2]
		if text[-4:].lower() == '.txt':
			try:
				tfile = open(text, 'r')
				text = tfile.read()
				tfile.close()
			except FileNotFoundError:
				pass

		filename = sys.argv[3]
		pixels = encode_string(text)
		write_pixels(pixels, filename)
		print('Done.')

	elif op in ARGS_DECODE and len(sys.argv) == 3:
		filename = sys.argv[2]
		print(decode_image(filename))

	else:
		argsfail()
