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
    return b'%d:%s' % (len(data), data)

def encode_dict(data):
    result = []
    keys = list(data.keys())
    keys.sort()
    for key in keys:
        result.append(bencode(key))
        result.append(bencode(data[key]))
    result = b''.join(result)
    return b'd%se' % result

def encode_float(data):
    return encode_bytes(str(data).encode())

def encode_int(data):
    return b'i%de' % data

def encode_iterator(data):
    result = []
    for item in data:
        result.append(bencode(item))
    result = b''.join(result)
    return b'l%se' % result


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

    #data = data.strip()
    if isinstance(data, str):
        data = data.encode('utf-8')

    identifier = data[0:1]
    if identifier == b'i':
        return decode_int(data)

    if identifier.isdigit():
        return decode_bytes(data)

    if identifier == b'l':
        return decode_list(data)

    if identifier == b'd':
        return decode_dict(data)

    raise ValueError('Invalid initial delimiter "%s"' % identifier)

def decode_bytes(data):
    #print('Decoding bytes from', data[:100])
    start = data.find(b':') + 1
    size = int(data[:start-1])
    end = start + size
    text = data[start:end]
    if len(text) < size:
        raise ValueError('Actual length %d is less than declared length %d' % len(text), size)
    remainder = data[end:]
    return {'result': text, 'remainder': remainder}

def decode_dict(data):
    #print('Decoding dict from', data[:100])
    result = {}

    # slice leading d
    remainder = data[1:]
    while remainder[0:1] != b'e':
        temp = bdecode(remainder)
        key = temp['result']
        remainder = temp['remainder']

        temp = bdecode(remainder)
        value = temp['result']
        remainder = temp['remainder']
        result[key] = value

    # slice ending e
    remainder = remainder[1:]
    return {'result': result, 'remainder': remainder}

def decode_int(data):
    #print('Decoding int from', data[:100])
    end = data.find(b'e')
    if end == -1:
        raise ValueError('Missing end delimiter "e"')

    # slice leading i and closing e
    result = int(data[1:end])
    remainder = data[end+1:]
    return {'result': result, 'remainder': remainder}

def decode_list(data):
    #print('Decoding list from', data[:100])
    result = []

    # slice leading l
    remainder = data[1:]
    while remainder[0:1] != b'e':
        item = bdecode(remainder)
        result.append(item['result'])
        remainder = item['remainder']

    # slice ending e
    remainder = remainder[1:]
    return {'result': result, 'remainder': remainder}
