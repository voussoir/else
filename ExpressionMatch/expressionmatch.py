import time
ESCAPE_SEQUENCES = {
    '\\': '\\',
    '"': '"',
}

BINARY_OPERATORS = {'AND', 'OR', 'XOR'}
UNARY_OPERATORS = {'NOT'}
PRECEDENCE = ['NOT', 'AND', 'XOR', 'OR']
OPERATORS = BINARY_OPERATORS | UNARY_OPERATORS

DEFAULT_MATCH_FUNCTION = str.__contains__

MESSAGE_WRITE_YOUR_OWN_MATCHER = '''
The default match function is {function}.
Consider passing your own `match_function`, which accepts two
positional arguments:
1. The object being tested.
2. The Expression token, a string.
'''.strip()

def func_and(values):
    return all(values)

def func_or(values):
    return any(values)

def func_xor(values):
    values = list(values)
    return values.count(True) % 2 == 1

def func_not(value):
    value = list(value)
    if len(value) != 1:
        raise ValueError('NOT only takes 1 value')
    return not value[0]

OPERATOR_FUNCTIONS = {
    'AND': func_and,
    'OR': func_or,
    'XOR': func_xor,
    'NOT': func_not,
}

class ExpressionTree:
    def __init__(self, token, parent=None):
        self.children = []
        self.parent = parent
        self.token = token

    def __str__(self):
        if self.token is None:
            return '""'

        if self.token not in OPERATORS:
            t = self.token
            t = t.replace('"', '\\"')
            if ' ' in t:
                t = '"%s"' % t
            return t

        if len(self.children) == 1:
            child = self.children[0]
            childstring = str(child)
            if child.token in OPERATORS:
                childstring = '(%s)' % childstring
                return '%s%s' % (self.token, childstring)
            return '%s %s' % (self.token, childstring)

        children = []
        for child in self.children:
            childstring = str(child)
            if child.token in OPERATORS:
                childstring = '(%s)' % childstring
            children.append(childstring)
        #children = [str(child) for child in self.children]

        if len(children) == 1:
            return '%s %s' % (self.token, children[0])

        s = ' %s ' % self.token
        s = s.join(children)
        return s

    @classmethod
    def parse(cls, tokens, spaces=0):
        if isinstance(tokens, str):
            tokens = tokenize(tokens)

        if isinstance(tokens[0], list):
            current = cls.parse(tokens[0], spaces=spaces+1)
        else:
            current = cls(token=tokens[0])

        for token in tokens[1:]:
            ##print('  '*spaces, 'cur', current, current.token)
            if isinstance(token, list):
                new = cls.parse(token, spaces=spaces+1)
            else:
                new = cls(token=token)
            ##print('  '*spaces, 'new', new)

            if 0 == 1:
                pass

            elif current.token not in OPERATORS:
                if new.token in BINARY_OPERATORS:
                    if len(new.children) == 0:
                        new.children.append(current)
                        current.parent = new
                        current = new
                else:
                    raise Exception('Expected binary operator, got %s.' % new.token)

            elif current.token in BINARY_OPERATORS:
                if new.token in BINARY_OPERATORS:
                    if new.token == current.token:
                        for child in new.children:
                            child.parent = current
                        current.children.extend(new.children)
                    else:
                        if len(new.children) == 0:
                            new.children.append(current)
                            current.parent = new
                            current = new
                        else:
                            current.children.append(new)
                            new.parent = current

                elif new.token in UNARY_OPERATORS:
                    if len(new.children) == 0:
                        current.children.append(new)
                        new.parent = current
                        current = new
                    else:
                        current.children.append(new)
                        new.parent = current

                elif new.token not in OPERATORS:
                    if len(current.children) > 0:
                        current.children.append(new)
                        new.parent = current
                    else:
                        raise Exception('Expected current children > 0.')

            elif current.token in UNARY_OPERATORS:
                if len(current.children) == 0:
                    current.children.append(new)
                    new.parent = current
                    if current.parent is not None:
                        current = current.parent
                elif new.token in BINARY_OPERATORS:
                    if len(new.children) == 0:
                        new.children.append(current)
                        current.parent = new
                        current = new
                    else:
                        current.children.append(new)
                        new.parent = current
                        if current.parent is not None:
                            current = current.parent
                else:
                    raise Exception('Expected new to be my operand or parent binary.')

            ##print('  '*spaces, 'fin:', current.rootmost(), '\n')

        current = current.rootmost()
        ##print('---', current)
        return current

    def _evaluate(self, text, match_function=None):
        if self.token not in OPERATORS:
            if match_function is None:
                match_function = DEFAULT_MATCH_FUNCTION

            value = match_function(text, self.token)
            #print(self.token, value)
            return value

        operator_function = OPERATOR_FUNCTIONS[self.token]
        children = (child.evaluate(text, match_function=match_function) for child in self.children)
        return operator_function(children)

    def evaluate(self, text, match_function=None):
        if match_function is None:
            match_function = DEFAULT_MATCH_FUNCTION

        try:
            return self._evaluate(text, match_function)
        except Exception as e:
            if match_function is DEFAULT_MATCH_FUNCTION:
                message = MESSAGE_WRITE_YOUR_OWN_MATCHER.format(function=DEFAULT_MATCH_FUNCTION)
                override = Exception(message)
                raise override from e
            raise e

    def map(self, function):
        for node in self.walk():
            if node.token in OPERATORS:
                continue
            node.token = function(node.token)

    def prune(self):
        '''
        Remove any nodes where `token` is None.
        '''
        self.children = [child for child in self.children if child is not None]
        for child in self.children:
            child.prune()

    def rootmost(self):
        current = self
        while current.parent is not None:
            current = current.parent
        return current

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()

    def walk_leaves(self):
        for node in self.walk():
            if node.token not in OPERATORS:
                yield node


