BYTE = 1
KIBIBYTE = 1024 * BYTE
MIBIBYTE = 1024 * KIBIBYTE
GIBIBYTE = 1024 * MIBIBYTE
TEBIBYTE = 1024 * GIBIBYTE
PEBIBYTE = 1024 * TEBIBYTE
EXIBYTE = 1024 * PEBIBYTE
ZEBIBYTE = 1024 * EXIBYTE
YOBIBYTE = 1024 * ZEBIBYTE

UNIT_STRINGS = {
    BYTE: 'b',
    KIBIBYTE: 'KiB',
    MIBIBYTE: 'MiB',
    GIBIBYTE: 'GiB',
    TEBIBYTE: 'TiB',
    PEBIBYTE: 'PiB',
    EXIBYTE: 'EiB',
    ZEBIBYTE: 'ZiB',
    YOBIBYTE: 'YiB',
}

def bytestring(bytes):
    possible_units = sorted(UNIT_STRINGS.keys(), reverse=True)

    # choose which magnitutde to use as the divisor
    if bytes < 1:
        appropriate_unit = 1
    else:
        for unit in possible_units:
            if bytes >= unit:
                appropriate_unit = unit
                break

    size_unit_string = UNIT_STRINGS[appropriate_unit]
    size_string = '%.3f %s' % ((bytes / appropriate_unit), size_unit_string)
    return size_string

def parsebytes(string):
    import re
    string = string.lower().replace(' ', '')

    matches = re.findall('((\\.|\\d)+)', string)
    if len(matches) == 0:
        raise ValueError('No numbers found')
    if len(matches) > 1:
        raise ValueError('Too many numbers found')
    byte_value = matches[0][0]

    if not string.startswith(byte_value):
        raise ValueError('Number is not at start of string')

    string = string.replace(byte_value, '')
    byte_value = float(byte_value)
    if string == '':
        return byte_value

    reversed_units = {value.lower():key for (key, value) in UNIT_STRINGS.items()}
    for (unit_string, multiplier) in reversed_units.items():
        if string in (unit_string, unit_string[0], unit_string.replace('i', '')):
            break
    else:
        raise ValueError('Could not determine byte value of %s' % string)

    return byte_value * multiplier