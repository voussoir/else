import glob
import os
class Path:
    '''
    I started to use pathlib.Path, but it was too much of a pain.
    '''
    def __init__(self, path):
        path = os.path.normpath(path)
        path = os.path.abspath(path)
        self.absolute_path = path

    def __contains__(self, other):
        return other.absolute_path.startswith(self.absolute_path)

    def __eq__(self, other):
        return hasattr(other, 'absolute_path') and self.absolute_path == other.absolute_path

    def __hash__(self):
        return hash(self.absolute_path)

    def __repr__(self):
        return '{c}({path})'.format(c=self.__class__.__name__, path=repr(self.absolute_path))

    @property
    def basename(self):
        return os.path.basename(self.absolute_path)

    def correct_case(self):
        self.absolute_path = get_path_casing(self.absolute_path)
        return self.absolute_path

    @property
    def exists(self):
        return os.path.exists(self.absolute_path)

    @property
    def is_dir(self):
        return os.path.isdir(self.absolute_path)

    @property
    def is_file(self):
        return os.path.isfile(self.absolute_path)

    @property
    def is_link(self):
        return os.path.islink(self.absolute_path)

    @property
    def parent(self):
        parent = os.path.dirname(self.absolute_path)
        parent = self.__class__(parent)
        return parent

    @property
    def relative_path(self):
        relative = self.absolute_path
        relative = relative.replace(os.getcwd(), '')
        relative = relative.lstrip(os.sep)
        return relative

    @property
    def size(self):
        if self.is_file:
            return os.path.getsize(self.absolute_path)
        else:
            return None

    @property
    def stat(self):
        return os.stat(self.absolute_path)

def get_path_casing(path):
    '''
    Take what is perhaps incorrectly cased input and get the path's actual
    casing according to the filesystem.

    Thank you:
    Ethan Furman http://stackoverflow.com/a/7133137/5430534
    xvorsx http://stackoverflow.com/a/14742779/5430534
    '''
    if isinstance(path, Path):
        path = path.absolute_path

    (drive, subpath) = os.path.splitdrive(path)
    drive = drive.upper()
    subpath = subpath.lstrip(os.sep)

    pattern = [glob_patternize(piece) for piece in subpath.split(os.sep)]
    pattern = os.sep.join(pattern)
    pattern = drive + os.sep + pattern
    #print(pattern)
    try:
        return glob.glob(pattern)[0]
    except IndexError:
        return path

def glob_patternize(piece):
    '''
    Create a pattern like "[u]ser" from "user", forcing glob to look up the
    correct path name, while guaranteeing that the only result will be the correct path.

    Special cases are:
        !, because in glob syntax, [!x] tells glob to look for paths that don't contain
            "x". [!] is invalid syntax, so we pick the first non-! character to put
            in the brackets.
        [, because this starts a capture group
    '''
    piece = glob.escape(piece)
    for character in piece:
        if character not in '![]':
            replacement = '[%s]' % character
            #print(piece, character, replacement)
            piece = piece.replace(character, replacement, 1)
            break
    return piece
