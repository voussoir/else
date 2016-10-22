import os
from setuptools import setup

def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()

setup(
    author='Ethan Dalool (voussoir)',
    name='bytestring',
    version='0.0.1',
    description='Convert integers into IEC binary strings and back',
    py_modules=['bytestring', 'bytestring_test'],
    entry_points='''
        [console_scripts]
        bytestring=bytestring:main
    ''',
)