import glob
import os
from PIL import Image
import sys

def fit_into_bounds(image_width, image_height, frame_width, frame_height):
    '''
    Given the w+h of the image and the w+h of the frame,
    return new w+h that fits the image into the frame
    while maintaining the aspect ratio.

    (1920, 1080, 400, 400) -> (400, 225)
    '''
    width_ratio = frame_width / image_width
    height_ratio = frame_height / image_height
    ratio = min(width_ratio, height_ratio)

    new_width = int(image_width * ratio)
    new_height = int(image_height * ratio)

    return (new_width, new_height)

filenames = sys.argv[1]

filenames = glob.glob(filenames)
for filename in filenames:
    i = Image.open(filename)
    if all(x.isdigit() for x in sys.argv[2:3]):
        new_x = int(sys.argv[2])
        new_y = int(sys.argv[3])
    else:
        try:
            ratio = float(sys.argv[2])
            new_x = int(i.size[0] * ratio)
            new_y = int(i.size[1] * ratio)
        except ValueError:
            print('you did it wrong')
            quit()

    (image_width, image_height) = i.size

    if new_x == 0:
        (new_x, new_y) = fit_into_bounds(image_width, image_height, 10000000, new_y)
    if new_y == 0:
        (new_x, new_y) = fit_into_bounds(image_width, image_height, new_x, 10000000)

    print(i.size, new_x, new_y)
    i = i.resize( (new_x, new_y), Image.ANTIALIAS)
    suffix = '_{width}x{height}'.format(width=new_x, height=new_y)
    (base, extension) = os.path.splitext(filename)
    newname = base + suffix + extension
    i.save(newname, quality=100)
