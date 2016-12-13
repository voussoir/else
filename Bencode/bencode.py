'''
A Python 3 translation of bcode.py
https://pypi.python.org/pypi/bcode/0.5
'''

def bencode(data):
    '''
    Encode python types to bencode.
    '''
    if data is None:
        return None

    data_type = type(data)

    encoders = {
        bytes: encode_bytes,
        str: encode_string,
        float: encode_float,
        int: encode_int,
        dict: encode_dict,
    }

    encoder = encoders.get(data_type, None)
    if encoder is None:
        try:
            return encode_iterator(iter(data))
        except TypeError:
            raise ValueError('Invalid field type %s' % data_type)
    return encoder(data)

def encode_bytes(data):
    return '%d:%s' % (len(data), data)

def encode_dict(data):
    result = []
    keys = list(data.keys())
    keys.sort()
    for key in keys:
        result.append(bencode(key))
        result.append(bencode(data[key]))
    result = ''.join(result)
    return 'd%se' % result

def encode_float(data):
    return encode_string(str(data))

def encode_int(data):
    return 'i%de' % data

def encode_iterator(data):
    result = []
    for item in data:
        result.append(bencode(item))
    result = ''.join(result)
    return 'l%se' % result

def encode_string(data):
    return encode_bytes(data)


# =============================================================================


def bdecode(data):
    '''
    Decode bencode to python types.

    Returns a dictionary
    {
        'result': the decoded item
        'remainder': what's left of the input text
    }
    '''
    if data is None:
        return None

    data = data.strip()
    if isinstance(data, bytes):
        data = data.decode('utf-8')

    if data[0] == 'i':
        return decode_int(data)

    if data[0].isdigit():
        return decode_string(data)

    if data[0] == 'l':
        return decode_list(data)

    if data[0] == 'd':
        return decode_dict(data)

    raise ValueError('Invalid initial delimiter "%s"' % data[0])

def decode_dict(data):
    result = {}

    # slice leading d
    remainder = data[1:]
    while remainder[0] != 'e':
        temp = bdecode(remainder)
        key = temp['result']
        remainder = temp['remainder']

        temp = bdecode(remainder)
        value = temp['result']
        remainder = temp['remainder']

        result[key] = value

    # slice ending 3
    remainder = remainder[1:]
    return {'result': result, 'remainder': remainder}

def decode_int(data):
    end = data.find('e')
    if end == -1:
        raise ValueError('Missing end delimiter "e"')

    # slice leading i and closing e
    result = data[1:end]
    remainder = data[end+1:]
    return {'result': result, 'remainder': remainder}

def decode_list(data):
    result = []
    
    # slice leading l
    remainder = data[1:]
    while remainder[0] != 'e':
        item = bdecode(data)
        result.append(item['result'])
        reaminder = item['remainder']

    # slice ending e
    remainder = remainder[1:]
    return {'result': result, 'remainder': remainder}

def decode_string(data):
    start = data.find(':') + 1
    size = int(data[:start-1])
    end = start + size
    text = data[start:end]
    if len(text) < size:
        raise ValueError('Actual length %d is less than declared length %d' % len(text), size)
    remainder = data[end:]
    return {'result': text, 'remainder': remainder}