def implied_tokens(tokens):
    '''
    1. If two operands are directly next to each other, or an operand is followed
        by a unary operator, it is implied that there is an AND between them.
        '1 2' -> '1 AND 2'
        '1 NOT 2' -> '1 AND NOT 2'

    2. If an expression begins or ends with an invalid operator, remove it.
        'AND 2' -> '2'
        '2 AND' -> '2'

    3. If a parenthetical term contains only 1 item, the parentheses can be removed.
        '(a)' -> 'a'
        '(NOT a)' -> 'NOT a'
        '(a OR)' -> '(a)' (by rule 2) -> 'a'

    4. If two operators are next to each other, except for binary-unary,
        keep only the first.
        '1 OR AND 2' -> '1 OR 2'
        '1 NOT AND 2' -> '1 AND NOT AND 2' (by rule 1) -> '1 AND NOT 2'
        'NOT NOT 1' -> 'NOT 1'
        '1 AND NOT NOT 2' -> '1 AND NOT 2'
    '''
    final_tokens = []
    has_operand = False
    has_binary_operator = False
    has_unary_operator = False

    if len(tokens) == 1 and not isinstance(tokens[0], str):
        # [['A' 'AND' 'B']] -> ['A' 'AND' 'B']
        tokens = tokens[0]

    for token in tokens:
        skip_this = False
        while isinstance(token, (list, tuple)):
            if len(token) == 0:
                # Delete empty parentheses.
                skip_this = True
                break
            if len(token) == 1:
                # Take singular terms out of their parentheses.
                token = token[0]
            else:
                previous = token
                token = implied_tokens(token)
                if previous == token:
                    break

        if skip_this:
            continue

        #print('tk:', token, 'hu:', has_unary_operator, 'hb:', has_binary_operator, 'ho:', has_operand)
        if isinstance(token, str) and token in OPERATORS:
            this_binary = token in BINARY_OPERATORS
            this_unary = not this_binary

            # 'NOT AND' and 'AND AND' are malformed...
            if this_binary and (has_binary_operator or has_unary_operator):
                continue
            # ...'NOT NOT' is malformed...
            if this_unary and has_unary_operator:
                continue
            # ...but AND NOT is okay.

            # 'AND test' is malformed
            if this_binary and not has_operand:
                continue

            if this_unary and has_operand:
                final_tokens.append('AND')

            has_unary_operator = this_unary
            has_binary_operator = this_binary
            has_operand = False

        else:
            if has_operand:
                final_tokens.append('AND')
            has_unary_operator = False
            has_binary_operator = False
            has_operand = True

        final_tokens.append(token)

    if has_binary_operator or has_unary_operator:
        final_tokens.pop(-1)

    return final_tokens

def order_operations(tokens):
    for (index, token) in enumerate(tokens):
        if isinstance(token, list):
            tokens[index] = order_operations(token)

    if len(tokens) < 5:
        return tokens

    index = 0
    slice_start = None
    slice_end = None
    precedence_stack = []
    while index < len(tokens):
        #time.sleep(0.1)
        token = tokens[index]
        try:
            precedence = PRECEDENCE.index(token)
        except ValueError:
            precedence = None

        if precedence is None:
            index += 1
            continue
        precedence_stack.append(precedence)


        if token in UNARY_OPERATORS:
            slice_start = index
            slice_end = index + 2

        elif len(precedence_stack) > 1:
            if precedence_stack[-1] < precedence_stack[-2]:
                slice_start = index - 1
                slice_end = None
            elif precedence_stack[-2] < precedence_stack[-1]:
                slice_end = index

        #print(tokens, index, token, precedence_stack, slice_start, slice_end, sep=' || ')

        if slice_start is None or slice_end is None:
            index += 1
            continue

        tokens[slice_start:slice_end] = [tokens[slice_start:slice_end]]
        slice_start = None
        slice_end = None
        for x in range(2):
            if not precedence_stack:
                break

            delete = precedence_stack[-1]
            while precedence_stack and precedence_stack[-1] == delete:
                index -= 1
                precedence_stack.pop(-1)

        index += 1

    if slice_start is not None:
        slice_end = len(tokens)
        tokens[slice_start:slice_end] = [tokens[slice_start:slice_end]]

    return tokens

