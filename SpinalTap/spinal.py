import json
import os
import ratelimiter
import shutil
import sys
import time

BYTE = 1
KIBIBYTE = BYTE * 1024
MIBIBYTE = KIBIBYTE * 1024
GIBIBYTE = MIBIBYTE * 1024
TEBIBYTE = GIBIBYTE * 1024

CHUNK_SIZE = 64 * KIBIBYTE
# Number of bytes to read and write at a time


class DestinationIsDirectory(Exception):
    pass

class DestinationIsFile(Exception):
    pass

class RecursiveDirectory(Exception):
    pass

class SourceNotDirectory(Exception):
    pass

class SourceNotFile(Exception):
    pass

class SpinalError(Exception):
    pass


def callback_exclusion(name, path_type):
    '''
    Example of an exclusion callback function.
    '''
    print('Excluding', name)

def callback_v1(filename, written_bytes, total_bytes):
    '''
    Example of a copy callback function.

    Prints "filename written/total (percent%)"
    '''
    if written_bytes >= total_bytes:
        ends = '\n'
    else:
        ends = ''
    percent = (100 * written_bytes) / total_bytes
    percent = '%03.3f' % percent
    written = '{:,}'.format(written_bytes)
    total = '{:,}'.format(total_bytes)
    written = written.rjust(len(total), ' ')
    status = '{filename} {written}/{total} ({percent}%)\r'
    status = status.format(filename=filename, written=written, total=total, percent=percent)
    print(status, end=ends)
    sys.stdout.flush()

def copy_file(
    source,
    destination=None,
    destination_new_root=None,
    bytes_per_second=None,
    callback=None,
    dry_run=False,
    overwrite_old=True,
    ):
    '''
    Copy a file from one place to another.

    source:
        The file to copy.

    destination:
        The filename of the new copy. Alternatively, use
        destination_new_root.

    destination_new_root:
        Determine the destination path by calling
        `new_root(source_dir, destination_new_root)`.
        Thus, this path acts as a root and the rest of the path is matched.

    bytes_per_second:
        Restrict file copying to this many bytes per second. Can be an integer
        or an existing Ratelimiter object.
        The provided BYTE, KIBIBYTE, etc constants may help.

        Default = None

    callback:
        If provided, this function will be called after writing
        each CHUNK_SIZE bytes to destination with three parameters:
        name of file being copied, number of bytes written so far,
        total number of bytes needed.

        Default = None

    dry_run:
        Do everything except the actual file copying.

        Default = False

    overwrite_old:
        If True, overwrite the destination file if the source file
        has a more recent "last modified" timestamp.

        Default = True

    Returns: [destination filename, number of bytes written to destination]
    '''
    # Prepare parameters
    if not is_xor(destination, destination_new_root):
        m = 'One and only one of `destination` and '
        m += '`destination_new_root` can be passed'
        raise ValueError(m)

    if destination_new_root is not None:
        destination = new_root(source, destination_new_root)

    source = os.path.abspath(source)
    destination = os.path.abspath(destination)

    if not os.path.isfile(source):
        raise SourceNotFile(source)

    if os.path.isdir(destination):
        raise DestinationIsDirectory(destination)

    if isinstance(bytes_per_second, ratelimiter.Ratelimiter):
        limiter = bytes_per_second
    elif bytes_per_second is not None:
        limiter = ratelimiter.Ratelimiter(allowance_per_period=bytes_per_second, period=1)
    else:
        limiter = None

    source_bytes = os.path.getsize(source)

    # Determine overwrite
    destination_exists = os.path.exists(destination)
    if destination_exists:
        if overwrite_old is False:
            return [destination, source_bytes]

        source_modtime = os.path.getmtime(source)
        destination_modtime = os.path.getmtime(destination)
        if source_modtime == destination_modtime:
            return [destination, source_bytes]

    # Copy
    if dry_run:
        if callback is not None:
            callback(destination, source_bytes, source_bytes)
        return [destination, source_bytes]

    written_bytes = 0
    source_file = open(source, 'rb')
    destionation_file = open(destination, 'wb')
    while True:
        data_chunk = source_file.read(CHUNK_SIZE)
        data_bytes = len(data_chunk)
        if data_bytes == 0:
            break

        destionation_file.write(data_chunk)
        written_bytes += data_bytes

        if limiter is not None:
            limiter.limit(data_bytes)

        if callback is not None:
            callback(destination, written_bytes, source_bytes)

    # Fin
    source_file.close()
    destionation_file.close()
    shutil.copystat(source, destination)
    return [destination, written_bytes]

