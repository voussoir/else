import string

ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

def from_base(number, base, alphabet=None):
    if base < 2:
        raise ValueError('base must be >= 2.')
    if not isinstance(base, int):
        raise TypeError('base must be an int.')

    if base == 10:
        return int(number)

    if alphabet is None:
        alphabet = ALPHABET
    number = str(number)
    alphabet = alphabet[:base]

    if number.count('.') > 1:
        raise ValueError('Too many decimal points')

    mixed_case = any(c in string.ascii_uppercase for c in alphabet) and \
                 any(c in string.ascii_lowercase for c in alphabet)
    if not mixed_case:
        alphabet = alphabet.upper()
        number = number.upper()

    char_set = set(number.replace('.', '', 1))
    alpha_set = set(alphabet)
    differences = char_set.difference(alpha_set)
    if len(differences) > 0:
        raise ValueError('Unknown characters for base', base, differences)
    alpha_dict = {character:index for (index, character) in enumerate(alphabet)}

    try:
        decimal_pos = number.index('.')
    except ValueError:
        decimal_pos = len(number)

    result = 0
    for (index, character) in enumerate(number):
        if index == decimal_pos:
            continue
        power = (decimal_pos - index)
        if index < decimal_pos:
            power -= 1
        value = alpha_dict[character] * (base ** power)
        #print(value)
        result += value
    return result

def to_base(number, base, decimal_places=10, alphabet=None):
    if base < 2:
        raise ValueError('base must be >= 2.')
    if not isinstance(base, int):
        raise TypeError('base must be an int.')

    if base == 10:
        return str(number)

    if alphabet is None:
        alphabet = ALPHABET

    if base > len(alphabet):
        raise ValueError('Not enough symbols in alphabet for base %d' % base)

    result = ''
    whole_portion = int(number)
    float_portion = number - whole_portion
    while whole_portion > 0:
        (whole_portion, remainder) = divmod(whole_portion, base)
        result = alphabet[remainder] + result
    if float_portion != 0:
        result += '.'
        for x in range(decimal_places):
            float_portion *= base
            whole = int(float_portion)
            float_portion -= whole
            result += alphabet[whole]

    return result
