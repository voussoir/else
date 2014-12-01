import imageaverage
from PIL import Image
def develop():
	out = open('t.txt', 'w')
	image = Image.open('asciichars.png')
	c = 0
	for x in range(96):
		x *= 15
		chunk = image.crop((0, x, 9, x+14))
		av = imageaverage.average(chunk)
		c += 1
		chunk.save("individual\\%d_%d.png" % (c, av[3]))
		print(av[3], file=out)
		print(c)
	out.close()

develop()