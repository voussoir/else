import jobs
import time

def continuous_register():
    print('w')
    jobs.register(2, continuous_register)

jobs.register(5, print, args=('heyo',))
time.sleep(10)
print('x')
jobs.register(5, print, args=('heyo',))
time.sleep(2)
jobs.unregister(print, args=('heyo', ), kwargs={})
time.sleep(10)
print('y')