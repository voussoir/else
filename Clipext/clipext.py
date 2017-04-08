import pyperclip

CLIPBOARD_STRINGS = ['!c', '!clip', '!clipboard']
INPUT_STRINGS = ['!i', '!in', '!input', '!stdin']
EOF = '\x1a'

def _input_lines():
    userinput = []
    while True:
        try:
            additional = input()
        except EOFError:
            # If you enter nothing but ctrl-z
            additional = EOF
        else:
            userinput.append(additional)

        additional = additional.split(EOF)
        has_eof = len(additional) > 1
        additional = additional[0]

        yield additional

        if has_eof:
            break

def multi_line_input(split_lines=False):
    generator = _input_lines()
    if split_lines:
        return generator
    else:
        return '\n'.join(generator)

def resolve(arg, split_lines=False):
    lowered = arg.lower()
    if lowered in INPUT_STRINGS:
        return multi_line_input(split_lines=split_lines)
    elif lowered in CLIPBOARD_STRINGS:
        text = pyperclip.paste()
    else:
        text = arg

    if split_lines:
        lines = text.splitlines()
        return lines
    else:
        return text
