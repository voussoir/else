import os

import phase1

libdir = 'C:\\python36\\lib\\site-packages\\voussoirkit'
os.makedirs(libdir, exist_ok=True)

initfile = os.path.join(libdir, '__init__.py')
open(initfile, 'w').close()

for path in phase1.PATHS:
    libpath = os.path.join(libdir, os.path.basename(path))
    if not os.path.exists(libpath):
        print(libpath)
        os.link(path, libpath)
