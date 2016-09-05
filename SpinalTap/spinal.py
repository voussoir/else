import collections
import glob
import json
import os
import shutil
import stat
import string
import sys
import time

sys.path.append('C:\\git\\else\\Bytestring'); import bytestring
sys.path.append('C:\\git\\else\\Pathclass'); import pathclass
sys.path.append('C:\\git\\else\\Ratelimiter'); import ratelimiter


CHUNK_SIZE = 128 * bytestring.KIBIBYTE
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
    print('Excluding', path_type, name)

def callback_v1(fpobj, written_bytes, total_bytes):
    '''
    Example of a copy callback function.

    Prints "filename written/total (percent%)"
    '''
    filename = fpobj.absolute_path.encode('ascii', 'replace').decode()
    if written_bytes >= total_bytes:
        ends = '\n'
    else:
        ends = ''
    percent = (100 * written_bytes) / max(total_bytes, 1)
    percent = '%07.3f' % percent
    written = '{:,}'.format(written_bytes)
    total = '{:,}'.format(total_bytes)
    written = written.rjust(len(total), ' ')
    status = '{filename} {written}/{total} ({percent}%)\r'
    status = status.format(filename=filename, written=written, total=total, percent=percent)
    print(status, end=ends)
    sys.stdout.flush()

def copy(source, file_args=None, file_kwargs=None, dir_args=None, dir_kwargs=None):
    '''
    Perform copy_dir or copy_file as appropriate for the source path.
    '''
    source = str_to_fp(source)
    if source.is_file:
        file_args = file_args or tuple()
        file_kwargs = file_kwargs or dict()
        return copy_file(source, *file_args, **file_kwargs)
    elif source.is_dir:
        dir_args = dir_args or tuple()
        dir_kwargs = dir_kwargs or dict()
        return copy_dir(source, *dir_args, **dir_kwargs)
    raise SpinalError('Neither file nor dir: %s' % source)

def copy_dir(
        source,
        destination=None,
        destination_new_root=None,
        bytes_per_second=None,
        callback_directory=None,
        callback_exclusion=None,
        callback_file=None,
        callback_permission_denied=None,
        callback_verbose=None,
        dry_run=False,
        exclude_directories=None,
        exclude_filenames=None,
        files_per_second=None,
        overwrite_old=True,
        precalcsize=False,
    ):
    '''
    Copy all of the contents from source to destination,
    including subdirectories.

    source:
        The directory which will be copied.

    destination:
        The directory in which copied files are placed. Alternatively, use
        destination_new_root.

    destination_new_root:
        Determine the destination path by calling
        `new_root(source, destination_new_root)`.
        Thus, this path acts as a root and the rest of the path is matched.

        `destination` and `destination_new_root` are mutually exclusive.

    bytes_per_second:
        Restrict file copying to this many bytes per second. Can be an integer
        or an existing Ratelimiter object.
        The BYTE, KIBIBYTE, etc constants from module 'bytestring' may help.

        Default = None

    callback_directory:
        This function will be called after each file copy with three parameters:
        name of file copied, number of bytes written to destination so far,
        total bytes needed (from precalcsize).
        If `precalcsize` is False, this function will receive written bytes
        for both written and total, showing 100% always.

        Default = None

    callback_exclusion:
        Passed directly into `walk_generator`.

        Default = None

    callback_file:
        Will be passed into each individual `copy_file` operation as the
        `callback` for that file.

        Default = None

    callback_permission_denied:
        Will be passed into each individual `copy_file` operation as the
        `callback_permission_denied` for that file.

        Default = None

    callback_verbose:
        If provided, this function will be called with some operation notes.

        Default = None

    dry_run:
        Do everything except the actual file copying.

        Default = False

    exclude_filenames:
        Passed directly into `walk_generator`.

        Default = None

    exclude_directories:
        Passed directly into `walk_generator`.

        Default = None

    files_per_second:
        Maximum number of files to be processed per second. Helps to keep CPU usage
        low.

        Default = None

    overwrite_old:
        If True, overwrite the destination file if the source file
        has a more recent "last modified" timestamp.

        Default = True

    precalcsize:
        If True, calculate the size of source before beginning the
        operation. This number can be used in the callback_directory function.
        Else, callback_directory will receive written bytes as total bytes
        (showing 100% always).
        This can take a long time.

        Default = False

    Returns: [destination path, number of bytes written to destination]
    (Written bytes is 0 if all files already existed.)
    '''
    # Prepare parameters
    if not is_xor(destination, destination_new_root):
        m = 'One and only one of `destination` and '
        m += '`destination_new_root` can be passed.'
        raise ValueError(m)

    source = str_to_fp(source)

    if destination_new_root is not None:
        source.correct_case()
        destination = new_root(source, destination_new_root)
    destination = str_to_fp(destination)

    if destination in source:
        raise RecursiveDirectory(source, destination)

    if not source.is_dir:
        raise SourceNotDirectory(source)

    if destination.is_file:
        raise DestinationIsFile(destination)

    if precalcsize is True:
        total_bytes = get_dir_size(source)
    else:
        total_bytes = 0

    callback_directory = callback_directory or do_nothing
    callback_verbose = callback_verbose or do_nothing
    bytes_per_second = limiter_or_none(bytes_per_second)
    files_per_second = limiter_or_none(files_per_second)

    # Copy
    written_bytes = 0
    walker = walk_generator(
        source,
        callback_exclusion=callback_exclusion,
        callback_verbose=callback_verbose,
        exclude_directories=exclude_directories,
        exclude_filenames=exclude_filenames,
    )
    for (source_abspath) in walker:
        # Terminology:
        # abspath: C:\folder\subfolder\filename.txt
        # location: C:\folder\subfolder
        # base_name: filename.txt
        # folder: subfolder

        destination_abspath = source_abspath.absolute_path.replace(
            source.absolute_path,
            destination.absolute_path
        )
        destination_abspath = str_to_fp(destination_abspath)

        if destination_abspath.is_dir:
            raise DestinationIsDirectory(destination_abspath)

        destination_location = os.path.split(destination_abspath.absolute_path)[0]
        os.makedirs(destination_location, exist_ok=True)

        copied = copy_file(
            source_abspath,
            destination_abspath,
            bytes_per_second=bytes_per_second,
            callback=callback_file,
            callback_permission_denied=callback_permission_denied,
            callback_verbose=callback_verbose,
            dry_run=dry_run,
            overwrite_old=overwrite_old,
        )

        copiedname = copied[0]
        written_bytes += copied[1]

        if precalcsize is False:
            callback_directory(copiedname, written_bytes, written_bytes)
        else:
            callback_directory(copiedname, written_bytes, total_bytes)

        if files_per_second is not None:
            files_per_second.limit(1)

    return [destination, written_bytes]

