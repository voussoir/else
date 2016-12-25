import argparse
import fnmatch
import os
import re
import sys

from voussoirkit import safeprint
from voussoirkit import spinal

def search(terms, match_any=False, do_regex=False, do_glob=False):
    search_terms = [term.lower() for term in terms]

    def term_matches(text, term):
        return (
            (term in text) or
            (do_regex and re.search(term, text)) or
            (do_glob and fnmatch.fnmatch(text, term))
        )

    anyall = any if match_any else all

    generator = spinal.walk_generator(depth_first=False, yield_directories=True)
    for filepath in generator:
        basename = filepath.basename.lower()
        if anyall(term_matches(basename, term) for term in search_terms):
            safeprint.safeprint(filepath.absolute_path)


def search_argparse(args):
    return search(
        terms=args.search_terms,
        do_glob=args.do_glob,
        do_regex=args.do_regex,
        match_any=args.match_any,
    )

def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('search_terms', nargs='+', default=None)
    parser.add_argument('--any', dest='match_any', action='store_true')
    parser.add_argument('--regex', dest='do_regex', action='store_true')
    parser.add_argument('--glob', dest='do_glob', action='store_true')
    parser.set_defaults(func=search_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])
