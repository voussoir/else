TEMPLATE_PRIMARY = '''
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:cc="http://creativecommons.org/ns#"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:svg="http://www.w3.org/2000/svg"
    xmlns="http://www.w3.org/2000/svg"
    version="1.1"
    id="svg2"
    viewBox="0 0 744.09448819 1052.3622047"
    height="297mm"
    width="210mm" >
    <defs id="defs4" >
        <filter
            id="filter20779"
            style="color-interpolation-filters:sRGB" />
        <filter
            style="color-interpolation-filters:sRGB"
            id="filter26457"
            x="-0.012382473"
            width="1.0247649"
            y="-0.011640447"
            height="1.0232809" >

            <feGaussianBlur
                id="feGaussianBlur26459"
                stdDeviation="3.2073868" />
        </filter>
        <mask
            id="mask26461"
            maskUnits="userSpaceOnUse" >
                <g
                    style="fill:#ffffff;fill-opacity:1;stroke:none"
                    transform="matrix(1.5199904,0,0,1.5199673,-1612.5515,-1151.5565)"
                    id="g26463" >
                        <path
                            id="path26465"
                            transform="matrix(0.65789889,0,0,0.65790889,1060.8942,757.62709)"
                            d="
                             M 682.8789,715.34763
                             682.857,337.12518
                             372.03711,195.5332
                             61.221001,337.25218
                             61.220697,715.32812
                             372.041,856.80518 Z"
                            style="
                            opacity:1;
                            fill:#ffffff;
                            fill-opacity:1;
                            fill-rule:nonzero;
                            stroke:none;
                            stroke-width:3.34395361;
                            stroke-linecap:round;
                            stroke-linejoin:miter;
                            stroke-miterlimit:4;
                            stroke-dasharray:none;
                            stroke-dashoffset:0;
                            stroke-opacity:1" />
                </g>
        </mask>
    </defs>
    <g
    id="layer1">
        <g
        mask="url(#mask26461)"
        style="filter:url(#filter26457)" id="g24913" >
            <g
            transform="matrix(1.0361037,-0.47199221,1.0361037,0.47199221,-801.62397,128.09956)"
            style="fill:#000000;fill-opacity:1" >
                {elements_top}
            </g>
            <g
            transform="matrix(-1.0361028,0.47161497,0,1.2603136,884.86634,-558.55115)"
            style="fill:#000000;fill-opacity:1" >
                {elements_left}
            </g>
            <g
            transform="matrix(1.0361028,0.47161497,0,1.2603136,-140.77133,-558.55239)"
            style="fill:#000000;fill-opacity:1;stroke:none;stroke-opacity:1" >
                {elements_right}
            </g>
        </g>
        <g
        mask="url(#mask26461)"
        >
            <g
            transform="matrix(1.0361037,-0.47199221,1.0361037,0.47199221,-801.62397,128.09956)"
            style="fill:#000000;fill-opacity:1" >
                {elements_top}
            </g>
            <g
            transform="matrix(-1.0361028,0.47161497,0,1.2603136,884.86634,-558.55115)"
            style="fill:#000000;fill-opacity:1" >
                {elements_left}
            </g>
            <g
            transform="matrix(1.0361028,0.47161497,0,1.2603136,-140.77133,-558.55239)"
            style="fill:#000000;fill-opacity:1;stroke:none;stroke-opacity:1" >
                {elements_right}
            </g>
        </g>
    </g>
</svg>
'''
TEMPLATE_PIXEL = '''
            <path
                d="m {x},{y} {pixsize},0 0,{pixsize} -{pixsize},0 z"
                id="{id}"
                style="opacity:{opacity};fill:#{color}"
                />
'''
import os
import PIL.Image
import random
import sys

# These numbers are MAGIC, and only work because of how the template was made.
SQUARE_WIDTH = 300
START_X = 194.94924
START_Y = 637.82417

def hexadecimal(i):
    i = hex(i)[2:]
    width = 2 - (len(i) % 2)
    if width == 2: width = 0
    i = ('0'*width) + i
    return i

def mirror(image, direction):
    new_image = image.copy()
    for y in range(image.size[1]):
        for x in range(image.size[0]):
            pixel = image.getpixel((x, y))
            if direction == 'horizontal':
                x = (image.size[0] - 1) - x
            elif direction == 'vertical':
                y = (image.size[1] - 1) - y
            new_image.putpixel((x, y), pixel)
    return new_image


def vectorize(filenames):
    images = [PIL.Image.open(f) for f in filenames]
    if len(images) == 1:
        images = [images[0], images[0], images[0]]
    elif len(images) == 2:
        images = [images[0], images[1], images[1]]
    elif len(images) == 3:
        pass
    else:
        raise ValueError('Invalid number of images supplied')

    images[0] = images[0].rotate(270)
    images[2] = mirror(images[2], 'horizontal')
    elements_total = []
    for (image_index, image) in enumerate(images):
        elements_local = []
        width = image.size[0]
        step = SQUARE_WIDTH / width
        pixsize = SQUARE_WIDTH / width
        for y in range(width):
            y_point = START_Y + (y * step)
            for x in range(width):
                x_point = START_X + (x * step)
                color = image.getpixel((x, y))

                opacity = 1
                if isinstance(color, int):
                    color = hexadecimal(color) * 3
                elif isinstance(color, tuple):
                    if len(color) == 4:
                        opacity = color[3] / 255
                    if len(color) >= 3:
                        color = ''.join(hexadecimal(channel) for channel in color[:3])

                element = TEMPLATE_PIXEL.format(
                    x=x_point,
                    y=y_point,
                    opacity=opacity,
                    pixsize=pixsize,
                    color=color,
                    id='face_%d_%d' % (image_index, x + (y*width)))
                elements_local.append(element)
        elements_total.append(elements_local)

    elements_total = [''.join(elements) for elements in elements_total]
    image = TEMPLATE_PRIMARY.format(elements_top=elements_total[0], elements_right=elements_total[1], elements_left=elements_total[2])
    image = image.strip()

    basenames = [os.path.splitext(f)[0] for f in filenames]
    outputname = '+'.join(basenames) + '.svg'
    print(outputname)
    f = open(outputname, 'w')
    f.write(image)
    f.close()

if __name__ == '__main__':
    filenames = sys.argv[1:]
    vectorize(filenames)