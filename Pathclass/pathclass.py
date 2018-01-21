import glob
import os
import re

class Path:
    '''
    I started to use pathlib.Path, but it was too much of a pain.
    '''
    def __init__(self, path):
        if isinstance(path, Path):
            self.absolute_path = path.absolute_path
        else:
            path = path.strip()
            if re.search('[A-Za-z]:$', path):
                # Bare Windows drive letter.
                path += os.sep
            path = normalize_sep(path)
            path = os.path.normpath(path)
            path = os.path.abspath(path)
            self.absolute_path = path

    def __contains__(self, other):
        if isinstance(other, Path):
            other = other.normcase
        return other.startswith(self.normcase)

    def __eq__(self, other):
        if not hasattr(other, 'absolute_path'):
            return False
        return self.normcase == other.normcase

    def __hash__(self):
        return hash(self.normcase)

    def __repr__(self):
        return '{c}({path})'.format(c=self.__class__.__name__, path=repr(self.absolute_path))

    @property
    def basename(self):
        return os.path.basename(self.absolute_path)

    def correct_case(self):
        self.absolute_path = get_path_casing(self.absolute_path)
        return self.absolute_path

    @property
    def depth(self):
        return len(self.absolute_path.split(os.sep))

    @property
    def exists(self):
        return os.path.exists(self.absolute_path)

    @property
    def extension(self):
        return os.path.splitext(self.absolute_path)[1].lstrip('.')

    @property
    def is_dir(self):
        return os.path.isdir(self.absolute_path)

    @property
    def is_file(self):
        return os.path.isfile(self.absolute_path)

    @property
    def is_link(self):
        return os.path.islink(self.absolute_path)

    def join(self, subpath):
        if not isinstance(subpath, str):
            raise TypeError('subpath must be a string')
        return Path(os.path.join(self.absolute_path, subpath))

    def listdir(self):
        children = os.listdir(self.absolute_path)
        children = [self.with_child(child) for child in children]
        return children

    @property
    def normcase(self):
        return os.path.normcase(self.absolute_path)

    @property
    def parent(self):
        parent = os.path.dirname(self.absolute_path)
        parent = self.__class__(parent)
        return parent

    @property
    def relative_path(self):
        cwd = Path(os.getcwd())
        cwd.correct_case()
        self.correct_case()
        if self == cwd:
            return '.'

        if self in cwd:
            return self.absolute_path.replace(cwd.absolute_path, '.')

        common = common_path([os.getcwd(), self.absolute_path], fallback=None)
        if common is None:
            return self.absolute_path
        backsteps = cwd.depth - common.depth
        backsteps = os.sep.join('..' for x in range(backsteps))
        return self.absolute_path.replace(common.absolute_path, backsteps)

    def replace_extension(self, extension):
        extension = extension.rsplit('.', 1)[-1]
        base = os.path.splitext(self.absolute_path)[0]

        if extension == '':
            return Path(base)

        return Path(base + '.' + extension)

    @property
    def size(self):
        if self.is_file:
            return os.path.getsize(self.absolute_path)
        else:
            return None

    @property
    def stat(self):
        return os.stat(self.absolute_path)

    def with_child(self, basename):
        return self.join(os.path.basename(basename))



def common_path(paths, fallback):
    '''
    Given a list of file paths, determine the deepest path which all
    have in common.
    '''
    if isinstance(paths, (str, Path)):
        raise TypeError('`paths` must be a collection')
    paths = [Path(f) for f in paths]

    if len(paths) == 0:
        raise ValueError('Empty list')

    if hasattr(paths, 'pop'):
        model = paths.pop()
    else:
        model = paths[0]
        paths = paths[1:]

    while True:
        if all(f in model for f in paths):
            return model
        parent = model.parent
        if parent == model:
            # We just processed the root, and now we're stuck at the root.
            # Which means there was no common path.
            return fallback
        model = parent

def get_path_casing(path):
    '''
    Take what is perhaps incorrectly cased input and get the path's actual
    casing according to the filesystem.

    Thank you:
    Ethan Furman http://stackoverflow.com/a/7133137/5430534
    xvorsx http://stackoverflow.com/a/14742779/5430534
    '''
    if not isinstance(path, Path):
        path = Path(path)

    # Nonexistent paths don't glob correctly. If the input is a nonexistent
    # subpath of an existing path, we have to glob the existing portion first,
    # and then attach the fake portion again at the end.
    input_path = path
    while not path.exists:
        parent = path.parent
        if path == parent:
            # We're stuck at a fake root.
            return input_path.absolute_path
        path = parent

    path = path.absolute_path

    (drive, subpath) = os.path.splitdrive(path)
    drive = drive.upper()
    subpath = subpath.lstrip(os.sep)

    pattern = [glob_patternize(piece) for piece in subpath.split(os.sep)]
    pattern = os.sep.join(pattern)
    pattern = drive + os.sep + pattern

    try:
        cased = glob.glob(pattern)[0]
    except IndexError:
        return input_path.absolute_path

    imaginary_portion = input_path.absolute_path
    imaginary_portion = imaginary_portion[len(cased):]
    #real_portion = os.path.normcase(cased)
    #imaginary_portion = imaginary_portion.replace(real_portion, '')
    imaginary_portion = imaginary_portion.lstrip(os.sep)
    cased = os.path.join(cased, imaginary_portion)
    cased = cased.rstrip(os.sep)
    if not os.sep in cased:
        cased += os.sep
    return cased

def glob_patternize(piece):
    '''
    Create a pattern like "[u]ser" from "user", forcing glob to look up the
    correct path name, while guaranteeing that the only result will be the correct path.

    Special cases are:
        `!`
            because in glob syntax, [!x] tells glob to look for paths that don't contain
            "x", and [!] is invalid syntax.
        `[`, `]`
            because this starts a glob capture group

        so we pick the first non-special character to put in the brackets.
        If the path consists entirely of these special characters, then the
        casing doesn't need to be corrected anyway.
    '''
    piece = glob.escape(piece)
    for character in piece:
        if character not in '![]':
            replacement = '[%s]' % character
            #print(piece, character, replacement)
            piece = piece.replace(character, replacement, 1)
            break
    return piece

def normalize_sep(path):
    for char in ('\\', '/'):
        if char != os.sep:
            path = path.replace(char, os.sep)
    return path

def system_root():
    return os.path.abspath(os.sep)
