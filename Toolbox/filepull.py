import os
import sys

from voussoirkit import spinal

def main():
    files = list(spinal.walk_generator())
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

if __name__ == '__main__':
    main()