import http.server
import mimetypes
import os
import urllib.parse
import pathlib
import random
import socketserver
import sys
import types

sys.path.append('C:\\git\\else\\Bytestring'); import bytestring
sys.path.append('C:\\git\\else\\Ratelimiter'); import ratelimiter
sys.path.append('C:\\git\\else\\SpinalTap'); import spinal

FILE_READ_CHUNK = bytestring.MIBIBYTE

#f = open('favicon.png', 'rb')
#FAVI = f.read()
#f.close()
CWD = os.getcwd()

# The paths which the user may access.
# Attempting to access anything outside will 403.
# These are convered to Path objects after that class definition.
OKAY_PATHS = set(['files', 'favicon.ico'])

OPENDIR_TEMPLATE = '''
<html>
<body>
<meta charset="UTF-8">
<style type="text/css">Body {{font-family:Consolas}}</style>
<table style="width: 95%">
{entries}
</table>

</body>
</html>
'''

class Path:
    '''
    I started to use pathlib.Path, but it was too much of a pain.
    '''
    def __init__(self, path):
        path = urllib.parse.unquote(path)
        path = path.strip('/')
        path = os.path.normpath(path)
        path = spinal.get_path_casing(path).path
        self.absolute_path = path

    def __contains__(self, other):
        return other.absolute_path.startswith(self.absolute_path)

    def __hash__(self):
        return hash(self.absolute_path)

    @property
    def allowed(self):
        return any(self in okay for okay in OKAY_PATHS)

    def anchor(self, display_name=None):
        if display_name is None:
            display_name = self.basename

        if self.is_dir:
            # Folder emoji
            icon = '\U0001F4C1'
        else:
            # Diamond emoji, because there's not one for files.
            icon = '\U0001F48E'

        #print('anchor', path)
        a = '<a href="{full}">{icon} {display}</a>'.format(
            full=self.url_path,
            icon=icon,
            display=display_name,
            )
        return a

    @property
    def basename(self):
        return os.path.basename(self.absolute_path)

    @property
    def is_dir(self):
        return os.path.isdir(self.absolute_path)

    @property
    def is_file(self):
        return os.path.isfile(self.absolute_path)

    @property
    def parent(self):
        parent = os.path.dirname(self.absolute_path)
        parent = Path(parent)
        return parent

    @property
    def relative_path(self):
        relative = self.absolute_path
        relative = relative.replace(CWD, '')
        relative = relative.lstrip(os.sep)
        return relative

    @property
    def size(self):
        if self.is_file:
            return os.path.getsize(self.absolute_path)
        else:
            return None

    def table_row(self, display_name=None, shaded=False):
        form = '<tr style="background-color:#{bg}"><td style="width:90%">{anchor}</td><td>{size}</td></tr>'
        size = self.size
        if size is None:
            size = ''
        else:
            size = bytestring.bytestring(size)

        bg = 'ddd' if shaded else 'fff';
        row = form.format(
            bg=bg,
            anchor=self.anchor(display_name=display_name),
            size=size,
            )
        return row

    @property
    def url_path(self):
        url = self.relative_path
        url = url.replace(os.sep, '/')
        url = '/' + url
        url = urllib.parse.quote(url)
        return url

