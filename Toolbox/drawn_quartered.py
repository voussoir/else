'''
This script takes an image and splits it up into pieces as separate files.

drawn_quartered test.jpg --width 2 --height 2
drawn_quartered test.jpg outputname.jpg --width 3 --height 4
'''

import argparse
import math
import os
import PIL.Image
import sys

from voussoirkit import pathclass

def drawquarter(image, width=2, height=2):
    pieces = []
    (image_width, image_height) = image.size
    step_x = image_width / width
    step_y = image_height / height
    if (step_x != int(step_x)):
        print('Warning: Imperfect x', step_x)
    if (step_y != int(step_y)):
        print('Warning: Imperfect y', step_y)
    step_x = math.ceil(step_x)
    step_y = math.ceil(step_y)
    for y in range(height):
        end_y = y + 1
        for x in range(width):
            end_x = x + 1
            coords = (step_x * x, step_y * y, step_x * end_x, step_y * end_y)
            piece = image.crop(coords)
            pieces.append(piece)
    return pieces

def drawquarter_argparse(args):
    image = PIL.Image.open(args.input_filename)

    if args.output_filename is not None:
        output_filename = args.output_filename
    else:
        output_filename = args.input_filename

    output_path = pathclass.Path(output_filename)
    output_directory = output_path.parent
    os.makedirs(output_directory.absolute_path, exist_ok=True)
    output_filename_format = output_path.basename
    output_filename_format = output_filename_format.rsplit('.', 1)[0]
    output_filename_format += '_%dx%d_{ycoord}-{xcoord}.' % (args.width, args.height)
    output_filename_format += args.input_filename.rsplit('.', 1)[1]

    pieces = drawquarter(image, width=args.width, height=args.height)
    for (index, piece) in enumerate(pieces):
        (ycoord, xcoord) = divmod(index, args.height)
        output_filename = output_filename_format.format(xcoord=xcoord, ycoord=ycoord)
        output_filename = output_directory.with_child(output_filename)
        print(output_filename.relative_path)
        piece.save(output_filename.absolute_path)

def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('input_filename')
    parser.add_argument('output_filename', nargs='?', default=None)
    parser.add_argument('--width', dest='width', type=int, default=2)
    parser.add_argument('--height', dest='height', type=int, default=2)
    parser.set_defaults(func=drawquarter_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])
