import argparse
import math
import PIL.Image
import PIL.ImageDraw
import sys

def choose_guideline_style(guideline_mod):
    if guideline_mod % 16 == 0:
        return ('#1f32ff', 3)
    if guideline_mod % 8 == 0:
        return ('#80f783', 2)
    if guideline_mod % 4 == 0:
        return ('#f4bffb', 1)

def in_ellipsoid(x, y, z, rad_x, rad_y, rad_z, center_x=None, center_y=None, center_z=None):
    '''
    Given a point (x, y, z), return whether that point lies inside the
    ellipsoid defined by (x/a)^2 + (y/b)^2 + (z/c)^2 = 1
    '''
    if center_x is None: center_x = rad_x
    if center_y is None: center_y = rad_y
    if center_z is None: center_z = rad_z
    #print(x, y, z, rad_x, rad_y, rad_z, center_x, center_y, center_z)
    x = ((x - center_x) / rad_x) ** 2
    y = ((y - center_y) / rad_y) ** 2
    z = ((z - center_z) / rad_z) ** 2
    distance = x + y + z
    #print(distance)
    return distance < 1

def voxelspheregenerator(WIDTH, HEIGH, DEPTH, WALL_THICKNESS=None, specific=None):
    ODD_W = WIDTH % 2 == 1
    ODD_H = HEIGH % 2 == 1
    ODD_D = DEPTH % 2 == 1

    RAD_X = WIDTH / 2
    RAD_Y = HEIGH / 2
    RAD_Z = DEPTH / 2

    if WALL_THICKNESS:
        INNER_RAD_X = RAD_X - WALL_THICKNESS
        INNER_RAD_Y = RAD_Y - WALL_THICKNESS
        INNER_RAD_Z = RAD_Z - WALL_THICKNESS

    X_CENTER = {WIDTH // 2} if ODD_W else {WIDTH // 2, (WIDTH // 2) - 1}
    Y_CENTER = {HEIGH // 2} if ODD_H else {HEIGH // 2, (HEIGH // 2) - 1}
    Z_CENTER = {DEPTH // 2} if ODD_D else {DEPTH // 2, (DEPTH // 2) - 1}

    layer_digits = len(str(DEPTH))
    filename_form = '{w}x{h}x{d}w{wall}-{{layer:0{digits}}}.png'
    filename_form = filename_form.format(
        w=WIDTH,
        h=HEIGH,
        d=DEPTH,
        wall=WALL_THICKNESS if WALL_THICKNESS else 0,
        digits=layer_digits,
    )

    dot_highlight = PIL.Image.open('dot_highlight.png')
    dot_normal = PIL.Image.open('dot_normal.png')
    dot_corner = PIL.Image.open('dot_corner.png')
    pixel_scale = dot_highlight.size[0]

    # Space between each pixel
    PIXEL_MARGIN = 7

    # Space between the pixel area and the canvas
    PIXELSPACE_MARGIN = 2

    # Space between the canvas area and the image edge
    CANVAS_MARGIN = 2

    LABEL_HEIGH = 20
    FINAL_IMAGE_SCALE = 1

    PIXELSPACE_WIDTH = (WIDTH * pixel_scale) + ((WIDTH - 1) * PIXEL_MARGIN)
    PIXELSPACE_HEIGH = (HEIGH * pixel_scale) + ((HEIGH - 1) * PIXEL_MARGIN)

    CANVAS_WIDTH = PIXELSPACE_WIDTH + (2 * PIXELSPACE_MARGIN * pixel_scale)
    CANVAS_HEIGH = PIXELSPACE_HEIGH + (2 * PIXELSPACE_MARGIN * pixel_scale)

    IMAGE_WIDTH = CANVAS_WIDTH + (2 * CANVAS_MARGIN * pixel_scale)
    IMAGE_HEIGH = CANVAS_HEIGH + (2 * CANVAS_MARGIN * pixel_scale) + LABEL_HEIGH

    CANVAS_START_X = CANVAS_MARGIN * pixel_scale
    CANVAS_START_Y = CANVAS_MARGIN * pixel_scale
    CANVAS_END_X = CANVAS_START_X + CANVAS_WIDTH
    CANVAS_END_Y = CANVAS_START_Y + CANVAS_HEIGH

    PIXELSPACE_START_X = CANVAS_START_X + (PIXELSPACE_MARGIN * pixel_scale)
    PIXELSPACE_START_Y = CANVAS_START_Y + (PIXELSPACE_MARGIN * pixel_scale)
    PIXELSPACE_END_X = PIXELSPACE_START_X + PIXELSPACE_WIDTH
    PIXELSPACE_END_Y = PIXELSPACE_START_Y + PIXELSPACE_HEIGH

    GUIDELINE_MOD_X = math.ceil(RAD_X)
    GUIDELINE_MOD_Y = math.ceil(RAD_Y)

    def pixel_coord(x, y):
        x = PIXELSPACE_START_X + (x * pixel_scale) + (x * PIXEL_MARGIN)
        y = PIXELSPACE_START_Y + (y * pixel_scale) + (y * PIXEL_MARGIN)
        return (x, y)

    def make_layer_matrix(z):
        layer_matrix = [[None for y in range(math.ceil(RAD_Y))] for x in range(math.ceil(RAD_X))]

        # Generate the upper left corner.
        furthest_x = RAD_X
        furthest_y = RAD_Y
        for y in range(math.ceil(RAD_Y)):
            for x in range(math.ceil(RAD_X)):
                ux = x + 0.5
                uy = y + 0.5
                uz = z + 0.5

                within = in_ellipsoid(ux, uy, uz, RAD_X, RAD_Y, RAD_Z)
                if WALL_THICKNESS:
                    in_hole = in_ellipsoid(
                        ux, uy, uz,
                        INNER_RAD_X, INNER_RAD_Y, INNER_RAD_Z,
                        RAD_X, RAD_Y, RAD_Z
                    )
                    within = within and not in_hole
                if within:
                    if x in X_CENTER or y in Y_CENTER:
                        if z in Z_CENTER:
                            dot = dot_normal
                        else:
                            dot = dot_highlight
                    else:
                        if z in Z_CENTER:
                            dot = dot_highlight
                        else:
                            dot = dot_normal
                    layer_matrix[x][y] = dot
                    furthest_x = min(x, furthest_x)
                    furthest_y = min(y, furthest_y)
                    #layer_image.paste(dot, box=(pixel_coord_x, pixel_coord_y))

        # Mark the corner pieces
        furthest_y = math.floor(furthest_y)
        for y in range(furthest_y, math.ceil(RAD_Y-1)):
            for x in range(furthest_x, math.ceil(RAD_X-1)):
                is_corner = (
                    layer_matrix[x][y] is not None and
                    layer_matrix[x-1][y+1] is not None and
                    layer_matrix[x+1][y-1] is not None and
                    (
                        # Outer corners
                        (layer_matrix[x][y-1] is None and layer_matrix[x-1][y] is None) or
                        # Inner corners, if hollow
                        (layer_matrix[x][y+1] is None and layer_matrix[x+1][y] is None)
                    )
                )
                if is_corner:
                    layer_matrix[x][y] = dot_corner

        return layer_matrix

    def make_layer_image(layer_matrix):
        layer_image = PIL.Image.new('RGBA', size=(IMAGE_WIDTH, IMAGE_HEIGH), color=(0, 0, 0, 0))
        draw = PIL.ImageDraw.ImageDraw(layer_image)

        # Plot.
        LABEL_Y = (2 * math.ceil(RAD_Y))
        for y in range(math.ceil(RAD_Y)):
            bottom_y = (HEIGH - 1) - y
            for x in range(math.ceil(RAD_X)):
                right_x = (WIDTH - 1) - x
                if layer_matrix[x][y] is not None:
                    layer_image.paste(layer_matrix[x][y], box=pixel_coord(x, y))
                    layer_image.paste(layer_matrix[x][y], box=pixel_coord(right_x, y))
                    layer_image.paste(layer_matrix[x][y], box=pixel_coord(x, bottom_y))
                    layer_image.paste(layer_matrix[x][y], box=pixel_coord(right_x, bottom_y))

        # Draw the counting helpers along the bottom.
        # Start at the center top of the circle and walk along the edge.
        # Every time the walker 'falls' down, mark the distance.
        def put_counterhelper(start_x, end_x, y):
            if start_x > end_x:
                return
            y = (HEIGH + 1) - y
            span = end_x - start_x
            center = start_x + 1
            draw.text(pixel_coord(center, y), str(span), fill='#000')

        y = 0
        x = math.floor(RAD_X) - 1
        end_x = x
        start_y = None
        while x >= y and y < RAD_Y:
            #print(x, y, start_y)
            pixel = layer_matrix[x][y]
            if pixel is None:
                y += 1
                if x != end_x:
                    put_counterhelper(x, end_x, y)
                    if start_y is None:
                        start_y = y
                    else:
                        put_counterhelper(x, end_x, start_y)
                end_x = x
                continue
            x -= 1
        y += 1
        put_counterhelper(x, end_x, y)
        
        # To draw the guidelines, start from 
        for x in range(GUIDELINE_MOD_X % 4, WIDTH + 4, 4):
            # Vertical guideline
            as_if = GUIDELINE_MOD_X - x
            #print(x, as_if)
            line_x = PIXELSPACE_START_X + (x * pixel_scale) + (x * PIXEL_MARGIN)
            line_x = line_x - PIXEL_MARGIN + (PIXEL_MARGIN // 2)
            if line_x >= PIXELSPACE_END_X:
                continue
            (color, width) = choose_guideline_style(as_if)
            draw.line((line_x, CANVAS_START_Y, line_x, CANVAS_END_Y - 1), fill=color, width=width)
            draw.text((line_x, CANVAS_END_X), str(x), fill='#000')

        for y in range(GUIDELINE_MOD_Y % 4, HEIGH + 4, 4):
            # Horizontal guideline
            as_if = GUIDELINE_MOD_Y - y
            #print(y, as_if)
            line_y = PIXELSPACE_START_Y + (y * pixel_scale) + (y * PIXEL_MARGIN)
            line_y = line_y - PIXEL_MARGIN + (PIXEL_MARGIN // 2)
            if line_y >= PIXELSPACE_END_Y:
                continue
            (color, width) = choose_guideline_style(as_if)
            draw.line((CANVAS_START_X, line_y, CANVAS_END_X - 1, line_y), fill=color, width=width)
            draw.text((CANVAS_END_X, line_y), str(y), fill='#000')

        draw.rectangle((CANVAS_START_X, CANVAS_START_Y, CANVAS_END_X - 1, CANVAS_END_Y - 1), outline='#000')
        draw.text((CANVAS_START_X, IMAGE_HEIGH - LABEL_HEIGH), layer_filename, fill='#000')
        print(layer_filename)
        if FINAL_IMAGE_SCALE != 1:
            layer_image = layer_image.resize((FINAL_IMAGE_SCALE * IMAGE_WIDTH, FINAL_IMAGE_SCALE * IMAGE_HEIGH))

        return layer_image

    if specific is None:
        zrange = range(DEPTH)
    elif isinstance(specific, int):
        zrange = [specific]
    else:
        zrange = specific

    layer_matrices = []
    for z in zrange:
        if z < math.ceil(RAD_Z):
            layer_matrix = make_layer_matrix(z)
            layer_matrices.append(layer_matrix)
        else:
            layer_matrix = layer_matrices[(DEPTH - 1) - z]
        layer_filename = filename_form.format(layer=z)
        layer_image = make_layer_image(layer_matrix)
        layer_image.save(layer_filename)


def voxelsphere_argparse(args):
    height_depth_match = bool(args.height) == bool(args.depth)
    if not height_depth_match:
        raise ValueError('Must provide both or neither of height+depth. Not just one.')

    if (args.height is args.depth is None):
        args.height = args.width
        args.depth = args.width

    wall_thickness = int(args.wall_thickness) if args.wall_thickness else None
    specific = int(args.specific) if args.specific else None
    voxelspheregenerator(
        WIDTH=int(args.width),
        HEIGH=int(args.height),
        DEPTH=int(args.depth),
        WALL_THICKNESS=wall_thickness,
        specific=specific,
    )


def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('width')
    parser.add_argument('height', nargs='?', default=None)
    parser.add_argument('depth', nargs='?', default=None)
    parser.add_argument('--wall', dest='wall_thickness', default=None)
    parser.add_argument('--specific', dest='specific', default=None)
    parser.set_defaults(func=voxelsphere_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])
