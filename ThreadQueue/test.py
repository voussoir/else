import time
import threadqueue
import random
import threading
t = threadqueue.ThreadQueue(4, print)
main_thr = threading.current_thread().ident
def f():
    mysleep = random.randint(1, 10)
    time.sleep(mysleep)
    t.behalf(main_thr, lambda: print(threading.current_thread().ident==main_thr))
    raise ValueError()
    return mysleep

[t.add(f) for x in range(20)]
list(t.run())
