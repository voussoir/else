import shutil
import os

PATHS = [
'C:\\git\\else\\BaseNumber\\basenumber.py',
'C:\\git\\else\\Bytestring\\bytestring.py',
'C:\\git\\else\\Cacheclass\\cacheclass.py',
'C:\\git\\else\\Clipext\\clipext.py',
'C:\\git\\else\\Downloady\\downloady.py',
'C:\\git\\else\\ExpressionMatch\\expressionmatch.py',
'C:\\git\\else\\Fusker\\fusker.py',
'C:\\git\\else\\Pathclass\\pathclass.py',
'C:\\git\\else\\Ratelimiter\\ratelimiter.py',
'C:\\git\\else\\RateMeter\\ratemeter.py',
'C:\\git\\else\\Safeprint\\safeprint.py',
'C:\\git\\else\\SpinalTap\\spinal.py',
'C:\\git\\else\\Treeclass\\pathtree.py',
'C:\\git\\else\\Treeclass\\treeclass.py',
]

if __name__ == '__main__':
    os.makedirs('voussoirkit', exist_ok=True)
    for filename in PATHS:
        shutil.copy(filename, os.path.join('voussoirkit', os.path.basename(filename)))
    open(os.path.join('voussoirkit', '__init__.py'), 'w').close()