def copy_dir(
    source_dir,
    destination_dir=None,
    destination_new_root=None,
    bytes_per_second=None,
    callback_directory=None,
    callback_file=None,
    dry_run=False,
    exclude_directories=None,
    exclude_filenames=None,
    exclusion_callback=None,
    overwrite_old=True,
    precalcsize=False,
    ):
    '''
    Copy all of the contents from source_dir to destination_dir,
    including subdirectories.

    source_dir:
        The directory which will be copied.

    destination_dir:
        The directory in which copied files are placed. Alternatively, use
        destination_new_root.

    destination_new_root:
        Determine the destination path by calling
        `new_root(source_dir, destination_new_root)`.
        Thus, this path acts as a root and the rest of the path is matched.

    bytes_per_second:
        Restrict file copying to this many bytes per second. Can be an integer
        or an existing Ratelimiter object.
        The provided BYTE, KIBIBYTE, etc constants may help.

        Default = None

    callback_directory:
        This function will be called after each file copy with three parameters:
        name of file copied, number of bytes written to destination_dir so far,
        total bytes needed (from precalcsize).

        Default = None

    callback_file:
        Will be passed into each individual copy_file() as the `callback`
        for that file.

        Default = None

    dry_run:
        Do everything except the actual file copying.

        Default = False

    exclude_filenames:
        A set of filenames that will not be copied. Entries can be absolute
        paths to exclude that particular file, or plain names to exclude
        all matches. For example:
        {'C:\\folder\\file.txt', 'desktop.ini'}

        Default = None

    exclude_directories:
        A set of directories that will not be copied. Entries can be
        absolute paths to exclude that particular directory, or plain names
        to exclude all matches. For example:
        {'C:\\folder', 'thumbnails'}

        Default = None

    exclusion_callback:
        This function will be called when a file or directory is excluded with
        two parameters: the path, and 'file' or 'directory'.

        Default = None

    overwrite_old:
        If True, overwrite the destination file if the source file
        has a more recent "last modified" timestamp.

        Default = True

    precalcsize:
        If True, calculate the size of source_dir before beginning the
        operation. This number can be used in the callback_directory function.
        Else, callback_directory will receive written bytes as total bytes
        (showing 100% always).
        This can take a long time.

        Default = False

    Returns: [destination_dir path, number of bytes written to destination_dir]
    '''

    # Prepare parameters
    if not is_xor(destination_dir, destination_new_root):
        m = 'One and only one of `destination_dir` and '
        m += '`destination_new_root` can be passed'
        raise ValueError(m)

    if destination_new_root is not None:
        destination_dir = new_root(source_dir, destination_new_root)

    source_dir = os.path.normpath(os.path.abspath(source_dir))
    destination_dir = os.path.normpath(os.path.abspath(destination_dir))

    if is_subfolder(source_dir, destination_dir):
        raise RecursiveDirectory(source_dir, destination_dir)

    if not os.path.isdir(source_dir):
        raise SourceNotDirectory(source_dir)

    if os.path.isfile(destination_dir):
        raise DestinationIsFile(destination_dir)

    if exclusion_callback is None:
        exclusion_callback = lambda *x: None

    if exclude_filenames is None:
        exclude_filenames = set()

    if exclude_directories is None:
        exclude_directories = set()

    exclude_filenames = {normalize(f) for f in exclude_filenames}
    exclude_directories = {normalize(f) for f in exclude_directories}

    if precalcsize is True:
        total_bytes = get_dir_size(source_dir)
    else:
        total_bytes = 0

    if isinstance(bytes_per_second, ratelimiter.Ratelimiter):
        limiter = bytes_per_second
    elif bytes_per_second is not None:
        limiter = ratelimiter.Ratelimiter(allowance_per_period=bytes_per_second, period=1)
    else:
        limiter = None

    # Copy
    written_bytes = 0
    for (source_location, base_filename) in walk_generator(source_dir):
        # Terminology:
        # abspath: C:\folder\subfolder\filename.txt
        # base_filename: filename.txt
        # folder: subfolder
        # location: C:\folder\subfolder
        #source_location = normalize(source_location)
        #base_filename = normalize(base_filename)

        source_folder_name = os.path.split(source_location)[1]
        source_abspath = os.path.join(source_location, base_filename)

        destination_abspath = source_abspath.replace(source_dir, destination_dir)
        destination_location = os.path.split(destination_abspath)[0]

        if base_filename in exclude_filenames:
            exclusion_callback(source_abspath, 'file')
            continue
        if source_abspath in exclude_filenames:
            exclusion_callback(source_abspath, 'file')
            continue
        if source_location in exclude_directories:
            exclusion_callback(source_location, 'directory')
            continue
        if source_folder_name in exclude_directories:
            exclusion_callback(source_location, 'directory')
            continue

        if os.path.isdir(destination_abspath):
            raise DestinationIsDirectory(destination_abspath)

        if not os.path.isdir(destination_location):
            os.makedirs(destination_location)

        copied = copy_file(
            source_abspath,
            destination_abspath,
            bytes_per_second=limiter,
            callback=callback_file,
            dry_run=dry_run,
            overwrite_old=overwrite_old,
        )

        copiedname = copied[0]
        written_bytes += copied[1]

        if callback_directory is not None:
            if precalcsize is False:
                callback_directory(copiedname, written_bytes, written_bytes)
            else:
                callback_directory(copiedname, written_bytes, total_bytes)

    return [destination_dir, written_bytes]

