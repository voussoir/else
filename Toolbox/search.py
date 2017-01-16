import argparse
import fnmatch
import os
import re
import sys

from voussoirkit import safeprint
from voussoirkit import spinal

def search(
        terms,
        *,
        case_sensitive=False,
        do_regex=False,
        do_glob=False,
        local_only=False,
        match_any=False,
    ):
    def term_matches(text, term):
        return (
            (term in text) or
            (do_regex and re.search(term, text)) or
            (do_glob and fnmatch.fnmatch(text, term))
        )

    if case_sensitive:
        search_terms = terms
    else:
        search_terms = [term.lower() for term in terms]

    anyall = any if match_any else all

    generator = spinal.walk_generator(
        depth_first=False,
        recurse=not local_only,
        yield_directories=True,
    )
    for filepath in generator:
        basename = filepath.basename
        if not case_sensitive:
            basename = basename.lower()

        if anyall(term_matches(basename, term) for term in search_terms):
            safeprint.safeprint(filepath.absolute_path)


def search_argparse(args):
    return search(
        terms=args.search_terms,
        case_sensitive=args.case_sensitive,
        do_glob=args.do_glob,
        do_regex=args.do_regex,
        local_only=args.local_only,
        match_any=args.match_any,
    )

def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('search_terms', nargs='+', default=None)
    parser.add_argument('--any', dest='match_any', action='store_true')
    parser.add_argument('--regex', dest='do_regex', action='store_true')
    parser.add_argument('--glob', dest='do_glob', action='store_true')
    parser.add_argument('--case', dest='case_sensitive', action='store_true')
    parser.add_argument('--local', dest='local_only', action='store_true')
    parser.set_defaults(func=search_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])
