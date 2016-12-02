import os
import sys


def brename(transformation):
    old = os.listdir()
    if 're.' in transformation:
        import re
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