'''
Notice how this file does not import syshub or know about it
in any way.
'''
import sys
def say_something():
    print('hello')

def input_something():
    print('prompt: ', end='')
    b = sys.stdin.readline()
    print(b)

def raise_something():
    print(sys.excepthook)
    raise ValueError