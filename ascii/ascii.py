#  Gray = 0.21 R + 0.72 G + 0.07 B
from PIL import Image
import json
import time
import sys

asciifile = open('asciitable.json')
asciitable = json.loads(asciifile.read())
asciifile.close()
for key in asciitable:
	asciitable[key] = int(asciitable[key]) + 1
asciikeys = list(asciitable.keys())
asciivals = list(asciitable.values())
asciikeys.sort(key=asciitable.get)
each = 256 / len(asciivals)
asciivals = [((x+1) * each) for x in range(len(asciivals))]
print("Loaded ASCII table.")
	
def average(inx):
	r, g, b = 0, 0, 0
	width = inx.size[0]
	height = inx.size[1]
	area = width * height
	transparent = False
	for y in range(height):
		for x in range(width):
			pixel = inx.getpixel((x, y))
			if "RGB" in inx.mode:
				try:
					if pixel[3] == 0:
						transparent = True
				except IndexError:
					pass
				r += pixel[0]
				g += pixel[1]
				b += pixel[2]
			else:
				r += pixel
				g += pixel
				b += pixel
	if not transparent:
		r  = int(r/ area)
		g  = int(g/ area)
		b  = int(b/ area)
		i = int((0.21 * r) + (0.72 * g) + (0.07 * b))
		return [r, g, b, i]
	return [255, 255, 255, 255]

def boot():
	global asciikeys
	global asciivals
	try:
		FILENAME = input('File: ')
		if '.' not in FILENAME:
			FILENAME += '.png'
		resolution = input('x y (leave blank for standard): ')
		if resolution != "":
			XVALUE = int(resolution.split()[0])
			YVALUE = int(resolution.split()[1])
		else:
			XVALUE = 8
			YVALUE = 12
		CONTRAST = input('Smooth 1-~ (blank for standard): ')
		try:
			CONTRAST = int(CONTRAST)
			if CONTRAST < 1:
				CONTRAST = 1
		except ValueError:
			CONTRAST = 8
	except EOFError:
		FILENAME = "Raspberry.png"
		XVALUE = 8
		YVALUE = 12
		CONTRAST = 8
		#Optimal resolutions include:
		# 9 x 15
		# 3 x 5 (huge!)
		# 8 x 12
	ascii(FILENAME, XVALUE, YVALUE, CONTRAST)
	
def ascii(FILENAME, XVALUE, YVALUE, CONTRAST):
	rpi = Image.open(FILENAME)
	global asciikeys
	global asciivals
	asciikeys = asciikeys[::CONTRAST]
	asciivals = asciivals[::CONTRAST]
	width = rpi.size[0]
	height = rpi.size[1]
	charspanx = int(width / XVALUE)
	charspany = int(height / YVALUE)
	print("%d x %d characters" % (charspanx, charspany))
	output = ""
	print("Working...")
	for yline in range(charspany):
		print("\r%0.2f" % (yline/charspany), end='')
		sys.stdout.flush()
		for xline in range(charspanx):
			xcoord = xline*XVALUE
			ycoord = yline*YVALUE
	
			region = (xcoord, ycoord, xcoord+XVALUE, ycoord+YVALUE)
			region = rpi.crop(region)
			av = average(region)
			i = av[3]
			c = 0
			for value in asciivals:
				if i == 255:
					output += ' '
					break
				if i <= value:
					output += asciikeys[c]
					break
				c += 1

		output += "\n"
	output += '\n%s\n%dx%d\n%d' % (FILENAME, XVALUE, YVALUE, CONTRAST)
	
	outfile = FILENAME.split('.')[0] + '.txt'
	outfile = open(outfile, 'w')
	print(output, file=outfile)
	outfile.close()
	print("\r1.00")

if __name__ == "__main__":
	boot()