print('importing')
import argparse
import fnmatch
import itertools
import os
import re
import stat
import sys
import traceback

from voussoirkit import clipext
from voussoirkit import expressionmatch
from voussoirkit import pathclass
from voussoirkit import safeprint
from voussoirkit import spinal

# Thanks georg
# http://stackoverflow.com/a/13443424
STDIN_MODE = os.fstat(sys.stdin.fileno()).st_mode
if stat.S_ISFIFO(STDIN_MODE):
    STDIN_MODE = 'pipe'
else:
    STDIN_MODE = 'terminal'

def all_terms_match(search_text, terms, match_function):
    matches = (
        (not terms['yes_all'] or all(match_function(search_text, term) for term in terms['yes_all'])) and
        (not terms['yes_any'] or any(match_function(search_text, term) for term in terms['yes_any'])) and
        (not terms['not_all'] or not all(match_function(search_text, term) for term in terms['not_all'])) and
        (not terms['not_any'] or not any(match_function(search_text, term) for term in terms['not_any']))
    )
    return matches

def search(
        *,
        yes_all=None,
        yes_any=None,
        not_all=None,
        not_any=None,
        case_sensitive=False,
        content_args=None,
        do_expression=False,
        do_glob=False,
        do_regex=False,
        line_numbers=False,
        local_only=False,
        text=None,
    ):
    if text is None:
        print('starting search')
    terms = {
        'yes_all': yes_all,
        'yes_any': yes_any,
        'not_all': not_all,
        'not_any': not_any
    }
    terms = {k: ([v] if isinstance(v, str) else v or []) for (k, v) in terms.items()}
    #print(terms, content_args)

    if all(v == [] for v in terms.values()) and not content_args:
        raise ValueError('No terms supplied')

    def term_matches(line, term):
        if not case_sensitive:
            line = line.lower()

        if do_expression:
            return term.evaluate(line)

        return (
            (term in line) or
            (do_regex and re.search(term, line)) or
            (do_glob and fnmatch.fnmatch(line, term))
        )

    if do_expression:
        # The value still needs to be a list so the upcoming any() / all()
        # receives an iterable as it expects. It just happens to be 1 tree.
        trees = {}
        for (key, value) in terms.items():
            if value == []:
                trees[key] = []
                continue
            tree = ' '.join(value)
            tree = expressionmatch.ExpressionTree.parse(tree)
            if not case_sensitive:
                tree.map(str.lower)
            trees[key] = [tree]
        terms = trees

    elif not case_sensitive:
        terms = {k: [x.lower() for x in v] for (k, v) in terms.items()}

    if text is None:
        search_objects = spinal.walk_generator(
            depth_first=False,
            recurse=not local_only,
            yield_directories=True,
        )
    else:
        search_objects = text.splitlines()

    for (index, search_object) in enumerate(search_objects):
        if index % 10 == 0:
            #print(index, end='\r', flush=True)
            pass
        if isinstance(search_object, pathclass.Path):
            search_text = search_object.basename
            result_text = search_object.absolute_path
        else:
            search_text = search_object
            result_text = search_object
        if line_numbers:
            result_text = '%4d | %s' % (index+1, result_text)

        if all_terms_match(search_text, terms, term_matches):
            if not content_args:
                yield result_text
            else:
                filepath = pathclass.Path(search_object)
                if not filepath.is_file:
                    continue
                try:
                    with open(filepath.absolute_path, 'r') as handle:
                        text = handle.read()
                except UnicodeDecodeError:
                    try:
                        with open(filepath.absolute_path, 'r', encoding='utf-8') as handle:
                            text = handle.read()
                    except UnicodeDecodeError:
                        #safeprint.safeprint(filepath.absolute_path)
                        #traceback.print_exc()
                        continue
                except Exception:
                    safeprint.safeprint(filepath.absolute_path)
                    traceback.print_exc()
                    continue

                content_args['text'] = text
                content_args['line_numbers'] = True
                results = search(**content_args)
                results = list(results)
                if not results:
                    continue

                yield filepath.absolute_path
                yield from results
                yield ''

def argparse_to_dict(args):
    text = args.text
    if text is not None:
        text = clipext.resolve(text)
    elif STDIN_MODE == 'pipe':
        text = clipext.resolve('!i')

    if hasattr(args, 'content_args') and args.content_args is not None:
        content_args = argparse_to_dict(args.content_args)
    else:
        content_args = None

    return {
        'yes_all': args.yes_all,
        'yes_any': args.yes_any,
        'not_all': args.not_all,
        'not_any': args.not_any,
        'case_sensitive': args.case_sensitive,
        'content_args': content_args,
        'do_expression': args.do_expression,
        'do_glob': args.do_glob,
        'do_regex': args.do_regex,
        'local_only': args.local_only,
        'line_numbers': args.line_numbers,
        'text': text,
    }

def search_argparse(args):
    generator = search(**argparse_to_dict(args))
    result_count = 0
    for result in generator:
        safeprint.safeprint(result)
        result_count += 1
    if args.show_count:
        print('%d items.' % result_count)

def main(argv):
    parser = argparse.ArgumentParser()

    # The padding is inserted to guarantee that --content is not the first
    # argument. Because if it were, we wouldn't know if we have
    # [pre, '--content'] or ['--content', post], etc. and I don't want to
    # actually check the values.
    argv.insert(0, 'padding')
    grouper = itertools.groupby(argv, lambda x: x == '--content')
    halves = [list(group) for (key, group) in grouper]
    # halves looks like [pre, '--content', post]
    name_args = halves[0]
    # Pop the padding
    name_args.pop(0)
    content_args = [item for chunk in halves[2:] for item in chunk]

    parser.add_argument('yes_all', nargs='*', default=None)
    parser.add_argument('--all', dest='yes_all', nargs='+')
    parser.add_argument('--any', dest='yes_any', nargs='+')
    parser.add_argument('--not_all', dest='not_all', nargs='+')
    parser.add_argument('--not_any', dest='not_any', nargs='+')

    parser.add_argument('--case', dest='case_sensitive', action='store_true')
    parser.add_argument('--content', dest='do_content', action='store_true')
    parser.add_argument('--count', dest='show_count', action='store_true')
    parser.add_argument('--expression', dest='do_expression', action='store_true')
    parser.add_argument('--glob', dest='do_glob', action='store_true')
    parser.add_argument('--line_numbers', dest='line_numbers', action='store_true')
    parser.add_argument('--local', dest='local_only', action='store_true')
    parser.add_argument('--regex', dest='do_regex', action='store_true')
    parser.add_argument('--text', dest='text', default=None)
    parser.set_defaults(func=search_argparse)

    args = parser.parse_args(name_args)
    if content_args:
        args.content_args = parser.parse_args(content_args)
    else:
        args.content_args = None
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])