def copy_file(
        source,
        destination=None,
        destination_new_root=None,
        bytes_per_second=None,
        callback=None,
        callback_permission_denied=None,
        callback_verbose=None,
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
        the Path object being copied, number of bytes written so far,
        total number of bytes needed.

        Default = None

    callback_permission_denied:
        If provided, this function will be called when a source file denies
        read access, with the file path and the exception object as parameters.
        THE OPERATION WILL RETURN NORMALLY.

        If not provided, the PermissionError is raised.

        Default = None

    callback_verbose:
        If provided, this function will be called with some operation notes.

        Default = None

    dry_run:
        Do everything except the actual file copying.

        Default = False

    overwrite_old:
        If True, overwrite the destination file if the source file
        has a more recent "last modified" timestamp.

        Default = True

    Returns: [destination filename, number of bytes written to destination]
    (Written bytes is 0 if the file already existed.)
    '''
    # Prepare parameters
    if not is_xor(destination, destination_new_root):
        m = 'One and only one of `destination` and '
        m += '`destination_new_root` can be passed'
        raise ValueError(m)

    source = str_to_fp(source)

    if not source.is_file:
        raise SourceNotFile(source)

    if destination_new_root is not None:
        source.correct_case()
        destination = new_root(source, destination_new_root)
    destination = str_to_fp(destination)

    callback = callback or do_nothing
    callback_verbose = callback_verbose or do_nothing

    if destination.is_dir:
        raise DestinationIsDirectory(destination)

    bytes_per_second = limiter_or_none(bytes_per_second)

    # Determine overwrite
    if destination.exists:
        if overwrite_old is False:
            return [destination, 0]

        source_modtime = source.stat.st_mtime
        if source_modtime == destination.stat.st_mtime:
            return [destination, 0]

    # Copy
    if dry_run:
        if callback is not None:
            callback(destination, 0, 0)
        return [destination, 0]

    source_bytes = source.size
    destination_location = os.path.split(destination.absolute_path)[0]
    os.makedirs(destination_location, exist_ok=True)
    written_bytes = 0

    try:
        callback_verbose('Opening handles.')
        source_file = open(source.absolute_path, 'rb')
        destination_file = open(destination.absolute_path, 'wb')
    except PermissionError as exception:
        if callback_permission_denied is not None:
            callback_permission_denied(source, exception)
            return [destination, 0]
        else:
            raise

    while True:
        data_chunk = source_file.read(CHUNK_SIZE)
        data_bytes = len(data_chunk)
        if data_bytes == 0:
            break

        destination_file.write(data_chunk)
        written_bytes += data_bytes

        if bytes_per_second is not None:
            bytes_per_second.limit(data_bytes)

        callback(destination, written_bytes, source_bytes)

    # Fin
    callback_verbose('Closing source handle.')
    source_file.close()
    callback_verbose('Closing dest handle.')
    destination_file.close()
    callback_verbose('Copying metadata')
    shutil.copystat(source.absolute_path, destination.absolute_path)
    return [destination, written_bytes]

def do_nothing(*args):
    '''
    Used by other functions as the default callback.
    '''
    return

def get_dir_size(path):
    '''
    Calculate the total number of bytes across all files in this directory
    and its subdirectories.
    '''
    path = str_to_fp(path)

    if not path.is_dir:
        raise SourceNotDirectory(path)

    total_bytes = 0
    for filepath in walk_generator(path):
        total_bytes += filepath.size

    return total_bytes

def is_subfolder(parent, child):
    '''
    Determine whether parent contains child.
    '''
    parent = normalize(str_to_fp(parent).absolute_path) + os.sep
    child = normalize(str_to_fp(child).absolute_path) + os.sep
    return child.startswith(parent)

def is_xor(*args):
    '''
    Return True if and only if one arg is truthy.
    '''
    return [bool(a) for a in args].count(True) == 1

def limiter_or_none(value):
    if isinstance(value, str):
        value = bytestring.parsebytes(value)
    if isinstance(value, ratelimiter.Ratelimiter):
        limiter = value
    elif value is not None:
        limiter = ratelimiter.Ratelimiter(allowance=value, period=1)
    else:
        limiter = None
    return limiter

def new_root(filepath, root):
    '''
    Prepend `root` to `filepath`, drive letter included. For example:
    "C:\\folder\\subfolder\\file.txt" and "C:\\backups" becomes
    "C:\\backups\\C\\folder\\subfolder\\file.txt"

    I use this so that my G: drive can have backups from my C: and D: drives
    while preserving directory structure in G:\\D and G:\\C.
    '''
    filepath = str_to_fp(filepath).absolute_path
    root = str_to_fp(root).absolute_path
    filepath = filepath.replace(':', os.sep)
    filepath = os.path.normpath(filepath)
    filepath = os.path.join(root, filepath)
    return str_to_fp(filepath)

def normalize(text):
    '''
    Apply os.path.normpath and os.path.normcase.
    '''
    return os.path.normpath(os.path.normcase(text))

def str_to_fp(path):
    '''
    If `path` is a string, create a Path object, otherwise just return it.
    '''
    if isinstance(path, str):
        path = pathclass.Path(path)
    return path

def walk_generator(
        path='.',
        callback_exclusion=None,
        callback_verbose=None,
        exclude_directories=None,
        exclude_filenames=None,
    ):
    '''
    Yield Path objects for files in the file tree, similar to os.walk.

    callback_exclusion:
        This function will be called when a file or directory is excluded with
        two parameters: the path, and 'file' or 'directory'.

        Default = None

    callback_verbose:
        If provided, this function will be called with some operation notes.

        Default = None

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
    '''
    if exclude_directories is None:
        exclude_directories = set()

    if exclude_filenames is None:
        exclude_filenames = set()

    callback_exclusion = callback_exclusion or do_nothing
    callback_verbose = callback_verbose or do_nothing

    exclude_filenames = {normalize(f) for f in exclude_filenames}
    exclude_directories = {normalize(f) for f in exclude_directories}

    path = str_to_fp(path).absolute_path

    if normalize(path) in exclude_directories:
        callback_exclusion(path, 'directory')
        return

    if normalize(os.path.split(path)[1]) in exclude_directories:
        callback_exclusion(path, 'directory')
        return

    directory_queue = collections.deque()
    directory_queue.append(path)

    # This is a recursion-free workplace.
    # Thank you for your cooperation.
    while len(directory_queue) > 0:
        current_location = directory_queue.popleft()
        callback_verbose('listdir: %s' % current_location)
        contents = os.listdir(current_location)
        callback_verbose('received %d items' % len(contents))

        directories = []
        for base_name in contents:
            absolute_name = os.path.join(current_location, base_name)

            if os.path.isdir(absolute_name):
                exclude = normalize(absolute_name) in exclude_directories
                exclude |= normalize(base_name) in exclude_directories
                if exclude:
                    callback_exclusion(absolute_name, 'directory')
                    continue

                directories.append(absolute_name)

            else:
                exclude = normalize(absolute_name) in exclude_filenames
                exclude |= normalize(base_name) in exclude_filenames
                if exclude:
                    callback_exclusion(absolute_name, 'file')
                    continue

                yield(str_to_fp(absolute_name))

        # Extendleft causes them to get reversed, so flip it first.
        directories.reverse()
        directory_queue.extendleft(directories)
