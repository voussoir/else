from PIL import Image
import os
import sys
import urllib.request

def boot():
	path = input("Path to image or directory\n> ")
	if path == '':
		path = os.getcwd()
	objectives = input("Pixel Objective\n> ")
	objectives = objectives.replace(' ', '')
	objectives = [int(x) for x in objectives.split(',')]
	outpath = input("Path to output (Blank for standard)\n> ")
	start(path, objectives, outpath=outpath)

def start(path, objectives=[32], subfolder="pixel", outpath=""):
	if '.' in path:
		path = path.replace('\\', '/')
		name = path.split('/')[-1]
		path = '/'.join(path.split('/')[:-1])
		images = [name]
	else:
		images = os.listdir(path)
		if path[-1] in ['/', '\\']:
			path = path[:-1]

	print(path)
	
	if outpath == "":
		outpath = path + '/' + subfolder + '/'
	elif ':' not in outpath:
		outpath = path + '/' + outpath + '/'
	if outpath[-1] not in ['/', '\\']:
		outpath += '/'
	path += '/'

	print('from:', path)
	print('  to:',outpath)

	done = False
	while not done:
		done = True
		for name in images:
			ext = name.lower()[-4:]
			if ext != '.png' and ext != '.jpg':
				done = False
				images.remove(name)
				if name != subfolder:
					print('Unlisted "%s": not .jpg or .png' % name)
				break

	os.makedirs(outpath, exist_ok=True)

	for name in images:
		filepath = path + name
		image = Image.open(filepath)

		for objective in objectives:
			nimage = pixelify(image, name, objective)	
			parts = name.split('.')
			newpath = outpath + parts[0] + '_' + str(objective) + '.' + parts[1]
			nimage.save(newpath, quality=100)

def pixelify(image, name, objective):
	print("Working: " + name, objective)
	image = image.copy()
	image_width = image.size[0]
	image_height = image.size[1]
	ratio = objective / max([image_width, image_height])
	new_width = image_width * ratio
	new_height = image_height * ratio
	image = image.resize((round(new_width), round(new_height)), 1)
	image = image.resize((image_width, image_height), 0)
	return image

if __name__ == "__main__":
	if len(sys.argv) > 1:
		print(sys.argv)
		path = sys.argv[1]
		objectives = [32]
		outpath = ""
		try:
			objectives = [int(x) for x in sys.argv[2].split(',')]
			outpath = sys.argv[3]
		except IndexError:
			pass
		start(path, objectives, outpath=outpath)
	else:
		while True:
			boot()
			print('\n')