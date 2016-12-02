import argparse
import sys

from voussoirkit import bytestring

def hms_s(hms):
    hms = hms.split(':')
    seconds = 0
    if len(hms) == 3:
        seconds += int(hms[0])*3600
        hms.pop(0)
    if len(hms) == 2:
        seconds += int(hms[0])*60
        hms.pop(0)
    if len(hms) == 1:
        seconds += int(hms[0])
    return seconds

def s_hms(s):
    (minutes, seconds) = divmod(s, 60)
    (hours, minutes) = divmod(minutes, 60)
    return '%02d:%02d:%02d' % (hours, minutes, seconds)

def kbps(time=None, size=None, kbps=None):
    if [time, size, kbps].count(None) != 1:
        raise ValueError('Incorrect number of unknowns')

    if size is None:
        seconds = hms_s(time)
        kibs = int(kbps) / 8
        size = kibs * 1024
        size *= seconds
        out = bytestring.bytestring(size)
        return out

    if time is None:
        size = bytestring.parsebytes(size)
        kilobits = size / 128
        time = kilobits / int(kbps)
        return s_hms(time)

    if kbps is None:
        seconds = hms_s(time)
        size = bytestring.parsebytes(size)
        kibs = size / 1024
        kilobits = kibs * 8
        kbps = kilobits / seconds
        return int(kbps)

def example_argparse(args):
    print(kbps(time=args.time, size=args.size, kbps=args.kbps))

def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('-t', '--time', dest='time', default=None)
    parser.add_argument('-s', '--size', dest='size', default=None)
    parser.add_argument('-k', '--kbps', dest='kbps', default=None)
    parser.set_defaults(func=example_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])
