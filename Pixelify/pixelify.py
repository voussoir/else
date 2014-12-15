from PIL import Image
import os

def boot():
	path = input("Path to image or directory\n> ")
	if path == '':
		path = os.getcwd()
	objectives = input("Pixel Objective\n> ")
	objectives = objectives.replace(' ', '')
	objectives = [int(x) for x in objectives.split(',')]
	outpath = input("Path to output (Blank for standard)\n> ")
	pixelify(path, objectives, outpath=outpath)

def pixelify(path, objectives=[32], subfolder="pixel", outpath=""):
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

	if not os.path.exists(outpath):
		print('Creating directory: ' + outpath)
		os.makedirs(outpath)

	for name in images:
		filepath = path + name
		image = Image.open(filepath)

		for objective in objectives:
			print("Working: " + name, objective)
			image_width = image.size[0]
			image_height = image.size[1]
			ratio = objective / max([image_width, image_height])
			new_width = image_width * ratio
			new_height = image_height * ratio
			nimage = image.resize((round(new_width), round(new_height)), 1)
			nimage = nimage.resize((image_width, image_height), 0)
	
			parts = name.split('.')
			newpath = outpath + parts[0] + '_' + str(objective) + '.' + parts[1]
			nimage.save(newpath)

if __name__ == "__main__":
	while True:
		boot()
		print('\n')