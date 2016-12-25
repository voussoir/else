'''
Search for a target string within the lines of files.

For example:
fileswith.py *.py "import random"
'''

import argparse
import fnmatch
import glob
import re
import sys

from voussoirkit import safeprint
from voussoirkit import spinal


def fileswith(filepattern, terms, do_regex=False, do_glob=False):
    search_terms = [term.lower() for term in terms]

    def term_matches(text, term):
        return (
            (term in text) or
            (do_regex and re.search(term, text)) or
            (do_glob and fnmatch.fnmatch(text, term))
        )


    generator = spinal.walk_generator(depth_first=False, yield_directories=True)
    for filepath in generator:
        if not fnmatch.fnmatch(filepath.basename, filepattern):
            continue
        handle = open(filepath.absolute_path, 'r', encoding='utf-8')
        matches = []
        try:
            with handle:
                for (index, line) in enumerate(handle):
                    if all(term_matches(line, term) for term in terms):
                        line = '%d | %s' % (index, line.strip())
                        matches.append(line)
        except:
            pass
        if matches:
            print(filepath.absolute_path)
            safeprint.safeprint('\n'.join(matches))
            print()


def fileswith_argparse(args):
    return fileswith(
        filepattern=args.filepattern,
        terms=args.search_terms,
        do_glob=args.do_glob,
        do_regex=args.do_regex,
    )

def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('filepattern')
    parser.add_argument('search_terms', nargs='+', default=None)
    parser.add_argument('--regex', dest='do_regex', action='store_true')
    parser.add_argument('--glob', dest='do_glob', action='store_true')
    parser.set_defaults(func=fileswith_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])
