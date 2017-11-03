from PIL import Image
import sys

filename = sys.argv[1]
try:
    newname = sys.argv[4]
except IndexError:
    newname = None
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
print(i.size, new_x, new_y)
i = i.resize( (new_x, new_y) )
if newname is None:
    if '.' in filename:
        suffix = '_{width}x{height}'.format(width=new_x, height=new_y)
        newname = filename.replace('.', suffix + '.')
    else:
        newname += suffix
i.save(newname, quality=100)