def execute_spinaltask(task):
    '''
    Execute a spinal task.
    '''
    pass

def get_dir_size(source_dir):
    '''
    Calculate the total number of bytes across all files in this directory
    and its subdirectories.
    '''
    source_dir = os.path.abspath(source_dir)

    if not os.path.isdir(source_dir):
        raise SourceNotDirectory(source_dir)

    total_bytes = 0
    for (directory, filename) in walk_generator(source_dir):
        filename = os.path.join(directory, filename)
        filesize = os.path.getsize(filename)
        total_bytes += filesize

    return total_bytes

def is_subfolder(parent, child):
    '''
    Determine whether parent contains child.
    '''
    parent = normalize(os.path.abspath(parent)) + os.sep
    child = normalize(os.path.abspath(child)) + os.sep
    return child.startswith(parent)

def is_xor(*args):
    '''
    Return True if and only if one arg is truthy.
    '''
    return [bool(a) for a in args].count(True) == 1

def new_root(filepath, root):
    '''
    Prepend `root` to `filepath`, drive letter included. For example:
    "C:\\folder\\subfolder\\file.txt" and "C:\\backups" becomes
    "C:\\backups\\C\\folder\\subfolder\\file.txt"

    I use this so that my G: drive can have backups from my C: and D: drives
    while preserving directory structure in G:\\D and G:\\C.
    '''
    filepath = os.path.abspath(filepath)
    root = os.path.abspath(root)
    filepath = filepath.replace(':', os.sep)
    filepath = os.path.normpath(filepath)
    filepath = os.path.join(root, filepath)
    return filepath

def normalize(text):
    '''
    Apply os.path.normpath and os.path.normcase.
    '''
    return os.path.normpath(os.path.normcase(text))

def walk_generator(path):
    '''
    Yield filenames from os.walk so the caller doesn't need to deal with the
    nested for-loops.
    '''
    path = os.path.abspath(path)
    walker = os.walk(path)
    for (location, folders, files) in walker:
        for filename in files:
            yield (location, filename)