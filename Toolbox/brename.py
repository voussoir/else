'''
Batch rename files by providing a string to be `eval`ed, using variable `x` as
the current filename.
Yes I know this is weird, but for certain tasks it's just too quick and easy to pass up.

For example:

Prefix all the files:
brename.py "'Test_' + x"

Keep the first word and extension:
brename.py "(x.split(' ')[0] + '.' + x.split('.')[-1]) if ' ' in x else x"
'''
import argparse
import os
import random
import re
import sys

from voussoirkit import safeprint

dot = '.'
quote = '"'
apostrophe = "'"
space = ' '

def brename(transformation, autoyes=False):
    old = os.listdir()
    new = []
    for (index, x) in enumerate(old):
        (noext, ext) = os.path.splitext(x)
        x = eval(transformation)
        new.append(x)
    pairs = []
    for (x, y) in zip(old, new):
        if x == y:
            continue
        pairs.append((x, y))

    if not loop(pairs, dry=True):
        print('Nothing to replace')
        return

    ok = autoyes
    if not ok:
        print('Is this correct? y/n')
        ok = input('>').lower() in ('y', 'yes', 'yeehaw')

    if ok:
        loop(pairs, dry=False)

def excise(s, mark_left, mark_right):
    '''
    Remove the text between the left and right landmarks, inclusive, returning
    the rest of the text.

    excise('What a wonderful day [soundtrack].mp3', ' [', ']') ->
    returns 'What a wonderful day.mp3'
    '''
    return s.split(mark_left)[0] + s.split(mark_right)[-1]

def longest_length(li):
    longest = 0
    for item in li:
        longest = max(longest, len(item))
    return longest

def loop(pairs, dry=False):
    has_content = False
    for (x, y) in pairs:
        if dry:
            line = '{old}\n{new}\n'
            line = line.format(old=x, new=y)
            #print(line.encode('utf-8'))
            safeprint.safeprint(line)
            has_content = True
        else:
            os.rename(x, y)
    return has_content

def title(text):
    (text, extension) = os.path.splitext(text)
    text = text.title()
    if ' ' in text:
        (first, rest) = text.split(' ', 1)
    else:
        (first, rest) = (text, '')
    rest = ' %s ' % rest
    for article in ['The', 'A', 'An', 'At', 'To', 'In', 'Of', 'From', 'And']:
        article = ' %s ' % article
        rest = rest.replace(article, article.lower())
    rest = rest.strip()
    if rest != '':
        rest = ' ' + rest
    text = first + rest + extension
    return text

def brename_argparse(args):
    brename(args.transformation, autoyes=args.autoyes)

def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('transformation', help='python command using x as variable name')
    parser.add_argument('-y', '--yes', dest='autoyes', action='store_true', help='accept results without confirming')
    parser.set_defaults(func=brename_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