OKAY_PATHS = set(Path(p) for p in OKAY_PATHS)

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def write(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        if isinstance(data, types.GeneratorType):
            for chunk in data:
                self.wfile.write(chunk)
        else:
            self.wfile.write(data)

    def read_filebytes(self, path, range_min=None, range_max=None):
        #print(path)

        if path.is_file:
            if range_min is None:
                range_min = 0

            if range_max is None:
                range_max = path.size

            range_span = range_max - range_min

            #print('read span', range_min, range_max, range_span)
            f = open(path.absolute_path, 'rb')
            f.seek(range_min)
            sent_amount = 0
            while sent_amount < range_span:
                chunk = f.read(FILE_READ_CHUNK)
                if len(chunk) == 0:
                    break

                yield chunk
                sent_amount += len(chunk)

            #print('I read', len(fr))
            f.close()

        elif path.is_dir:
            text = generate_opendir(path)
            text = text.encode('utf-8')
            yield text

        else:
            self.send_error(404)
            yield bytes()

    def do_GET(self):
        #print(dir(self))
        path = Path(self.path)
        if self.send_path_validation_error(path):
            return

        range_min = None
        range_max = None

        status_code = 200
        headers = {}

        if path.is_file:
            file_size = path.size
            if 'range' in self.headers:
                desired_range = self.headers['range']
                desired_range = desired_range.lower()
                desired_range = desired_range.split('bytes=')[-1]

                helper = lambda x: int(x) if x and x.isdigit() else None
                if '-' in desired_range:
                    (desired_min, desired_max) = desired_range.split('-')
                    #print('desire', desired_min, desired_max)
                    range_min = helper(desired_min)
                    range_max = helper(desired_max)
                else:
                    range_min = helper(desired_range)

                if range_min is None:
                    range_min = 0
                if range_max is None:
                    range_max = file_size

                # because ranges are 0 indexed
                range_max = min(range_max, file_size - 1)
                range_min = max(range_min, 0)

                status_code = 206
                range_header = 'bytes {min}-{max}/{outof}'.format(
                    min=range_min,
                    max=range_max,
                    outof=file_size,
                )
                headers['Content-Range'] = range_header
                headers['Accept-Ranges'] = 'bytes'
                content_length = (range_max - range_min) + 1

            else:
                content_length = file_size

            headers['Content-length'] = content_length

        mime = mimetypes.guess_type(path.absolute_path)[0]
        if mime is not None:
            #print(mime)
            headers['Content-type'] = mime

        self.send_response(status_code)
        for (key, value) in headers.items():
            self.send_header(key, value)

        d = self.read_filebytes(path, range_min=range_min, range_max=range_max)
        #print('write')
        self.end_headers()
        self.write(d)

    def do_HEAD(self):
        path = Path(self.path)
        if self.send_path_validation_error(path):
            return

        status_code = 200

        if path.is_dir:
            mime = 'text/html'
        else:
            mime = mimetypes.guess_type(path.absolute_path)[0]
            self.send_header('Content-length', path.size)

        if mime is not None:
            self.send_header('Content-type', mime)

        self.send_response(status_code)
        self.end_headers()

    def send_path_validation_error(self, path):
        if not path.allowed:
            self.send_error(403, 'Stop that!')
            return True
        return False


class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    '''
    Thanks root and twasbrillig http://stackoverflow.com/a/14089457
    '''
    pass


def generate_opendir(path):
    #print('Listdir:', path)
    items = os.listdir(path.absolute_path)
    items = [os.path.join(path.absolute_path, f) for f in items]
    #print(items)

    # This places directories above files, each ordered alphabetically
    items.sort(key=str.lower)
    directories = []
    files = []
    for item in items:
        if os.path.isdir(item):
            directories.append(item)
        else:
            files.append(item)

    items = directories + files
    items = [Path(f) for f in items]
    entries = []

    if any(path.absolute_path == okay.absolute_path for okay in OKAY_PATHS):
        # This is different than a permission check, we're seeing if they're
        # actually at the top, in which case they don't need an up button.
        pass
    else:
        entry = path.parent.table_row(display_name='up')
        entries.append(entry)

    shaded = True
    for item in items:
        entry = item.table_row(shaded=shaded)
        entries.append(entry)
        shaded = not shaded

    entries = '\n'.join(entries)
    text = OPENDIR_TEMPLATE.format(entries=entries)
    return text

def generate_random_filename(original_filename='', length=8):
    import random
    bits = length * 44
    bits = random.getrandbits(bits)
    identifier = '{:x}'.format(bits).rjust(length, '0')
    return identifier

def main():
    server = ThreadedServer(('', 32768), RequestHandler)
    print('server starting')
    server.serve_forever()

if __name__ == '__main__':
    main()
