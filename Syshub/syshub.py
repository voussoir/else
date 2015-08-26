'''
This module allows the user to redirect sys.stdout, stdin, and exceptions
streams (referred to as std* collectively) on a per-module basis. That is,
a main program can import both moduleA and moduleB, then register them here
so that any print statements or prompts in the modules will behave differently.
'''

import inspect
import sys
import traceback

class SysRouter:
    def __init__(self):
        if self.__class__.ROUTER_EXISTS:
            raise ValueError('You may only instantiate one of each SysRouter')
        self.__class__.ROUTER_EXISTS = True

    def router_get_caller(self, key, default, jumps=0):
        stack = inspect.stack()

        calling_frame = stack[2+jumps][0]
        calling_module = inspect.getmodule(calling_frame)
        if calling_module is None:
            try:
                calling_frame = stack[3+jumps][0]
                calling_module = inspect.getmodule(calling_frame)    
                calling_name = calling_module.__name__
            except:
                calling_name = ''
        else:
            calling_name = calling_module.__name__

        rerouted = SYSHUB_MAP.get(calling_name, {}).get(key, default)
        return rerouted

class SysRouterOut(SysRouter):
    ROUTER_EXISTS = False

    def flush(self):
        STDOUT.flush()

    def write(self, data):
        rerouted = self.router_get_caller('out', STDOUT.write)
        return rerouted(data)

class SysRouterIn(SysRouter):
    ROUTER_EXISTS = False

    def readline(self):
        rerouted = self.router_get_caller('in', STDIN.readline)
        return rerouted()

#class SysRouterErr(SysRouter):
#    ROUTER_EXISTS = False
#
#    def flush(self):
#        STDERR.flush()
#
#    def write(self, data):
#        rerouted = self.router_get_caller('out', STDERR.write)
#        return rerouted(data)

class SysRouterExc(SysRouter):
    ROUTER_EXISTS = False

    def __call__(self, exception_type, exception_instance, trace):
        caller = traceback._format_exception_iter(ValueError, exception_instance, trace,None, None)
        caller = list(caller)[-2]
        caller = caller.split('"')[1]
        caller = caller.replace('\\', '/')
        caller = caller.split('/')[-1]
        caller = caller.split('.')[0]
        rerouted = SYSHUB_MAP.get(caller, {}).get('exc', EXCEPTHOOK)
        rerouted(exception_type, exception_instance, trace)

SYSHUB_MAP = {}

STDOUT = sys.stdout
STDIN = sys.stdin
#STDERR = sys.stderr
EXCEPTHOOK = sys.excepthook
sys.stdout = SysRouterOut()
sys.stdin = SysRouterIn()
#sys.stderr = SysRouterErr()
sys.excepthook = SysRouterExc()

def register(module, calltype, method):
    '''
    Register a module in the syshub map.
    
    When the module performs an input, output, or err operation, Syshub will
    check the map so see if it should redirect the call to the provided
    method.

    Registered modules will not affect the behavior of unregistered modules.

    Rerouting a module's 'out' will not affect that module's 'in', etc.

    -----

    parameters:
    module   = the module object from which calls will be rerouted.
    calltype = one of {'out', 'in', 'exc}, corresponding to sys.std*
               and sys.excepthook
    method   = the method to which any arguments intended for the std* method
               will be passed.

    -----

    SYSHUB_MAP is kept in the format:

    {module: {'out': method, 'in': method, 'exc': method}}
    '''
    i = module.__name__
    if i in SYSHUB_MAP:
        SYSHUB_MAP[i][calltype] = method
    else:
        SYSHUB_MAP[i] = {calltype: method}
