'''
When you run this file from the commandline given a single argument, all
of the files in the current working directory will be renamed in the format
{argument}_{count} where argument is your cmd input and count is a zero-padded
integer that counts each file in the folder.
'''

import argparse
import os
import random
import string
import re
import sys

from voussoirkit import pathclass
from voussoirkit import safeprint

IGNORE_EXTENSIONS = ['py', 'lnk', 'ini']


def natural_sorter(x):
    '''
    http://stackoverflow.com/a/11150413
    '''
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)] 
    return alphanum_key(x)

def fileprefix(
        prefix='',
        sep='_',
        ctime=False,
        autoyes=False,
    ):
    current_directory = pathclass.Path('.')

    prefix = prefix.strip()
    if prefix == ':':
        prefix = current_directory.basename + ' - '
    elif prefix != '':
        prefix += sep

    filepaths = current_directory.listdir()
    filepaths = [f for f in filepaths if f.is_file]
    filepaths = [f for f in filepaths if f.extension.lower() not in IGNORE_EXTENSIONS]

    try:
        pyfile = pathclass.Path(__file__)
        filepaths.remove(pyfile)
    except ValueError:
        pass

    # trust me on this.
    zeropadding = len(str(len(filepaths)))
    zeropadding = max(2, zeropadding)
    zeropadding = str(zeropadding)

    format = '{{prefix}}{{index:0{pad}d}}{{extension}}'.format(pad=zeropadding)

    if ctime:
        print('Sorting by time')
        filepaths.sort(key=lambda x: x.stat.st_ctime)
    else:
        print('Sorting by name')
        filepaths.sort(key=lambda x: natural_sorter(x.basename))

    rename_pairs = []

    for (index, filepath) in enumerate(filepaths):
        extension = filepath.extension
        if extension != '':
            extension = '.' + extension

        newname = format.format(prefix=prefix, index=index, extension=extension)
        if filepath.basename != newname:
            rename_pairs.append((filepath.absolute_path, newname))
    for (oldname, newname) in rename_pairs:
        message = f'{oldname} -> {newname}'
        safeprint.safeprint(message)

    ok = autoyes
    if not ok:
        print('Is this correct? y/n')
        ok = input('>').lower() in ('y', 'yes', 'yeehaw')

    if ok:
        for (oldname, newname) in rename_pairs:
            os.rename(oldname, newname)


def fileprefix_argparse(args):
    return fileprefix(
        prefix=args.prefix,
        sep=args.sep,
        ctime=args.ctime,
        autoyes=args.autoyes,
    )

def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('prefix', nargs='?', default='')
    parser.add_argument('--sep', dest='sep', default=' ', help='the character between the prefix and remainder')
    parser.add_argument('--ctime', dest='ctime', action='store_true', help='sort by ctime instead of filename')
    parser.add_argument('-y', '--yes', dest='autoyes', action='store_true', help='accept results without confirming')
    parser.set_defaults(func=fileprefix_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])
