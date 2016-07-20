import argparse
import os
import PIL.ImageFilter
import PIL.Image
import sys

def blur_letterbox(
        image,
        new_width=None,
        new_height=None,
        blurring=None,
    ):

    (iw, ih) = image.size
    new_width = new_width or iw
    new_height = new_height or ih

    if blurring is None:
        blurring = (new_width * new_height) * 0.00001
        print('Using bluriness', blurring)

    background = image.resize(fit_over_bounds(iw, ih, new_width, new_height), PIL.Image.ANTIALIAS)
    background = background.filter(PIL.ImageFilter.GaussianBlur(radius=blurring))
    foreground = image.resize(fit_into_bounds(iw, ih, new_width, new_height), PIL.Image.ANTIALIAS)

    background_offsets = offsets(background, new_width, new_height)
    foreground_offsets = offsets(foreground, new_width, new_height)

    final = PIL.Image.new(mode=image.mode, size=(new_width, new_height))
    final.paste(background, (background_offsets))
    final.paste(foreground, (foreground_offsets))
    return final

def fit_into_bounds(iw, ih, fw, fh):
    '''
    Given the w+h of the image and the w+h of the frame,
    return new w+h that fits the image into the frame
    while maintaining the aspect ratio and leaving blank space
    everywhere else
    '''
    ratio = min(fw/iw, fh/ih)

    w = int(iw * ratio)
    h = int(ih * ratio)

    return (w, h)

def fit_over_bounds(iw, ih, fw, fh):
    '''
    Given the w+h of the image and the w+h of the frame,
    return new w+h that covers the entire frame
    while maintaining the aspect ratio
    '''
    ratio = max(fw/iw, fh/ih)

    w = int(iw * ratio)
    h = int(ih * ratio)

    return (w, h)

def listget(li, index, fallback=None):
    try:
        return li[index]
    except IndexError:
        return fallback

def offsets(image, new_width, new_height):
    '''
    Calculate the horizontal and vertical offsets
    needed to center the image in the given box
    '''
    horizontal = int((new_width - image.size[0]) / 2)
    vertical = int((image.size[1] - new_height) / 2) * -1
    return (horizontal, vertical)


def main(argv):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('filename')
    parser.add_argument('-w', '--width', dest='width', default=None)
    parser.add_argument('-h', '--height', dest='height', default=None)
    parser.add_argument('-b', '--blurring', dest='blurring', default=None)

    args = parser.parse_args(argv)
    if args.width is None and args.height is None:
        print('Need a new width or height')
        return

    int_or_none = lambda x: int(x) if x else x
    (base, extension) = os.path.splitext(args.filename)
    new_name = base + '_blur' + extension
    image = PIL.Image.open(args.filename)
    image = blur_letterbox(
        image,
        int_or_none(args.width),
        int_or_none(args.height),
        int_or_none(args.blurring)
    )
    image.save(new_name)

if __name__ == '__main__':
    main(sys.argv[1:])