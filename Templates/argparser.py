## SINGLE

import argparse
import sys

def example_argparse(args):
    print(args)

def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('required_positional')
    parser.add_argument('optional_positional', nargs='?', default=None)
    parser.add_argument('-k', '--kwarg', dest='kwarg', default=None)
    parser.add_argument('-b', '--boolkwarg', dest='boolkwarg', action='store_true')
    parser.set_defaults(func=example_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])

###############################################################################
###############################################################################

## MULTIPLE

import argparse
import sys

def example_argparse(args):
    print(args)

def main(argv):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    p_example = subparsers.add_parser('example1')
    p_example.add_argument('required_positional')
    p_example.add_argument('optional_positional', nargs='?', default=None)
    p_example.add_argument('-k', '--kwarg', dest='kwarg', default=None)
    p_example.add_argument('-b', '--boolkwarg', dest='boolkwarg', action='store_true')
    p_example.set_defaults(func=example_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])