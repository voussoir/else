import argparse
import os
import PIL.Image
import random
import sys

SVG_TEMPLATE = '''
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:cc="http://creativecommons.org/ns#"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:svg="http://www.w3.org/2000/svg"
    xmlns="http://www.w3.org/2000/svg"
    id="svg5633"
    version="1.1"
    viewBox="0 0 {width} {height}"
    height="{height}mm"
    width="{width}mm">
    <defs
        id="defs5627" />
    <metadata
        id="metadata5630">
    <rdf:RDF>
        <cc:Work
            rdf:about="">
        <dc:format>image/svg+xml</dc:format>
        <dc:type
            rdf:resource="http://purl.org/dc/dcmitype/StillImage" />
        <dc:title></dc:title>
        </cc:Work>
    </rdf:RDF>
</metadata>
<g
    id="layer1">
    {rectangles}
</g>
</svg>
'''.strip()

RECTANGLE_TEMPLATE = '''
<rect
y="{y}"
x="{x}"
height="{height}"
width="{width}"
id="{id}"
style=
    "opacity:{opacity};
    fill:{fill};
    fill-opacity:{opacity};
    fill-rule:nonzero;
    stroke:none;
    stroke-width:0;
    stroke-linecap:round;
    stroke-linejoin:miter;
    stroke-miterlimit:4;
    stroke-dasharray:none;
    stroke-dashoffset:0;
    stroke-opacity:1"
/>
'''.strip()

def normalize_rgb(rgb, mode):
    if mode == '1':
        v = rgb * 255
        return (v, v, v, 255)
    if mode == 'L':
        return (rgb, rgb, rgb, 255)
    if mode == 'RGB':
        return rgb + (255, )
    if mode == 'RGBA':
        return rgb

def int_to_hex(i):
    return hex(i)[2:].rjust(2, '0')

def rgb_to_hex(rgb):
    return '#' + ''.join(int_to_hex(x) for x in rgb)

def make_svg(image):
    rectangles = []
    (width, height) = image.size
    for y in range(height):
        for x in range(width):
            pixel = image.getpixel((x, y))
            pixel = normalize_rgb(pixel, image.mode)
            (rgb, opacity) = (pixel[:-1], pixel[-1])
            fill = rgb_to_hex(rgb)
            #print(fill)
            opacity = opacity / 255
            rectangle = RECTANGLE_TEMPLATE.format(
                x=x,
                y=y,
                width=1,
                height=1,
                id=str(random.random()),
                fill=fill,
                opacity=opacity,
            )
            rectangles.append(rectangle)
            #print(rectangle)
    rectangles = '\n'.join(rectangles)
    svg = SVG_TEMPLATE.format(width=width, height=height, rectangles=rectangles)
    return svg

def image_to_svg(image_filename, svg_filename=None):
    svg_filename = svg_filename or ''
    if not svg_filename:
        svg_filename = image_filename + '.svg'

    image = PIL.Image.open(image_filename)
    svg = make_svg(image)
    with open(svg_filename, 'w') as handle:
        handle.write(svg)

def image_to_svg_argparse(args):
    return image_to_svg(
        image_filename=args.image_filename,
        svg_filename=args.svg_filename
    )

def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('image_filename')
    parser.add_argument('svg_filename', nargs='?', default=None)
    parser.set_defaults(func=image_to_svg_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])
