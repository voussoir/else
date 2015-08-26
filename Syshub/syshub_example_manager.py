import inspect
import syshub
import syshub_example_slave as slave
import syshub_example_slave2 as slave2
import sys
import traceback

def print_from_slave(data):
    if data not in ('\n', ''):
        data = 'SLAVE]: ' + data
    sys.stdout.write(data)
    sys.stdout.flush()
    return len(data)

def input_from_slave():
    sys.stdout.write('\n')
    return 'robots'

def exception_from_slave(exception_type, exception_instance, trace):
    message = traceback.format_exception(exception_type, exception_instance, trace)
    message = ''.join(message)
    message = 'SLAVE]: ' + message.replace('\n', '\nSLAVE]: ')
    sys.stderr.write(message)
    sys.stderr.flush()
    return len(message)

def print_from_slave2(data):
    if data not in ('\n', ''):
        data = 'SLAV2]: ' + data
    sys.stdout.write(data)
    sys.stdout.flush()
    return len(data)

def input_from_slave2():
    return input('type here> ')

syshub.register(module=slave, calltype='out', method=print_from_slave)
syshub.register(module=slave, calltype='in', method=input_from_slave)
syshub.register(module=slave, calltype='exc', method=exception_from_slave)

syshub.register(module=slave2, calltype='out', method=print_from_slave2)
syshub.register(module=slave2, calltype='in', method=input_from_slave2)
#print(syshub.SYSHUB_MAP)
slave.say_something()
slave.input_something()
slave2.say_something()
slave2.input_something()
slave.raise_something()