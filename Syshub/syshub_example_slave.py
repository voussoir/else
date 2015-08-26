'''
Notice how this file does not import syshub or know about it
in any way.
'''
import sys
def say_something():
    print('hello')

def input_something():
    print('prompt: ', end='')
    print(sys.stdin.readline())

def raise_something():
    raise ValueError