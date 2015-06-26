'''
                            -----:::
                     ...-----------:::::::::
                ............---------:::::::,,,,
             ..`````````.......--------:::::::,,,,,
           .```````````````...:vv,------:::::::,,,,,"
         ..``````````````````-zz+z:------::::::,,,,,,""
       ....``````       `````-zzzz:------:::::::,,,,,,"""
      .....`````         `````xzzx.-------::::::,,,,,,""""
    ---..::-`````        ````,zzzz".------:::::::,,,_~~""""_
   -----xzzzJ?~-```    `````_Jzzzzz~------::::::"vJonnnT"""__
  ------L+zzzzzz?".`````.:~xzzzzz+++J/":--:::,;Jooonnnn+"""___
  :------/z+zzzzzzzxL??xzzzzzzz+++++++TTzJJJ+ooooonnnoL""""___
 :::-------;J++zzzzzzzzzzzzzzzxxxJ+++TTTTTTToooooonT?""""""____
 :::::-------~L+++++++++++z/,------"v+TTTTTooooooz/","""""_____
::::::::-------,vz+++++++z,----------"+TTooooooL_,,,""""""______
,,:::::::::------:L++++++x---------:::JooooooJ",,,,""""""_______
,,,,::::::::::::---?TTTTTTv:---::::::vooooooL,,,,,""""""________
,,,,,,,::::::::::::~TTTTTTT+xv/;;/?xToooooon;,,,,""""""_________
 ,,,,,,,,,,:::::::,zooooooooooooooooooooonnn+",""""""__________
 """,,,,,,,,,,,,,,zoooooooooooooooooonnnnnnnn+"""""____________
  """""",,,,,,,,,,ooooooooooooonnnnnnnnnnnnnnn_""_____________
  """"""""""",,,,,+nnnnnnnnnnnnnnnnnnnnnnnnZZT"_______________
   ____"""""""""""vnnnnnnnnnnnnnnnnnnnnZZZZZZ?_______________
    ________"""""""znnnnnnnnnnnZZZZZZZZZZZZZz_______________
      ______________JZZZZZZZZZZZZZZZZZZZZZZz______________
       ______________/+ZZZZZZZZZZZZZeeeeZ+/______________
         ______________;xoeeeeeeeeeeeeox;______________
           _______________~vxJz++zJxv~_______________
             ______________________________________
                ________________________________
                     _______________________
                            ________

'''
import os
import shutil
import time

BYTE = 1
KILOBYTE = BYTE * 1024
MEGABYTE = KILOBYTE * 1024
GIGABYTE = MEGABYTE * 1024
TERABYTE = GIGABYTE * 1024

CHUNKSIZE = 64 * KILOBYTE
# Number of bytes to read and write at a time

EXC_SRCNOTDIR = 'srcnotdir'
EXC_SRCNOTFILE = 'srcnotfle'
EXC_RECURDIR = 'recurdir'
# These strings will become the `description` attribute
# of a SpinalError when it is raised. Use it to determine
# what type of SpinalError has occured.


class SpinalError(Exception):
    def __init__(self, err, desc):
        super(SpinalError, self)
        self.description = desc


def copyfile(src, dst, overwrite=True, callbackfunction=None):
    '''
    Copy a file from src to dst.

                 src : the file to copy.

                 dst : the filename of the new copy.

           overwrite : if True, copy src to dst even if
                       dst already exists.
                       else, do nothing.

                       default = True

    callbackfunction : if provided, this function will be called
                       after writing each CHUNKSIZE bytes to dst
                       with three parameters:
                       name of file being copied,
                       number of bytes written so far,
                       total number of bytes needed.

                       default = None

    RETURN : [dst filename, number of bytes written to dst]
    '''

    src = os.path.abspath(src)
    dst = os.path.abspath(dst)

    if not os.path.isfile(src):
        raise SpinalError("Source file is not a file: %s" % src,
              EXC_SRCNOTFILE)

    totalbytes = os.path.getsize(src)
    dstexists = os.path.exists(dst)
    if dstexists and overwrite is False:
        if callbackfunction is not None:
            callbackfunction(dst, totalbytes, totalbytes)
        return [dst, totalbytes]        
    elif dstexists:
        src_modtime = os.path.getmtime(src)
        dst_modtime = os.path.getmtime(dst)
        if src_modtime == dst_modtime:
            if callbackfunction is not None:
                callbackfunction(dst, totalbytes, totalbytes)
            return [dst, totalbytes]

    writtenbytes = 0
    srcfile = open(src, 'rb')
    dstfile = open(dst, 'wb')
    while True:
        filedata = srcfile.read(CHUNKSIZE)
        datasize = len(filedata)
        if datasize == 0:
            break

        dstfile.write(filedata)
        writtenbytes += datasize

        if callbackfunction is not None:
            callbackfunction(dst, writtenbytes, totalbytes)

    srcfile.close()
    dstfile.close()
    shutil.copystat(src, dst)
    return [dst, writtenbytes]

