from PIL import Image
import hashlib
import os
import sys

def load_all_images(iterable):
    images = []
    for filename in iterable:
        print('Loading "%s"' % filename)
        try:
            image = Image.open(filename)
            image.filename = filename
            print('Loaded "%s"' % filename)
            images.append(image)
        except OSError:
            print('Could not load "%s"' % filename)
    return images

def listfiles(directory):
    files = [name for name in os.listdir(directory)]
    files = [os.path.join(directory, name) for name in files]
    files = [name for name in files if os.path.isfile(name)]
    return files

def stitch(images):
    largest_width = max(image.size[0] for image in images)
    largest_height = max(image.size[1] for image in images)
    print('Using cell size of %dx%dpx' % (largest_width, largest_height))
    grid_width = round(len(images) ** 0.5)
    # overflow adds an extra line for nonperfect squares.
    overflow = 1 if (len(images) % grid_width != 0) else 0
    grid_height = (len(images) // grid_width) + overflow
    grid_width_pixels = grid_width * largest_width
    grid_height_pixels = grid_height * largest_height

    print('Creating image of size: %dx%d (%dx%dpx)' % (grid_width, grid_height, grid_width_pixels, grid_height_pixels))
    stitched_image = Image.new('RGBA', [grid_width_pixels, grid_height_pixels])
    print('Pasting components')
    for (index, image) in enumerate(images):
        pad_x = int((largest_width - image.size[0]) / 2)
        pad_y = int((largest_height - image.size[1]) / 2)
        gridspot_x = index % grid_width
        gridspot_y = index // grid_width
        pixel_x = (gridspot_x * largest_width) + pad_x
        pixel_y = (gridspot_y * largest_height) + pad_y
        print(index, gridspot_x, gridspot_y, pixel_x, pixel_y)
        stitched_image.paste(image, (pixel_x, pixel_y))
    return stitched_image


if __name__ == '__main__':
    directory = sys.argv[1]
    images = listfiles(directory)
    directory_id = 'massstitch_%s.png' % directory
    if directory_id in images:
        images.remove(directory_id)
    images = load_all_images(images)
    stitched_image = stitch(images)
    print('Saving "%s"' % directory_id)
    stitched_image.save(directory_id)