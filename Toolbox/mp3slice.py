'''
This script cuts an audio file into multiple files when you provide the
timestamps and titles for each.

> mp3slice bigfile.mp3 00:00-01:00 part1.mp3 01:00-02:00 part2.mp3
'''

import argparse
import os
import sys

from voussoirkit import bytestring


def parse_rules(lines):
    rules = []
    for (times, title) in lines[::-1]:
        rule = {'title': title}
        (start, end) = hyphen_range(times)
        if start is None:
            raise ValueError('Null start')
        rule['start'] = start
        if end is None and len(rules) > 0:
            end = rules[-1]['start']
        rule['end'] = end
        rules.append(rule)
    rules.sort(key=lambda x: x.get('start'))
    return rules

def read_rulefile(filename):
    text = None
    for encoding in [None, 'utf-8']:
        try:
            with open(filename, 'r', encoding=encoding) as handle:
                text = handle.read()
                break
        except UnicodeError:
            pass
    else:
        raise UnicodeError()

    lines = [l.strip() for l in text.strip().splitlines()]
    lines = [l for l in lines if l]
    rules = [l.split(maxsplit=1) for l in lines]
    return parse_rules(rules)

def chunk_sequence(sequence, chunk_length, allow_incomplete=True):
    '''
    Given a sequence, divide it into sequences of length `chunk_length`.

    allow_incomplete:
        If True, allow the final chunk to be shorter if the
        given sequence is not an exact multiple of `chunk_length`.
        If False, the incomplete chunk will be discarded.
    '''
    (complete, leftover) = divmod(len(sequence), chunk_length)
    if not allow_incomplete:
        leftover = 0

    chunk_count = complete + min(leftover, 1)

    chunks = []
    for x in range(chunk_count):
        left = chunk_length * x
        right = left + chunk_length
        chunks.append(sequence[left:right])

    return chunks

def hyphen_range(s):
    '''
    Given a string like '1-3', return numbers (1, 3) representing lower
    and upper bounds.

    Supports bytestring.parsebytes and hh:mm:ss format, for example
    '1k-2k', '10:00-20:00', '4gib-'
    '''
    s = s.strip()
    s = s.replace(' ', '')
    if not s:
        return (None, None)
    parts = s.split('-')
    parts = [part.strip() or None for part in parts]
    if len(parts) == 1:
        low = parts[0]
        high = None
    elif len(parts) == 2:
        (low, high) = parts
    else:
        raise ValueError('Too many hyphens')

    low = _unitconvert(low)
    high = _unitconvert(high)
    if low is not None and high is not None and low > high:
        raise exceptions.OutOfOrder(range=s, min=low, max=high)
    return low, high

def hms_to_seconds(hms):
    '''
    Convert hh:mm:ss string to an integer seconds.
    '''
    hms = hms.split(':')
    seconds = 0
    if len(hms) == 3:
        seconds += int(hms[0])*3600
        hms.pop(0)
    if len(hms) == 2:
        seconds += int(hms[0])*60
        hms.pop(0)
    if len(hms) == 1:
        seconds += float(hms[0])
    return seconds

def _unitconvert(value):
    '''
    When parsing hyphenated ranges, this function is used to convert
    strings like "1k" to 1024 and "1:00" to 60.
    '''
    if value is None:
        return None
    if ':' in value:
        return hms_to_seconds(value)
    elif all(c in '0123456789.' for c in value):
        return float(value)
    else:
        return bytestring.parsebytes(value)

def example_argparse(args):
    if len(args.rules) == 1 and os.path.isfile(args.rules[0]):
        rules = read_rulefile(args.rules[0])
    else:
        rules = args.rules
        rules = chunk_sequence(rules, 2)
        if len(rules[-1]) != 2:
            raise ValueError('Odd-number parameters')
        rules = parse_rules(rules)

    extension = os.path.splitext(args.input_filename)[1]
    outputters = []
    for rule in rules:
        outputter = []
        if not rule['title'].endswith(extension):
            rule['title'] += extension
        outputter.append('-ss')
        outputter.append(str(rule['start']))
        if rule['end'] is not None:
            outputter.append('-to')
            outputter.append(str(rule['end']))
        outputter.append(' -c copy')
        outputter.append('"%s"' % rule['title'])
        print(outputter)
        outputter = ' '.join(outputter)
        outputters.append(outputter)
    outputters = ' '.join(outputters)
    command = 'ffmpeg -i "%s" %s' % (args.input_filename, outputters)
    print(command)
    os.system(command)


def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('input_filename')
    parser.add_argument('rules', nargs='+', default=None)
    parser.set_defaults(func=example_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])
