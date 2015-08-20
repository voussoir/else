import shlex

def add(x=None, y=None, *trash):
    try:
        return float(x) + float(y)
    except (ValueError, TypeError):
        return

def multiply(x=None, y=None, *trash):
    try:
        return float(x) * float(y)
    except (ValueError, TypeError):
        return

def exponent(x=None, y=None, *trash):
    try:
        return float(x) ** float(y)
    except (ValueError, TypeError):
        return

def join(text=None, spacer=None, *trash):
    if None in (text, spacer):
        return
    return spacer.join(text.split(' '))

def default_function(*trash):
    return 'Look what I found: ' + str(trash)


FUNCTION_MAP = {
    'add': add,
    'multiply': multiply,
    'exponent': exponent,
    'join': join
}

COMMAND_IDENTIFIERS = ['robot!']

SAMPLE_COMMENTS = [
'robot! add 1 2',
'I want robot! multiply 4 2 trash trash trash',
'robot! blank',
'robot!',
'robot!     add   7   19',
'robot!    exponent 7 2',
'robot! join "one two three" "-"',
'robot! add 10 10 robot! multiply 10 10 robot! exponent 10 10',
'robot! add 1 1\nrobot! multiply 1 1',
'   do ROBOT! add boom box',
'']

COMMAND_IDENTIFIERS = [c.lower() for c in COMMAND_IDENTIFIERS]

def handle_line(text):
    print('User said:', text)
    elements = shlex.split(text)
    print('Broken into:', elements)
    for element_index, element in enumerate(elements):
        if element.lower() not in COMMAND_IDENTIFIERS:
            continue

        arguments = elements[element_index:]
        assert arguments.pop(0).lower() in COMMAND_IDENTIFIERS
        #arguments = arguments[1:]

        # If the user has multiple command calls on one line
        # (Which is stupid but they might do it anyway)
        # Let's only process one at a time please.
        for argument_index, argument in enumerate(arguments):
            if argument.lower() in COMMAND_IDENTIFIERS:
                arguments = arguments[:argument_index]
                break

        print('Found command:', arguments)
        if len(arguments) == 0:
            print('Did nothing')
            continue

        function = FUNCTION_MAP.get(arguments[0], default_function)
        print('Using function:', function.__name__)

        if function is not default_function:
            # When using the default function, we want to pass in the
            # first word because it might be important
            # For other commands, we don't need it because add()
            # doesn't need the string "add" for anything.
            arguments = arguments[1:]
        result = function(*arguments)
        print('Output: %s' % result)

def handle_comment(comment):
    lines = comment.split('\n')
    for line in lines:
        handle_line(line)

for comment in SAMPLE_COMMENTS:
    print()
    handle_comment(comment)

'''
User said: robot! add 1 2
Broken into: ['robot!', 'add', '1', '2']
Found command: ['add', '1', '2']
Using function: add
Output: 3.0

User said: I want robot! multiply 4 2 trash trash trash
Broken into: ['I', 'want', 'robot!', 'multiply', '4', '2', 'trash', 'trash', 'trash']
Found command: ['multiply', '4', '2', 'trash', 'trash', 'trash']
Using function: multiply
Output: 8.0

User said: robot! blank
Broken into: ['robot!', 'blank']
Found command: ['blank']
Using function: default_function
Output: Look what I found: ('blank',)

User said: robot!
Broken into: ['robot!']
Found command: []
Did nothing

User said: robot!     add   7   19
Broken into: ['robot!', 'add', '7', '19']
Found command: ['add', '7', '19']
Using function: add
Output: 26.0

User said: robot!    exponent 7 2
Broken into: ['robot!', 'exponent', '7', '2']
Found command: ['exponent', '7', '2']
Using function: exponent
Output: 49.0

User said: robot! join "one two three" "-"
Broken into: ['robot!', 'join', 'one two three', '-']
Found command: ['join', 'one two three', '-']
Using function: join
Output: one-two-three

User said: robot! add 10 10 robot! multiply 10 10 robot! exponent 10 10
Broken into: ['robot!', 'add', '10', '10', 'robot!', 'multiply', '10', '10', 'robot!', 'exponent', '10', '10']
Found command: ['add', '10', '10']
Using function: add
Output: 20.0
Found command: ['multiply', '10', '10']
Using function: multiply
Output: 100.0
Found command: ['exponent', '10', '10']
Using function: exponent
Output: 10000000000.0

User said: robot! add 1 1
Broken into: ['robot!', 'add', '1', '1']
Found command: ['add', '1', '1']
Using function: add
Output: 2.0
User said: robot! multiply 1 1
Broken into: ['robot!', 'multiply', '1', '1']
Found command: ['multiply', '1', '1']
Using function: multiply
Output: 1.0

User said: ROBOT! add boom box
Broken into: ['ROBOT!', 'add', 'boom', 'box']
Found command: ['add', 'boom', 'box']
Using function: add
Output: None

User said: 
Broken into: []
'''