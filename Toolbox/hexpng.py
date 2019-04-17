import argparse
import os
import PIL.Image
import sys


def full_hex(h):
    h = h.replace('#', '')
    if len(h) in [3, 4]:
        h = ''.join([c * 2 for c in h])
    if len(h) == 6:
        h += 'ff'
    return h

def hex_to_rgb(h):
    rgb = [int(h[(2*i):(2*i)+2], 16) for i in range(len(h)//2)]
    return tuple(rgb)

def make_hexpng(h, width=1, height=1):
    h = full_hex(h)
    rgb = hex_to_rgb(h)
    filename = '%s.png' % h
    i = PIL.Image.new('RGBA', size=[width, height], color=rgb)
    print(filename)
    i.save(filename)

def hexpng_argparse(args):
    make_hexpng(args.hex_value, width=args.width, height=args.height)

def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('hex_value')
    parser.add_argument('--width', dest='width', type=int, default=1)
    parser.add_argument('--height', dest='height', type=int, default=1)
    parser.set_defaults(func=hexpng_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