def copydir(srcdir, dstdir, overwrite=True, precalcsize=False,
            callbackfunction=None, callbackfile=None):
    '''
    Copy all of the contents from srcdir to dstdir,
    including subdirectories.

              srcdir : the directory which will be copied.

              dstdir : the directory in which copied files are placed.

           overwrite : if True, overwrite any files in dstdir with
                       the copies from srcdir should they already exist.
                       else, ignore them.

                       default = True

         precalcsize : if True, calculate the size of srcdir
                       before beginning the operation. This number
                       can be used in the callbackfunction.
                       else, callbackfunction will receive
                       written bytes as total bytes.

                       default = False

    callbackfunction : if provided, this function will be called
                       after each file copy with three parameters:
                       name of file copied,
                       number of bytes written to dstdir so far,
                       total bytes needed (from precalcsize).

                       default = None

        callbackfile : will be passed into each individual copyfile() as
                       the callbackfunction for that file.

                       default = None

    RETURN : [dstdir path, number of bytes written to dstdir]

    '''

    srcdir = os.path.abspath(srcdir)
    dstdir = os.path.abspath(dstdir)

    if dstdir.startswith(srcdir):
        raise SpinalError("Will not copy a dir into itself %s" % dstdir,
              EXC_RECURDIR)

    if os.path.isfile(srcdir):
        raise SpinalError("Destination dir is a file: %s" % dstdir,
              EXC_SRCNOTDIR)

    if precalcsize is True:
        totalbytes = getdirsize(srcdir)
    else:
        totalbytes = 0

    walker = os.walk(srcdir)
    writtenbytes = 0
    for step in walker:
        # (path, [dirs], [files])
        srcpath = step[0]
        dstpath = srcpath.replace(srcdir, dstdir)
        files = step[2]
        if not os.path.exists(dstpath):
            os.makedirs(dstpath)
        for filename in files:
            srcfile = os.path.join(srcpath, filename)
            dstfile = os.path.join(dstpath, filename)
            copied = copyfile(srcfile, dstfile, overwrite=overwrite,
                            callbackfunction=callbackfile)
            copiedname = copied[0]
            writtenbytes += copied[1]
            if callbackfunction is None:
                continue

            if totalbytes == 0:
                # precalcsize was not used. Just report the written bytes
                callbackfunction(copiedname, writtenbytes, writtenbytes)
            else:
                # provide the precalcsize
                callbackfunction(copiedname, writtenbytes, totalbytes)

    return [dstdir, writtenbytes]

def getdirsize(srcdir):
    '''
    Using os.walk, return the total number of bytes
    this directory contains, including all subdirectories.
    '''

    srcdir = os.path.abspath(srcdir)

    if not os.path.isdir(srcdir):
        raise SpinalError("Source dir is not a directory: %s" % srcdir,
              EXC_SRCNOTDIR)

    totalbytes = 0
    walker = os.walk(srcdir)
    for step in walker:
        # (path, [dirs], [files])
        path = step[0]
        files = step[2]
        for filename in files:
            fpath = os.path.join(path, filename)
            totalbytes += os.path.getsize(fpath)

    return totalbytes

def cb(filename, written, total):
    '''
    Example of a callbackfunction.

    Prints the number of bytes written,
    total bytes needed,
    and percentage so far.
    '''

    name = os.path.basename(filename)

    if written >= total:
        ends = '\n'
    else:
        ends = '\n'
    percentage = (100 * written) / total
    percentage = '%03.3f' % percentage
    written = '{:,}'.format(written)
    total = '{:,}'.format(total)
    written = (' '*(len(total)-len(written))) + written
    status = '%s %s / %s (%s)\r' % (name, written, total, percentage)
    print(status, end=ends)