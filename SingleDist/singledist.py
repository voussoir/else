import glob
import os
import shutil
import sys

filename = sys.argv[1]
package_name = filename.split('.py')[0]

print('Creating setup.py')
setup_content = '''
import setuptools

setuptools.setup(
    author='voussoir',
    name='{package_name}',
    version='0.0.1',
    description='',
    py_modules=['{package_name}'],
)
'''

setup_content = setup_content.format(package_name=package_name)

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
shutil.rmtree(glob.glob('*.egg-info')[0])
os.remove('setup.py')