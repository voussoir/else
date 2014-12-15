Pixelify
========

Requires PIL, which has been adapted to Python3 under the name pillow

    pip install pillow

Takes an image, or a folder full of images, and produces pixelated versions of each image according to an "objective". That is, how the image would look if it was forced to fit into an *objective x objective* frame. But, the actual output file will be the same dimensions as the original, simply pixelated.

<p align="center">
  <img src="https://raw.githubusercontent.com/voussoir/else/master/Pixelify/examples/NeilDeGrasseTyson.png?raw=true" alt="NDGT"/>
  <img src="https://raw.githubusercontent.com/voussoir/else/master/Pixelify/examples/pixel/NeilDeGrasseTyson_32.png?raw=true" alt="NDGT"/>
</p>

Examples:

    You are in a folder called C:\pics where there are 2 images: 1.png, 2.png

    Path to image or directory
	> 1.png
	Pixel Objective
	> 32

	A folder called "pixel" is created, and 1_32.png is inside.

	____________

	Path to image or directory
	> 1.png
	Pixel Objective
	> 32, 64, 128

	1_32.png, 1_64.png, and 1_128.png have been created

	___________

	Path to image or directory
	> 
	Pixel Objective
	> 32

	Path was left completely blank (no spaces or anything), so it uses the current folder.
	1_32.png and 2_32.png have been created. 

	____________

	Path to image or directory
	> C:\otherfolder
	Pixel Objective
	> 24

	C:\otherfolder\pixel\ is now full of 24-objective images.
