import collections
import glob
import json
import os
import ratelimiter
import shutil
import stat
import string
import sys
import time

BYTE = 1
KIBIBYTE = BYTE * 1024
MIBIBYTE = KIBIBYTE * 1024
GIBIBYTE = MIBIBYTE * 1024
TEBIBYTE = GIBIBYTE * 1024
SIZE_UNITS = (TEBIBYTE, GIBIBYTE, MIBIBYTE, KIBIBYTE, BYTE)

UNIT_STRINGS = {
    BYTE: 'b',
    KIBIBYTE: 'KiB',
    MIBIBYTE: 'MiB',
    GIBIBYTE: 'GiB',
    TEBIBYTE: 'TiB',
}

CHUNK_SIZE = 128 * KIBIBYTE
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

class FilePath:
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self._stat = None
        self._isdir = None
        self._isfile = None
        self._islink = None
        self._size = None

    def __hash__(self):
        return self.path.__hash__()

    def __repr__(self):
        return repr(self.path)

    @property
    def isdir(self):
        return self.type_getter('_isdir', stat.S_ISDIR)

    @property
    def isfile(self):
        return self.type_getter('_isfile', stat.S_ISREG)

    @property
    def islink(self):
        return self.type_getter('_islink', stat.S_ISLNK)

    @property
    def size(self):
        if self._size is None:
            if self.stat is False:
                self._size = None
            else:
                self._size = self.stat.st_size
        return self._size

    @property
    def stat(self):
        if self._stat is None:
            try:
                self._stat = os.stat(self.path)
            except FileNotFoundError:
                self._stat = False
        return self._stat

    def type_getter(self, attr, resolution):
        if getattr(self, attr) is None:
            if self.stat is False:
                return False
            else:
                setattr(self, attr, resolution(self.stat.st_mode))
        return getattr(self, attr)


def bytes_to_unit_string(bytes):
    size_unit = 1
    for unit in SIZE_UNITS:
        if bytes >= unit:
            size_unit = unit
            break
    size_unit_string = UNIT_STRINGS[size_unit]
    size_string = '%.3f %s' % ((bytes / size_unit), size_unit_string)
    return size_string

def callback_exclusion(name, path_type):
    '''
    Example of an exclusion callback function.
    '''
    print('Excluding', name)