def sublist_tokens(tokens, _from_index=0, depth=0):
    '''
    Given a list of tokens, replace parentheses with actual sublists.
    ['1', 'AND', '(', '3', 'OR', '4', ')'] ->
    ['1', 'AND', ['3', 'OR', '4']]

    Unclosed parentheses are automatically closed at the end.
    '''
    final_tokens = []
    index = _from_index
    while index < len(tokens):
        token = tokens[index]
        #print(index, token)
        index += 1
        if token == '(':
            (token, index) = sublist_tokens(tokens, _from_index=index, depth=depth+1)
        if token == ')':
            break
        final_tokens.append(token)
    if _from_index == 0:
        return final_tokens
    else:
        return (final_tokens, index)

def tokenize(expression):
    '''
    Break the string into a list of  tokens. Spaces are the delimiter unless
    they are inside quotation marks.

    Quotation marks and parentheses can be escaped by preceeding with a backslash '\\'

    Opening and closing parentheses are put into their own token unless
    escaped / quoted.

    Extraneous closing parentheses are ignored completely.

    '1 AND(4 OR "5 6") OR \\(test\\)' ->
    ['1', 'AND', '(', '4', 'OR', '5 6', ')', 'OR', '\\(test\\)']
    '''
    current_word = []
    in_escape = False
    in_quotes = False
    paren_depth = 0
    tokens = []
    for character in expression:
        if in_escape:
            character = ESCAPE_SEQUENCES.get(character, '\\'+character)
            in_escape = False

        elif character in  {'(', ')'} and not in_quotes:
            if character == '(':
                paren_depth += 1
            elif character == ')':
                paren_depth -= 1

            if paren_depth >= 0:
                tokens.append(''.join(current_word))
                tokens.append(character)
                current_word.clear()
                continue
            else:
                continue

        elif character == '\\':
            in_escape = True
            continue

        elif character == '"':
            in_quotes = not in_quotes
            continue

        elif character.isspace() and not in_quotes:
            tokens.append(''.join(current_word))
            current_word.clear()
            continue

        current_word.append(character)

    tokens.append(''.join(current_word))
    tokens = [w for w in tokens if w != '']
    tokens = sublist_tokens(tokens)
    tokens = implied_tokens(tokens)
    tokens = order_operations(tokens)
    return tokens

if __name__ == '__main__':
    tests = [
    #'test you AND(1 OR "harrison ford") AND (where are you) AND pg',
    #'(you OR "AND ME")',
    #'(3 XOR 2 OR 4',
    #'1 NOT OR AND (2 OR (3 OR 4) OR (5 OR 6)))',
    #'3 OR (5 OR)',
    #'1 AND(4 OR "5 6")OR \\(test) 2',
    #'1 2 AND (3 OR 4)',
    #'AND 2',
    #'1 AND 2 AND ("3 7" OR 6)AND (4 OR 5)',
    #'NOT 1 AND NOT (2 OR 3)',
    #'1 AND 2 AND 3 AND 4',
    #'NOT 1 AND 2 OR 3 OR (5 AND 6)',
    #'5 OR 6 AND 7 OR 8',
    #'1 OR 2 AND 3 AND 4 OR 5 AND 6 OR 7 OR 8 AND 9',
    #'2 XOR 3 AND 4',
    #'1 OR (2 OR 3 AND 4)',
    #'NOT XOR 4 7'
    '[sci-fi] OR [pg-13]',
    '([sci-fi] OR [war]) AND [r]',
    '[r] XOR [sci-fi]',
    '"mark hamill" "harrison ford"',
    ]
    teststrings = {
        'Star Wars': '[harrison ford] [george lucas] [sci-fi] [pg] [carrie fisher] [mark hamill] [space]',
        'Blade Runner': '[harrison ford] [ridley scott] [neo-noir] [dystopian] [sci-fi] [r]',
        'Indiana Jones': '[harrison ford] [steven spielberg] [adventure] [pg-13]',
        'Apocalypse Now': '[harrison ford] [francis coppola] [r] [war] [drama]'
    }
    for token in tests:
        print('start:', token)
        token = tokenize(token)
        print('implied:', token)
        e = ExpressionTree.parse(token)
        print('tree:', e)
        for (name, teststring) in teststrings.items():
            print('Matches', name, ':', e.evaluate(teststring))
        print()
