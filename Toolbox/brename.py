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
import os
import random
import re
import sys


def brename(transformation):
    old = os.listdir()
    new = [eval(transformation) for x in old]
    pairs = []
    for (x, y) in zip(old, new):
        if x == y:
            continue
        pairs.append((x, y))
    if not loop(pairs, dry=True):
        print('Nothing to replace')
        return
    print('Is this correct? y/n')
    if input('>').lower() not in ('y', 'yes', 'yeehaw'):
        return
    loop(pairs, dry=False)

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
            print(line)
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

if __name__ == '__main__':
    transformation = sys.argv[1]
    brename(transformation)
