import argparse
import fnmatch
import os
import re
import sys

from voussoirkit import clipext
from voussoirkit import expressionmatch
from voussoirkit import safeprint
from voussoirkit import spinal

def search(
        terms,
        *,
        case_sensitive=False,
        do_expression=False,
        do_glob=False,
        do_regex=False,
        inverse=False,
        local_only=False,
        match_any=False,
        text=None,
    ):
    def term_matches(text, term):
        if not case_sensitive:
            text = text.lower()

        return (
            (term in text) or
            (do_regex and re.search(term, text)) or
            (do_glob and fnmatch.fnmatch(text, term)) or
            (do_expression and term.evaluate(text))
        )

    if not case_sensitive:
        terms = [term.lower() for term in terms]

    if do_expression:
        terms = ' '.join(terms)
        terms = [expressionmatch.ExpressionTree.parse(terms)]

    anyall = any if match_any else all

    if text is None:
        walk = spinal.walk_generator(
            depth_first=False,
            recurse=not local_only,
            yield_directories=True,
        )
        lines = ((filepath.basename, filepath.absolute_path) for filepath in walk)
    else:
        lines = text.splitlines()

    for line in lines:
        if isinstance(line, tuple):
            (line, printout) = line
        else:
            printout = line
        matches = anyall(term_matches(line, term) for term in terms)
        if matches ^ inverse:
            safeprint.safeprint(printout)


def search_argparse(args):
    return search(
        terms=args.search_terms,
        case_sensitive=args.case_sensitive,
        do_glob=args.do_glob,
        do_regex=args.do_regex,
        inverse=args.inverse,
        local_only=args.local_only,
        match_any=args.match_any,
        text=args.text if args.text is None else clipext.resolve(args.text),
    )

def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('search_terms', nargs='+', default=None)
    parser.add_argument('--any', dest='match_any', action='store_true')
    parser.add_argument('--case', dest='case_sensitive', action='store_true')
    parser.add_argument('--regex', dest='do_regex', action='store_true')
    parser.add_argument('--glob', dest='do_glob', action='store_true')
    parser.add_argument('--expression', dest='do_expression', action='store_true')
    parser.add_argument('--local', dest='local_only', action='store_true')
    parser.add_argument('--inverse', dest='inverse', action='store_true')
    parser.add_argument('--text', dest='text', default=None)
    parser.set_defaults(func=search_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])
