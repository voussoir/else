'''
Create the file, or update the last modified timestamp.
'''
import glob
import os
import sys


glob_patterns = sys.argv[1:]
for glob_pattern in glob_patterns:
    filenames = glob.glob(glob_pattern)
    if len(filenames) == 0:
        print(glob_pattern)
        open(glob_pattern, 'a').close()
    else:
        for filename in filenames:
            print(filename)
            os.utime(filename)
