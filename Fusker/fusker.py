import collections
import itertools
import string
import sys

from voussoirkit import basenumber

class Landmark:
    def __init__(self, opener, closer, parser):
        self.opener = opener
        self.closer = closer
        self.parser = parser

def barsplit(chars):
    wordlist = []
    wordbuff = []
    def flush():
        if not wordbuff:
            return
        word = fusk_join(wordbuff)
        wordlist.append(word)
        wordbuff.clear()
    for item in chars:
        if item == '|':
            flush()
        else:
            wordbuff.append(item)
    flush()
    return wordlist

def fusk_join(items):
    form = ''
    fusks = []
    result = []
    for item in items:
        if isinstance(item, str):
            form += item
        else:
            form += '{}'
            fusks.append(item)
    product = itertools.product(*fusks)
    for group in product:
        f = form.format(*group)
        result.append(f)
    return result

def fusk_spinner(items):
    for item in items:
        if isinstance(item, str):
            yield item
        else:
            yield from item

def parse_spinner(characters):
    words = barsplit(characters)
    spinner = fusk_spinner(words)
    return spinner

def fusk_range(lo, hi, padto=0, base=10, lower=False):
    for x in range(lo, hi+1):
        x = basenumber.to_base(x, base)
        x = x.rjust(padto, '0')
        if lower:
            x = x.lower()
        yield x

def parse_range(characters):
    r = ''.join(characters)
    (lo, hi) = r.split('-')
    lo = lo.strip()
    hi = hi.strip()

    lowers = string.digits + string.ascii_lowercase
    uppers = string.digits + string.ascii_uppercase
    lohi = lo + hi
    lower = False
    if all(c in string.digits for c in lohi):
        base = 10
    elif all(c in lowers for c in lohi):
        lower = True
        base = 36
    elif all(c in uppers for c in lohi):
        base = 36
    else:
        base = 62

    if (not lo) or (not hi):
        raise ValueError('Invalid range', r)
    if len(lo) > 1 and lo.startswith('0'):
        padto = len(lo)
        if len(hi) != padto:
            raise ValueError('Inconsistent padding', lo, hi)
    else:
        padto = 0
    lo = basenumber.from_base(lo, base)
    hi = basenumber.from_base(hi, base)

    frange = fusk_range(lo, hi, padto=padto, base=base, lower=lower)
    return frange


landmarks = {
    '{': Landmark('{', '}', parse_spinner),
    '[': Landmark('[', ']', parse_range),
}

def fusker(fstring, landmark=None, depth=0):
    escaped = False
    result = []
    buff = []

    if isinstance(fstring, str):
        fstring = collections.deque(fstring)
    while fstring:
        character = fstring.popleft()
        if escaped:
            buff.append('\\' + character)
            escaped = False
        elif character == '\\':
            escaped = True
        elif landmark and character == landmark.closer:
            buff = [landmark.parser(buff)]
            break
        elif character in landmarks:
            subtotal = fusker(fstring, landmark=landmarks[character])
            buff.extend(subtotal)
        else:
            buff.append(character)
    if not landmark:
        buff = parse_spinner(buff)
    return buff
    return result

if __name__ == '__main__':
    pattern = sys.argv[1]
    fusk = fusker(pattern)
    for result in fusk:
        print(result)
