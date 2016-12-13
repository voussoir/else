import glob
import shutil
import os

PACKAGE = 'voussoirkit'
PATHS = [
'C:\\git\\else\\Bytestring\\bytestring.py',
'C:\\git\\else\\Clipext\\clipext.py',
'C:\\git\\else\\Downloady\\downloady.py',
'C:\\git\\else\\Pathclass\\pathclass.py',
'C:\\git\\else\\Ratelimiter\\ratelimiter.py',
'C:\\git\\else\\RateMeter\\ratemeter.py',
'C:\\git\\else\\SpinalTap\\spinal.py',
'C:\\git\\else\\WebstreamZip\\webstreamzip.py',
]

os.makedirs(PACKAGE, exist_ok=True)

for zipfile in glob.glob('*.zip'):
    os.remove(zipfile)

py_modules = []
local_paths = []

for path in PATHS:
    basename = os.path.basename(path)
    module_name = '{package}.{module}'.format(package=PACKAGE, module=basename.replace('.py', ''))
    py_modules.append(module_name)
    local_path = os.path.join(PACKAGE, basename)
    local_paths.append(local_path)
    try:
        os.link(path, local_path)
    except FileExistsError:
        pass

print('Creating setup.py')
setup_content = '''
import setuptools

setuptools.setup(
    author='voussoir',
    name='{package}',
    version='0.0.3',
    description='',
    py_modules=[{py_modules}],
)
'''

py_modules = ["'%s'" % x for x in py_modules]
py_modules = ', '.join(py_modules)
setup_content = setup_content.format(package=PACKAGE, py_modules=py_modules)

setup_file = open('setup.py', 'w')
setup_file.write(setup_content)
setup_file.close()

print('Executing setup.py')
os.system('python setup.py sdist')

print('Moving zip file')
zips = glob.glob('dist\\*.zip')
for zip_filename in zips:
    new_zip = os.path.basename(zip_filename)
    new_zip = os.path.abspath(new_zip)
    shutil.move(zip_filename, new_zip)

print('Deleting temp')
shutil.rmtree('dist')
shutil.rmtree(PACKAGE)
shutil.rmtree(glob.glob('*.egg-info')[0])
os.remove('setup.py')
os.rename(glob.glob('*.zip')[0], 'voussoirkit.zip')
