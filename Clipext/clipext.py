import pyperclip

CLIPBOARD_STRINGS = ['!c', '!clip', '!clipboard']
INPUT_STRINGS = ['!i', '!in', '!input', '!stdin']
EOF = '\x1a'

def multi_line_input():
    userinput = []
    while True:
        try:
            additional = input()
        except EOFError:
            # If you enter nothing but ctrl-z
            additional = EOF

        userinput.append(additional)

        if EOF in additional:
            break

    userinput = '\n'.join(userinput)
    userinput = userinput.split(EOF)[0]
    return userinput.strip()

def resolve(arg):
    lowered = arg.lower()
    if lowered in CLIPBOARD_STRINGS:
        return pyperclip.paste()
    if lowered in INPUT_STRINGS:
        return multi_line_input()
    return arg
