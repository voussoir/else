import pyperclip
import sys


if len(sys.argv) > 1:
    from voussoirkit import clipext
    stuff = clipext.resolve(sys.argv[1])
    pyperclip.copy(stuff)
else:
    text = pyperclip.paste()
    text = text.replace('\r', '')
    print(text)
