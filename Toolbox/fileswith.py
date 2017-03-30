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


def fileswith(
        filepattern,
        terms,
        case_sensitive=False,
        do_regex=False,
        do_glob=False,
        inverse=False,
        match_any=False,
    ):

    if not case_sensitive:
        terms = [term.lower() for term in terms]

    def term_matches(text, term):
        return (
            (term in text) or
            (do_regex and re.search(term, text)) or
            (do_glob and fnmatch.fnmatch(text, term))
        )

    anyall = any if match_any else all


    generator = spinal.walk_generator(depth_first=False, yield_directories=True)
    for filepath in generator:
        if not fnmatch.fnmatch(filepath.basename, filepattern):
            continue
        if not filepath.is_file:
            continue
        handle = open(filepath.absolute_path, 'r', encoding='utf-8')
        matches = []
        try:
            with handle:
                for (index, line) in enumerate(handle):
                    if not case_sensitive:
                        compare_line = line.lower()
                    else:
                        compare_line = line
                    if inverse ^ anyall(term_matches(compare_line, term) for term in terms):
                        line = '%d | %s' % (index+1, line.strip())
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
        case_sensitive=args.case_sensitive,
        do_glob=args.do_glob,
        do_regex=args.do_regex,
        inverse=args.inverse,
        match_any=args.match_any,
    )

def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('filepattern')
    parser.add_argument('search_terms', nargs='+', default=None)
    parser.add_argument('--any', dest='match_any', action='store_true')
    parser.add_argument('--case', dest='case_sensitive', action='store_true')
    parser.add_argument('--regex', dest='do_regex', action='store_true')
    parser.add_argument('--glob', dest='do_glob', action='store_true')
    parser.add_argument('--inverse', dest='inverse', action='store_true')
    parser.set_defaults(func=fileswith_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])
