import threading
import time

class ThreadQueue:
    def __init__(self, thread_count, post_processor=None):
        self.thread_count = thread_count
        self.post_processor = post_processor
        self._returns = []
        self._threads = []
        self._lambdas = []
        self._behalfs = {}
        self.hold_open = False

    def _post_process(self, returned_value):
        if self.post_processor is not None:
            self.post_processor(returned_value)
        self._returns.append(returned_value)

    def add(self, function, *function_args, **function_kwargs):
        lam = lambda: self._post_process(function(*function_args, **function_kwargs))
        self._lambdas.append(lam)

    def behalf(self, thread_id, f, *args, **kwargs):
        self._behalfs.setdefault(thread_id, [])
        event = threading.Event()
        call = {'f': f, 'args': args, 'kwargs': kwargs, 'event': event, 'return': None}
        self._behalfs[thread_id].append(call)
        event.wait()
        return call['return']

    def run_behalfs(self):
        calls = self._behalfs.get(threading.current_thread().ident, [])
        while calls:
            call = calls.pop(0)
            ret = call['f'](*call['args'], **call['kwargs'])
            call['return'] = ret
            call['event'].set()
        
    def run_queue(self):
        #print('Managing threads')
        self._threads = [thread for thread in self._threads if thread.is_alive()]
        threads_needed = self.thread_count - len(self._threads)
        if threads_needed > 0:
            for x in range(threads_needed):
                if len(self._lambdas) == 0:
                    break
                lam = self._lambdas.pop(0)
                thread = threading.Thread(target=lam)
                #thread.daemon = True
                thread.start()
                self._threads.append(thread)

    def run(self, hold_open=False):
        self.hold_open = hold_open
        while self.hold_open or self._threads or self._lambdas:
            self.run_queue()
            while self._returns:
                yield self._returns.pop(0)
            self.run_behalfs()

            #time.sleep(0.5)
