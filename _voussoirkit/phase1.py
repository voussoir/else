import shutil
import os

PATHS = [
'D:\\git\\else\\BaseNumber\\basenumber.py',
'D:\\git\\else\\Bytestring\\bytestring.py',
'D:\\git\\else\\Cacheclass\\cacheclass.py',
'D:\\git\\else\\Clipext\\clipext.py',
'D:\\git\\else\\Downloady\\downloady.py',
'D:\\git\\else\\ExpressionMatch\\expressionmatch.py',
'D:\\git\\else\\Fusker\\fusker.py',
'D:\\git\\else\\Passwordy\\passwordy.py',
'D:\\git\\else\\Pathclass\\pathclass.py',
'D:\\git\\else\\QuickID\\quickid.py',
'D:\\git\\else\\Ratelimiter\\ratelimiter.py',
'D:\\git\\else\\RateMeter\\ratemeter.py',
'D:\\git\\else\\Safeprint\\safeprint.py',
'D:\\git\\else\\SpinalTap\\spinal.py',
'D:\\git\\else\\SQLHelpers\\sqlhelpers.py',
'D:\\git\\else\\Treeclass\\pathtree.py',
'D:\\git\\else\\Treeclass\\treeclass.py',
]

if __name__ == '__main__':
    os.makedirs('voussoirkit', exist_ok=True)
    for filename in PATHS:
        shutil.copy(filename, os.path.join('voussoirkit', os.path.basename(filename)))
    open(os.path.join('voussoirkit', '__init__.py'), 'w').close()
