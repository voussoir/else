import signal
import time
import threading

class JobInterruption(Exception):
    pass

class JobSchedulingError(Exception):
    pass

THREAD = None
JOBS = {}
def thread_manager():
    while True:
        now = time.time()
        for (functionid, joblist) in JOBS.items():
            for job in joblist:
                if now < job[0]:
                    continue
                job[1](*job[2], **job[3])
                joblist.remove(job)
        time.sleep(0.5)

def launch_thread():
    global THREAD
    if THREAD is None or THREAD.is_alive is False:
        THREAD = threading.Thread(target=thread_manager)
        THREAD.daemon = True
        THREAD.start()

def register(seconds_from_now, function, args=[], kwargs={}):
    if seconds_from_now <= 0:
        raise JobSchedulingError('cannot schedule jobs for the past')
    iid = id(function)
    schedule = time.time() + seconds_from_now
    if iid not in JOBS:
        JOBS[iid] = [(schedule, function, args, kwargs)]
    else:
        JOBS[iid].append( (schedule, function, args, kwargs) )
    launch_thread()

def unregister_all(function):
    iid = id(function)
    if iid in JOBS:
        del JOBS[iid]

def unregister(function, args, kwargs):
    joblist = JOBS[id(function)]
    for job in joblist:
        if job[1:] != (function, args, kwargs):
            continue
        joblist.remove(job)