import random
import string
import time

import clipext

paragraph = '''
There once was a man from Peru
Who dreamed he was eating his shoe
He woke with a fright
In the middle of the night
To find that his dream had come true.
'''.strip()

inputs_mocked = 0
def mock_input():
    global inputs_mocked
    s = ''.join(random.choice(string.ascii_lowercase) for x in range(10))
    if inputs_mocked == 4:
        s += clipext.EOF
        inputs_mocked = 0
    inputs_mocked += 1
    return s

def mock_paste():
    lines = [''.join(random.choice(string.digits) for x in range(10)) for x in range(4)]
    lines = '\n'.join(lines)
    return lines

clipext.pyperclip.paste = mock_paste
clipext.input = mock_input

def test_splitted(text):
    print(repr(text))
    print('=')
    lines = clipext.resolve(text, split_lines=True)
    print(list(lines))
    print()

def test_unsplitted(text):
    print(repr(text))
    print('=')
    text = clipext.resolve(text, split_lines=False)
    print(repr(text))
    print()

test_splitted(paragraph)
test_splitted('!c')
test_splitted('!i')

print()

test_unsplitted(paragraph)
test_unsplitted('!c')
test_unsplitted('!i')

