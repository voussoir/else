from PIL import Image
import os

def boot():
	path = input("Path to image or directory\n> ")
	if path == '':
		path = os.getcwd()
	objectives = input("Pixel Objective\n> ")
	objectives = objectives.replace(' ', '')
	objectives = [int(x) for x in objectives.split(',')]
	pixelify(path, objectives)

def pixelify(path, objectives=[32], subfolder="pixel"):
	if '.' in path:
		name = path.split('/')[-1]
		path = '/'.join(path.split('/')[:-1])
		images = [name]
	else:
		images = os.listdir(path)
		if path[-1] in ['/', '\\']:
			path = path[:-1]

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

	newdir = path +'/' + subfolder + '/'
	if not os.path.exists(newdir):
		print('Creating directory: ' + newdir)
		os.makedirs(newdir)

	for name in images:
		filepath = path + '/' + name
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
			newpath = newdir + parts[0] + '_' + str(objective) + '.' + parts[1]
			nimage.save(newpath)



boot()