import argparse
import codecs
import glob
import sys

def contentreplace(filename, replace_from, replace_to, autoyes=False):
    f = open(filename, 'r', encoding='utf-8')
    with f:
        content = f.read()

    occurances = content.count(replace_from)

    print(f'{filename}: Found {occurances} occurences.')
    if occurances == 0:
        return

    permission = autoyes or (input('Replace? ').lower() in ('y', 'yes'))
    if not permission:
        return

    content = content.replace(replace_from, replace_to)

    f = open(filename, 'w', encoding='utf-8')
    with f:
        f.write(content)

def contentreplace_argparse(args):
    filenames = glob.glob(args.filename_glob)
    for filename in filenames:
        contentreplace(
            filename,
            codecs.decode(args.replace_from, 'unicode_escape'),
            codecs.decode(args.replace_to, 'unicode_escape'),
            autoyes=args.autoyes,
        )

def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('filename_glob')
    parser.add_argument('replace_from')
    parser.add_argument('replace_to')
    parser.add_argument('-y', '--yes', dest='autoyes', action='store_true', help='accept results without confirming')
    parser.set_defaults(func=contentreplace_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
