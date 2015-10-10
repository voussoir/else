import math
import random
import time
from PIL import Image, ImageDraw

# Do not touch
smallest_x = None
largest_x = None
largest_y = None
label_depths = {}
##############

def quadratic_formula(a, b, c):
    # x = (-b +/- sqrt(b**2 - 4*a*c)) / 2a
    discriminant = (b ** 2) - (4 * a * c)
    discriminant = math.sqrt(discriminant)
    b *= -1
    possible = (b + discriminant, b - discriminant)
    possible = [x / (2*a) for x in possible]
    return possible

def time_to_known_distance(velocity, distance, acceleration):
    # distance = (0.5 * acceleration * (time**2)) + (velocity * time)
    # (0.5 * acceleration * (time**2)) + (velocity * time) - (distance) = 0
    possible = quadratic_formula(a=0.5 * acceleration, b=velocity, c=-distance)
    if min(possible) < 0:
        return max(possible)
    else:
        return min(possible)

def make_throw(starting_x, starting_y, starting_velocity, thrown_angle):
    global smallest_x
    global largest_x
    global largest_y
    upward = thrown_angle in range(1, 179, 1) or thrown_angle in range(-181, -359, -1)
    upward = -1 if upward else 1
    
    rads = math.radians(thrown_angle)
    sin = math.sin(rads)
    cos = math.cos(rads)
    tan = math.tan(rads)

    throw = {'angle': thrown_angle}
    throw['horizontal_component'] = starting_velocity * cos * -upward
    throw['vertical_component'] = starting_velocity * sin * upward
    #print(thrown_angle, starting_velocity, throw['horizontal_component'])
    throw['hang_time'] = time_to_known_distance(throw['vertical_component'], starting_y, acceleration=9.8)
    throw['distance'] = throw['hang_time'] * throw['horizontal_component']

    def parabola(x):
        # 100% credit goes to wikipedia authors
        # https://en.wikipedia.org/wiki/Projectile_motion#Parabolic_equation
        left = tan * x
        numerator = 9.8 * (x ** 2)
        denominator = 2 * (starting_velocity ** 2) * (math.cos(rads) ** 2)
        y = left - (numerator / denominator)
        return y

    throw['parabola'] = parabola
    throw['parabola_points'] = []
    #print(throw['vertical_component'], throw['hang_time'])

    y = 1
    x = starting_x
    backwards = (thrown_angle in range(90, 270)) or (thrown_angle in range(-90, -270, -1))
    while y > 0:
        y = throw['parabola'](x) + starting_y
        if y < 0:
            # To keep a smooth floor of 0, rescale the active x so that
            # it looks like it continues in the right direction underground.
            previous = throw['parabola_points'][-1]
            would_be_length = previous[1] - y
            length_scale = previous[1] / would_be_length
            x = previous[0] + ((x - previous[0]) * length_scale)
            y = 0

        if (smallest_x is None or x < smallest_x): smallest_x = math.floor(x)
        if (largest_x is None or x > largest_x): largest_x = math.ceil(x)
        if (largest_y is None or y > largest_y): largest_y = math.ceil(y)
        throw['parabola_points'].append([int(x), int(y)])
        if backwards:
            x -= PLOT_STEP_X
        else:
            x += PLOT_STEP_X
    return throw

def get_label_depth(x):
    xx = x + LABEL_PAD_HORIZONTAL
    for label in label_depths:
        #print(label)
        if any(v in range(*label) for v in (x, xx)):
            label_depths[label] += 1
            return label_depths[label]
    label_depths[(x, x+LABEL_PAD_HORIZONTAL)] = 0
    return 0







SMART_LABEL_STACK = True
LABEL_PAD_HORIZONTAL = 80
LABEL_PAD_VERTICAL = 15
PLOT_PAD_LEFT = 5

STARTING_X = 0
STARTING_Y = 700
STARTING_VELOCITY = 100
# Larger step = fewer data points = quicker and less memory
PLOT_STEP_X = 5

throws = []
angle_increment = 15
angles = [-1, 0, 1]
#angles = [x * angle_increment for x in range(int(90 / angle_increment))]
#angles += [x+90 for x in angles]
for thrown_angle in (angles):
    t = make_throw(STARTING_X, STARTING_Y, STARTING_VELOCITY, thrown_angle)
    if len(t['parabola_points']) < 2:
        continue
    throws.append(t)
throws.sort(key=lambda t: t['distance'], reverse=True)

# Add some padding on the right edge because labels
# are left-justified and start from the end of each arc
image_width = (largest_x-smallest_x)+LABEL_PAD_HORIZONTAL
image_height = largest_y+(LABEL_PAD_VERTICAL * len(throws))

i = Image.new('RGBA', (image_width, image_height))
d = ImageDraw.Draw(i)

for (index, t) in enumerate(throws):
    # lets avoid making any solid white lines.
    r = random.randint(0, 200)
    g = random.randint(0, 200)
    b = random.randint(0, 200)
    color = (r, g, b, 255)
    print(t['angle'], t['distance'])
    point_a = None
    for pointindex in range(len(t['parabola_points']) - 1):
        if point_a is None:
            point_a = t['parabola_points'][pointindex][:]
            point_a[0] = (round(point_a[0])) + abs(smallest_x) + PLOT_PAD_LEFT
            point_a[1] = (largest_y - round(point_a[1]))
        else:
            point_a = point_b
        point_b = t['parabola_points'][pointindex + 1][:]
        point_b[0] = (round(point_b[0])) + abs(smallest_x) + PLOT_PAD_LEFT
        point_b[1] = (largest_y - round(point_b[1]))
        try:
            # this ensures a solid, smooth line between each of the plotted points.
            d.line(point_a + point_b, fill=color)
        except:
            print('broken:', point)

    # Now that the loop has ended, point_b is the point on the horizon.
    label_x = point_b[0]
    if SMART_LABEL_STACK:
        label_y = largest_y + (LABEL_PAD_VERTICAL * get_label_depth(label_x))
    else:
        label_y = largest_y + (LABEL_PAD_VERTICAL * index)
    label_text = '%d degrees' % t['angle']
    d.text((label_x, label_y), label_text, fill=color)
d.line((0, largest_y, i.size[0], largest_y), fill=(0, 0, 0, 255))

if SMART_LABEL_STACK:
    # Earlier we judged the image height by how many tags we would have to add
    # if they were stacked all on top of each other. We can crop that excess now.
    deepest = max(x[1] for x in label_depths.items()) + 1
    required_image_height = largest_y + (LABEL_PAD_VERTICAL) * deepest
    i = i.crop((0, 0, image_width, required_image_height))
i.save('projectiles.png')
print('saved.')