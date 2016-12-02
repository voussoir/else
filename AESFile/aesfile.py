import argparse
import hashlib
from Crypto.Cipher import AES
import sys
import os

# pip install
# https://raw.githubusercontent.com/voussoir/else/master/_voussoirkit/voussoirkit.zip
from voussoirkit import bytestring


BLOCK_SIZE = 32

SEEK_END = 2

def decrypt_file(aes, input_handle, output_handle):
    current_pos = input_handle.tell()
    input_size = input_handle.seek(0, SEEK_END) - current_pos
    input_handle.seek(current_pos)
    bytes_read = 0
    while True:
        chunk = input_handle.read(BLOCK_SIZE)
        if len(chunk) == 0:
            break
        bytes_read += len(chunk)
        chunk = aes.decrypt(chunk)
        if bytes_read == input_size:
            last_byte = chunk[-1]
            while chunk and chunk[-1] == last_byte:
                chunk = chunk[:-1]
        if bytes_read % bytestring.MIBIBYTE == 0:
            print(bytestring.bytestring(bytes_read))
        output_handle.write(chunk)

def encrypt_file(aes, input_handle, output_handle):
    last_byte = 0
    done = False
    bytes_read = 0
    while not done:
        chunk = input_handle.read(BLOCK_SIZE)
        if len(chunk) > 0:
            last_byte = chunk[-1]
        if len(chunk) < BLOCK_SIZE:
            pad_byte = (last_byte + 1) % 256
            pad_byte = chr(pad_byte)
            pad_byte = pad_byte.encode('ascii')
            chunk += pad_byte * (BLOCK_SIZE - len(chunk))
            done = True
        bytes_read += len(chunk)
        if bytes_read % bytestring.MIBIBYTE == 0:
            print(bytestring.bytestring(bytes_read))
        chunk = aes.encrypt(chunk)
        output_handle.write(chunk)
        #print(''.join((hex(x)[2:].rjust(2, '0') for x in chunk)))

def prepare_handles_argparse(args):
    return (aes, input_handle, output_handle)

def encrypt_argparse(args):
    input_handle = open(args.input, 'rb')
    output_handle = open(args.output, 'wb')

    password = hashit(args.password, 32)
    initialization_vector = os.urandom(16)
    aes = AES.new(password, mode=3, IV=initialization_vector)
    output_handle.write(initialization_vector)

    encrypt_file(aes, input_handle, output_handle)

def decrypt_argparse(args):
    input_handle = open(args.input, 'rb')
    output_handle = open(args.output, 'wb')

    password = hashit(args.password, 32)
    initialization_vector = input_handle.read(16)
    aes = AES.new(password, mode=3, IV=initialization_vector)
    decrypt_file(aes, input_handle, output_handle)

def hashit(text, length=None):
    h = hashlib.sha512(text.encode('utf-8')).hexdigest()
    if length is not None:
        h = h[:length]
    return h

def main(argv):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    p_encrypt = subparsers.add_parser('encrypt')
    p_encrypt.add_argument('-i', '--input', dest='input', required=True)
    p_encrypt.add_argument('-o', '--output', dest='output', required=True)
    p_encrypt.add_argument('-p', '--password', dest='password', required=True)
    p_encrypt.set_defaults(func=encrypt_argparse)

    p_decrypt = subparsers.add_parser('decrypt')
    p_decrypt.add_argument('-i', '--input', dest='input', required=True)
    p_decrypt.add_argument('-o', '--output', dest='output', required=True)
    p_decrypt.add_argument('-p', '--password', dest='password', required=True)
    p_decrypt.set_defaults(func=decrypt_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])