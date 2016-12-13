'''
Pull all of the files in nested directories into the current directory.
'''
import argparse
import os
import sys

from voussoirkit import spinal

def filepull(pull_from='.'):
    files = list(spinal.walk_generator(pull_from))
    cwd = os.getcwd()
    files = [f for f in files if os.path.split(f.absolute_path)[0] != cwd]

    if len(files) == 0:
        print('No files to move')
        return

    duplicate_count = {}
    for f in files:
        basename = f.basename
        duplicate_count.setdefault(basename, [])
        duplicate_count[basename].append(f.absolute_path)

    duplicates = ['\n'.join(sorted(copies)) for (basename, copies) in duplicate_count.items() if len(copies) > 1]
    duplicates = sorted(duplicates)
    if len(duplicates) > 0:
        raise Exception('duplicate names:\n' + '\n'.join(duplicates))

    for f in files:
        print(f.basename)

    print('Move %d files?' % len(files))
    if input('> ').lower() in ['y', 'yes']:
        for f in files:
            local = os.path.join('.', f.basename)
            os.rename(f.absolute_path, local)

def filepull_argparse(args):
    filepull(pull_from=args.pull_from)

def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('pull_from', nargs='?', default='.')
    parser.set_defaults(func=filepull_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])
