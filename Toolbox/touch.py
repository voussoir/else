'''
Create the file, or update the last modified timestamp.
'''
import glob
import os
import sys

def touch(glob_pattern):
    filenames = glob.glob(glob_pattern)
    if len(filenames) == 0:
        print(glob_pattern.encode('ascii', 'replace').decode())
        open(glob_pattern, 'a').close()
    else:
        for filename in filenames:
            print(filename.encode('ascii', 'replace').decode())
            os.utime(filename)

if __name__ == '__main__':
    glob_patterns = sys.argv[1:]
    for glob_pattern in glob_patterns:
        touch(glob_pattern)
