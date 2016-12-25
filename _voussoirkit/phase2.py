import shutil
import os

def delete(folder):
    try:
        shutil.rmtree(folder)
    except:
        pass

delete('dist')
delete('voussoirkit')
delete('voussoirkit.egg-info')
