import time

LOOPS = 10000

def func_1():
    pass

def func_2():
    pass


start = time.time()
for x in range(LOOPS):
    func_1()
end = time.time()
print('v1', end - start)

start = time.time()
for x in range(LOOPS):
    func_2()
end = time.time()
print('v2', end - start)
