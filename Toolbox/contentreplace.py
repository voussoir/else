import glob
import codecs
import sys
filenames = glob.glob(sys.argv[1])
replace_from = sys.argv[2]
replace_to = sys.argv[3]
try:
    automatic = sys.argv[4] == '-y'
except IndexError:
    automatic = False

replace_from = codecs.decode(replace_from, 'unicode_escape')
replace_to = codecs.decode(replace_to, 'unicode_escape')

def contentreplace(filename):
    f = open(filename, 'r', encoding='utf-8')
    with f:
        content = f.read()

    occurances = content.count(replace_from)
    if occurances == 0:
        print('No occurences')
        return

    print('Found %d occurences.' % occurances)
    if automatic:
        permission = 'y'
    else:
        permission = input('Replace? ')
    if permission.lower() not in ['y', 'yes']:
        exit()

    content = content.replace(replace_from, replace_to)

    f = open(filename, 'w', encoding='utf-8')
    with f:
        f.write(content)

for filename in filenames:
    contentreplace(filename)