def callback_v1(fpobj, written_bytes, total_bytes):
    '''
    Example of a copy callback function.

    Prints "fpobj written/total (percent%)"
    '''
    filename = fpobj.path.encode('ascii', 'replace').decode()
    if written_bytes >= total_bytes:
        ends = '\n'
    else:
        ends = ''
    percent = (100 * written_bytes) / total_bytes
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
    if source.isfile:
        file_args = file_args or tuple()
        file_kwargs = file_kwargs or dict()
        return copy_file(source, *file_args, **file_kwargs)
    elif source.isdir:
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
    callback_file=None,
    callback_permission_denied=None,
    dry_run=False,
    exclude_directories=None,
    exclude_filenames=None,
    exclusion_callback=None,
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

    bytes_per_second:
        Restrict file copying to this many bytes per second. Can be an integer
        or an existing Ratelimiter object.
        The provided BYTE, KIBIBYTE, etc constants may help.

        Default = None

    callback_directory:
        This function will be called after each file copy with three parameters:
        name of file copied, number of bytes written to destination so far,
        total bytes needed (from precalcsize).

        Default = None

    callback_file:
        Will be passed into each individual `copy_file` operation as the
        `callback` for that file.

        Default = None

    callback_permission_denied:
        Will be passed into each individual `copy_file` operation as the
        `callback_permission_denied` for that file.

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

    exclusion_callback:
        Passed directly into `walk_generator`.

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
        m += '`destination_new_root` can be passed'
        raise ValueError(m)

    source = str_to_fp(source)
    source = get_path_casing(source)

    if destination_new_root is not None:
        destination = new_root(source, destination_new_root)
    destination = str_to_fp(destination)

    if is_subfolder(source, destination):
        raise RecursiveDirectory(source, destination)

    if not source.isdir:
        raise SourceNotDirectory(source)

    if destination.isfile:
        raise DestinationIsFile(destination)

    if precalcsize is True:
        total_bytes = get_dir_size(source)
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
    walker = walk_generator(
        source,
        exclude_directories=exclude_directories,
        exclude_filenames=exclude_filenames,
        exclusion_callback=exclusion_callback,
        )
    for (source_abspath) in walker:
        # Terminology:
        # abspath: C:\folder\subfolder\filename.txt
        # location: C:\folder\subfolder
        # base_name: filename.txt
        # folder: subfolder

        destination_abspath = source_abspath.path.replace(source.path, destination.path)
        destination_abspath = str_to_fp(destination_abspath)

        if destination_abspath.isdir:
            raise DestinationIsDirectory(destination_abspath)

        destination_location = os.path.split(destination_abspath.path)[0]
        if not os.path.isdir(destination_location):
            os.makedirs(destination_location)

        copied = copy_file(
            source_abspath,
            destination_abspath,
            bytes_per_second=limiter,
            callback=callback_file,
            callback_permission_denied=callback_permission_denied,
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

    return [destination, written_bytes]

def copy_file(
    source,
    destination=None,
    destination_new_root=None,
    bytes_per_second=None,
    callback=None,
    dry_run=False,
    overwrite_old=True,
    callback_permission_denied=None,
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
        the FilePath object being copied, number of bytes written so far,
        total number of bytes needed.

        Default = None

    callback_permission_denied:
        If provided, this function will be called when a source file denies
        read access, with the file path and the exception object as parameters.
        THE OPERATION WILL RETURN NORMALLY.

        If not provided, the PermissionError is raised.

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
    source = get_path_casing(source)

    if destination_new_root is not None:
        destination = new_root(source, destination_new_root)
    destination = str_to_fp(destination)

    if not source.isfile:
        raise SourceNotFile(source)

    if destination.isdir:
        raise DestinationIsDirectory(destination)

    if isinstance(bytes_per_second, ratelimiter.Ratelimiter):
        limiter = bytes_per_second
    elif bytes_per_second is not None:
        limiter = ratelimiter.Ratelimiter(allowance_per_period=bytes_per_second, period=1)
    else:
        limiter = None


    # Determine overwrite
    if destination.stat is not False:
        destination_modtime = destination.stat.st_mtime

        if overwrite_old is False:
            return [destination, 0]

        source_modtime = source.stat.st_mtime
        if source_modtime == destination_modtime:
            return [destination, 0]

    # Copy
    if dry_run:
        if callback is not None:
            callback(destination, 0, 0)
        return [destination, 0]

    source_bytes = source.size
    destination_location = os.path.split(destination.path)[0]
    if not os.path.exists(destination_location):
        os.makedirs(destination_location)
    written_bytes = 0

    try:
        source_file = open(source.path, 'rb')
        destination_file = open(destination.path, 'wb')
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

        if limiter is not None:
            limiter.limit(data_bytes)

        if callback is not None:
            callback(destination, written_bytes, source_bytes)

    # Fin
    source_file.close()
    destination_file.close()
    shutil.copystat(source.path, destination.path)
    return [destination, written_bytes]

def get_path_casing(path):
    '''
    Take what is perhaps incorrectly cased input and get the path's actual
    casing according to the filesystem.

    Thank you
    Ethan Furman http://stackoverflow.com/a/7133137/5430534
    xvorsx http://stackoverflow.com/a/14742779/5430534

    '''
    p = str_to_fp(path)
    path = p.path
    (drive, subpath) = os.path.splitdrive(path)
    pattern = ["%s[%s]" % (piece[:-1], piece[-1]) for piece in subpath.split(os.sep)[1:]]
    pattern = os.sep.join(pattern)
    pattern = drive.upper() + os.sep + pattern
    try:
        return str_to_fp(glob.glob(pattern)[0])
    except IndexError:
        return p

def get_dir_size(path):
    '''
    Calculate the total number of bytes across all files in this directory
    and its subdirectories.
    '''
    path = str_to_fp(path)

    if not path.isdir:
        raise SourceNotDirectory(path)

    total_bytes = 0
    for (directory, filename) in walk_generator(path):
        filename = os.path.join(directory, filename)
        filesize = os.path.getsize(filename)
        total_bytes += filesize

    return total_bytes

def is_subfolder(parent, child):
    '''
    Determine whether parent contains child.
    '''
    parent = normalize(str_to_fp(parent).path) + os.sep
    child = normalize(str_to_fp(child).path) + os.sep
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
    filepath = str_to_fp(filepath).path
    root = str_to_fp(root).path
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
    If `path` is a string, create a FilePath object, otherwise just return it.
    '''
    if isinstance(path, str):
        path = FilePath(path)
    return path

def walk_generator(
    path,
    exclude_directories=None,
    exclude_filenames=None,
    exclusion_callback=None,
    ):
    '''
    Yield (location, filename) from the file tree similar to os.walk.
    Example value: ('C:\\Users\\Michael\\Music', 'song.mp3')

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
    '''
    if exclude_directories is None:
        exclude_directories = set()

    if exclude_filenames is None:
        exclude_filenames = set()

    if exclusion_callback is None:
        exclusion_callback = lambda *x: None

    exclude_filenames = {normalize(f) for f in exclude_filenames}
    exclude_directories = {normalize(f) for f in exclude_directories}

    path = str_to_fp(path).path

    if normalize(path) in exclude_directories:
        exclusion_callback(path, 'directory')
        return

    if normalize(os.path.split(path)[1]) in exclude_directories:
        exclusion_callback(path, 'directory')
        return

    directory_queue = collections.deque()
    directory_queue.append(path)

    # This is a recursion-free workplace.
    # Thank you for your cooperation.
    while len(directory_queue) > 0:
        location = directory_queue.popleft()
        contents = os.listdir(location)

        directories = []
        for base_name in contents:
            absolute_name = os.path.join(location, base_name)

            if os.path.isdir(absolute_name):
                if normalize(absolute_name) in exclude_directories:
                    exclusion_callback(absolute_name, 'directory')
                    continue

                if normalize(base_name) in exclude_directories:
                    exclusion_callback(absolute_name, 'directory')
                    continue

                directories.append(absolute_name)

            else:
                if normalize(base_name) in exclude_filenames:
                    exclusion_callback(absolute_name, 'file')
                    continue
                if normalize(absolute_name) in exclude_filenames:
                    exclusion_callback(absolute_filename, 'file')
                    continue

                yield(str_to_fp(absolute_name))

        directories.reverse()
        directory_queue.extendleft(directories)
