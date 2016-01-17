from PIL import Image
import sys

def chunk_iterable(iterable, chunk_length, allow_incomplete=True):
    '''
    Given an iterable, divide it into chunks of length `chunk_length`.
    If `allow_incomplete` is True, the final element of the returned list may be shorter
    than `chunk_length`. If it is False, those items are discarded.
    '''
    if len(iterable) % chunk_length != 0 and allow_incomplete:
        overflow = 1
    else:
        overflow = 0

    steps = (len(iterable) // chunk_length) + overflow
    return [iterable[chunk_length * x : (chunk_length * x) + chunk_length] for x in range(steps)]

def hex_to_rgb(x):
    x = x.replace('#', '')
    x = chunk_iterable(x, 2)
    print(x)
    x = tuple(int(i, 16) for i in x)
    return x

def mesh_generator(image_width, image_height, square_size, mode):
    square = square_size * 2
    print(mode)
    x_space = square_size * mode[0]
    y_space = square_size * mode[1]
    odd_x = False
    odd_y = False
    for y in range(0, image_height, y_space):
        odd_y = not odd_y
        for x in range(0, image_width, x_space):
            odd_x = not odd_x
            boost_x = int(odd_y) * square_size * mode[2]
            boost_y = int(odd_x) * square_size * mode[3]
            #print(boost_x, boost_y)
            #x += boost_x
            #y += boost_y
            yield (x + boost_x, y + boost_y)

def make_image(image_width, image_height, square_size, mode, bgcolor='#00000000', fgcolor='#000000'):
    pattern_repeat_width = (2 * square_size * mode[0])
    pattern_repeat_height = (2 * square_size * mode[1])
    print(pattern_repeat_width, pattern_repeat_height)

    bgcolor = hex_to_rgb(bgcolor)
    fgcolor = hex_to_rgb(fgcolor)

    pattern = Image.new('RGBA', (pattern_repeat_width, pattern_repeat_height), bgcolor)
    #image = Image.new('RGBA', (image_width, image_height))
    blackbox = Image.new('RGBA', (square_size, square_size), fgcolor)
    for pair in mesh_generator(pattern_repeat_width, pattern_repeat_height, square_size, mode):
        pattern.paste(blackbox, pair)
    while pattern.size[0] < image_width or pattern.size[1] < image_height:
        p = pattern
        (w, h) = p.size
        print('expanding from', w, h)
        pattern = Image.new('RGBA', (w * 2, h * 2))
        for y in range(2):
            for x in range(2):
                pattern.paste(p, (w * x, h * y))
    image = pattern.crop((0, 0, image_width, image_height))

    mode = [str(x) for x in mode]
    mode = ''.join(mode)
    filename = 'mesh_%dx%d_%d_%s.png' % (image_width, image_height, square_size, mode)
    image.save(filename)
    print('Saved %s' % filename)

def listget(li, index, fallback=None):
    try:
        return li[index]
    except IndexError:
        return fallback

if __name__ == '__main__':
    image_width = int(sys.argv[1])
    image_height = int(sys.argv[2])
    square_size = int(listget(sys.argv, 3, 1))
    x_spacing = int(listget(sys.argv, 4, 2))
    y_spacing = int(listget(sys.argv, 5, 2))
    x_alternator = int(listget(sys.argv, 6, 0))
    y_alternator = int(listget(sys.argv, 7, 0))
    bgcolor = listget(sys.argv, 8, '#00000000')
    fgcolor = listget(sys.argv, 9, '#000000')
    mode = (x_spacing, y_spacing, x_alternator, y_alternator)
    make_image(image_width, image_height, square_size, mode, bgcolor, fgcolor)