import PIL.Image

KERNEL_GAUSSIAN_BLUR = [
    [1, 2, 1],
    [2, 3, 2],
    [1, 2, 1],
]
KERNEL_EDGE_DETECTION_H = [
    [-2, 0, 2],
    [-2, 0, 2],
    [-2, 0, 2],
]
KERNEL_EDGE_DETECTION_V = [
    [-2, -2, 2],
    [0, 0, 0],
    [2, 2, 2],
]
def index_to_xy(index, width):
    (y, x) = divmod(index, width)
    return (x, y)

def xy_to_index(x, y, width):
    return (y * width) + x

def add(image_a, image_b):
    pixels_a = image_a.getdata()
    pixels_b = image_b.getdata()
    assert len(pixels_a) == len(pixels_b)
    pixels_c = [a + b for (a, b) in zip(pixels_a, pixels_b)]
    new_image = PIL.Image.new('L', (image_a.size))
    new_image.putdata(pixels_c, 1, 0)
    return new_image

def apply_filter(old_image, kernel):
    kernel_height = len(kernel)
    kernel_width = len(kernel[0])
    if (kernel_height % 2 != 1) or (kernel_width % 2 != 1):
        raise ValueError('Kernel is not of odd size')

    if any(len(segment) != kernel_width for segment in kernel):
        raise ValueError('Kernel is of inconsistent size')

    kernel_center = (kernel_width // 2, kernel_height // 2)
    flat_kernel = list(flatten_list(kernel))
    lower = min(flat_kernel)
    lower = min(0, lower * 255)
    upper = max(flat_kernel)
    upper = max(255, upper * 255)
    print(lower, upper)

    (image_width, image_height) = old_image.size
    old_pixels = old_image.getdata()
    new_pixels = list(old_image.getdata())

    for (index, old_pixel) in enumerate(old_pixels):
        operation_sum = 0
        operation_denominator = 0
        (x, y) = index_to_xy(index, image_width)
        #print(x, y, index)
        for (kernel_y, kernel_row) in enumerate(kernel):
            #print(kernel_row)
            subject_y = y - (kernel_center[1] - kernel_y)
            if subject_y < 0 or subject_y >= image_height:
                continue
            for (kernel_x, kernel_entry) in enumerate(kernel_row):
                if kernel_entry == 0:
                    continue
                subject_x = x - (kernel_center[0] - kernel_x)
                if subject_x < 0 or subject_x >= image_width:
                    continue
                subject = old_pixels[xy_to_index(subject_x, subject_y, image_width)]
                #print(x, y, subject_x, subject_y, kernel_entry, subject)
                operation_sum += kernel_entry * subject
                operation_denominator += kernel_entry

        operation_denominator = max(1, operation_denominator)
        operation_avg = abs(operation_sum / operation_denominator)
        #n_operation_avg = int(map_range(operation_avg, lower, upper, 0, 255))
        if index % 4096 == 0:
            #print(x, y, operation_sum, operation_denominator, operation_avg)
            print(y, '/', image_height)
        new_pixels[index] = operation_avg

    #print(new_pixels)
    new_image = PIL.Image.new('L', (old_image.size))
    new_image.putdata(new_pixels, 1, 0)
    #print(new_pixels)
    #print(list(new_image.getdata()))
    return new_image

def flatten_list(li):
    for element in li:
        if hasattr(element, '__iter__'):
            yield from flatten_list(element)
        else:
            yield element

def map_range(x, old_low, old_high, new_low, new_high):
    '''
    Given a number x in range [old_low, old_high], return corresponding
    number in range [new_low, new_high].
    '''
    if x > old_high or x < old_low:
        raise ValueError('%d not in range [%d..%d]' % (x, old_low, old_high))
    percentage = (x - old_low) / (old_high - old_low)
    y = (percentage * (new_high - new_low)) + new_low
    return y

if __name__ == '__main__':
    i = PIL.Image.open('icon.jpg')
    i = i.convert('L')
    i = apply_filter(i, KERNEL_GAUSSIAN_BLUR)
    a = apply_filter(i, KERNEL_EDGE_DETECTION_H)
    b = apply_filter(i, KERNEL_EDGE_DETECTION_V)
    i = add(a, b)
    i.save('icon.png')