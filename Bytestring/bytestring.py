import re
import sys

__VERSION__ = '0.0.1'

BYTE = 1
KIBIBYTE = 1024 * BYTE
MIBIBYTE = 1024 * KIBIBYTE
GIBIBYTE = 1024 * MIBIBYTE
TEBIBYTE = 1024 * GIBIBYTE
PEBIBYTE = 1024 * TEBIBYTE
EXIBYTE = 1024 * PEBIBYTE
ZEBIBYTE = 1024 * EXIBYTE
YOBIBYTE = 1024 * ZEBIBYTE

BYTE_STRING = 'b'
KIBIBYTE_STRING = 'KiB'
MIBIBYTE_STRING = 'MiB'
GIBIBYTE_STRING = 'GiB'
TEBIBYTE_STRING = 'TiB'
PEBIBYTE_STRING = 'PiB'
EXIBYTE_STRING = 'EiB'
ZEBIBYTE_STRING = 'ZiB'
YOBIBYTE_STRING = 'YiB'

UNIT_STRINGS = {
    BYTE: BYTE_STRING,
    KIBIBYTE: KIBIBYTE_STRING,
    MIBIBYTE: MIBIBYTE_STRING,
    GIBIBYTE: GIBIBYTE_STRING,
    TEBIBYTE: TEBIBYTE_STRING,
    PEBIBYTE: PEBIBYTE_STRING,
    EXIBYTE: EXIBYTE_STRING,
    ZEBIBYTE: ZEBIBYTE_STRING,
    YOBIBYTE: YOBIBYTE_STRING,
}
REVERSED_UNIT_STRINGS = {value: key for (key, value) in UNIT_STRINGS.items()}
UNIT_SIZES = sorted(UNIT_STRINGS.keys(), reverse=True)


def bytestring(size, decimal_places=3, force_unit=None):
    '''
    Convert a number into  string.

    force_unit:
        If None, an appropriate size unit is chosen automatically.
        Otherwise, you can provide one of the size constants to force that divisor.
    '''
    if force_unit is None:
        divisor = get_appropriate_divisor(size)
    else:
        if isinstance(force_unit, str):
            force_unit = normalize_unit_string(force_unit)
            force_unit = REVERSED_UNIT_STRINGS[force_unit]
        divisor = force_unit

    size_unit_string = UNIT_STRINGS[divisor]

    size_string = '{number:.0{decimal_places}f} {unit}'
    size_string = size_string.format(
        decimal_places=decimal_places,
        number=size/divisor,
        unit=size_unit_string,
    )
    return size_string

def get_appropriate_divisor(size):
    '''
    Return the divisor that would be appropriate for displaying this byte size.
    For example:
        1000 => 1 to display 1,000 b
        1024 => 1024 to display 1 KiB
        123456789 => 1048576 to display 117.738 MiB
    '''
    size = abs(size)
    for unit in UNIT_SIZES:
        if size >= unit:
            appropriate_unit = unit
            break
    else:
        appropriate_unit = 1
    return appropriate_unit

def normalize_unit_string(string):
    '''
    Given a string "k" or "kb" or "kib" in any case, return "KiB", etc.
    '''
    string = string.lower()
    for (size, unit_string) in UNIT_STRINGS.items():
        unit_string_l = unit_string.lower()
        if string in (unit_string_l, unit_string_l[0], unit_string_l.replace('i', '')):
            return unit_string
    raise ValueError('Unrecognized unit string "%s"' % string)

def parsebytes(string):
    '''
    Given a string like "100 kib", return the appropriate integer value.
    Accepts "k", "kb", "kib" in any casing.
    '''
    string = string.lower().strip()
    string = string.replace(' ', '').replace(',', '')

    matches = re.findall('((\\.|-|\\d)+)', string)
    if len(matches) == 0:
        raise ValueError('No numbers found')
    if len(matches) > 1:
        raise ValueError('Too many numbers found')
    byte_value = matches[0][0]

    if not string.startswith(byte_value):
        raise ValueError('Number is not at start of string')


    # if the string has no text besides the number, just return that int.
    string = string.replace(byte_value, '')
    byte_value = float(byte_value)
    if string == '':
        return int(byte_value)

    unit_string = normalize_unit_string(string)
    multiplier = REVERSED_UNIT_STRINGS[unit_string]

    return int(byte_value * multiplier)

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    if len(args) != 1:
        print('Usage: bytestring.py <number>')
        return 1
    n = int(sys.argv[1])
    print(bytestring(n))
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
