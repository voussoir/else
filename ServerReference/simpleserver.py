import http.server
import mimetypes
import os
import urllib.parse
import random
import sys

sys.path.append('C:\\git\\else\\Bytestring')
import bytestring

sys.path.append('C:\\git\\else\\Ratelimiter')
import ratelimiter


f = open('favicon.png', 'rb')
FAVI = f.read()
f.close()
CWD = os.getcwd()

# The paths which the user may access
# Attempting to access anything outside will 403
OKAY_PATHS = set(x.lower() for x in ['/files', '/favicon.ico'])
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


class Multipart:
    def __init__(stream, boundary):
        self.parts = []

class Path:
    def __init__(self, path):
        path = path.replace('\\', '/')
        if len(path) == 0 or path[0] != '/':
            path = '/' + path
        self.path = path

    def __repr__(self):
        return 'Path(%s)' % self.path

    def __str__(self):
        return self.path

    def anchor(self, display_name=None):
        if display_name is None:
            display_name = self.basename
        if self.is_dir:
            # Folder emoji
            icon = '\U0001F4C1'
        else:
            # Diamond emoji, because there's not one for files.
            icon = '\U0001F48E'
        return '<a href="{full}">{icon} {display}</a>'.format(full=self.path, icon=icon, display=display_name)

    @property
    def basename(self):
        return os.path.basename(self.path)

    @property
    def is_dir(self):
        return os.path.isdir(self.os_path)

    @property
    def os_path(self):
        abspath = os.path.join(CWD, self.relative_path)
        #print(abspath)
        return abspath

    @property
    def parent(self):
        parts = self.path.split('/')[:-1]
        parts = '/'.join(parts)
        return Path(parts)

    @property
    def relative_path(self):
        return self.path.lstrip('/')

    @property
    def size(self):
        if self.is_dir:
            return -1
        return os.path.getsize(self.os_path)

    def table_row(self, display_name=None, shaded=False):
        form = '<tr style="background-color:#{bg}"><td>{anchor}</td><td>{size}</td></tr>'
        bg = 'ddd' if shaded else 'fff';
        size = bytestring.bytestring(self.size) if self.size != -1 else ''
        row = form.format(bg=bg, anchor=self.anchor(display_name=display_name), size=size)
        return row


class RequestHandler(http.server.BaseHTTPRequestHandler):
    def write(self, string):
        if isinstance(string, str):
            string = string.encode('utf-8')
        self.wfile.write(string)

    def read_filebytes(self, path):
        #print(path)
        if os.path.isfile(path.relative_path):
            f = open(path.relative_path, 'rb')
            fr = f.read()
            f.close()
            return fr

        if os.path.isdir(path.relative_path):
            text = generate_opendir(path)
            text = text.encode('utf-8')
            return text

        self.send_error(404)
        return bytes()

    def do_GET(self):
        #print(dir(self))
        path = self.path.lower()
        path = urllib.parse.unquote(path).rstrip('/')

        error = path_validation(path)
        if error:
            self.send_error(*error)
            return

        path = Path(path)

        self.send_response(200)
        mime = mimetypes.guess_type(path.path)[0]
        if mime is not None:
            #print(mime)
            self.send_header('Content-type', mime)
            self.end_headers()

        d = self.read_filebytes(path)
        self.write(d)

    # def do_POST(self):
    #     path = self.path.lower()
    #     path = urllib.parse.unquote(path).rstrip('/')

    #     error = path_validation(path)
    #     if error:
    #         self.send_error(*error)
    #         return

    #     path = Path(path)
    #     content_type = self.headers.get('Content-Type', '')
    #     if not any (req in content_type for req in ['multipart/form-data', 'boundary=']):
    #         self.send_error(400, 'Bad request')
    #         return

    #     boundary = content_type.split('boundary=')[1]
    #     boundary = boundary.split(';')[0]
    #     boundary = boundary.strip()
    #     print('B:', self.headers.get_boundary())
    #     print('F:', self.headers.get_filename())

    #     incoming_size = int(self.headers.get('Content-Length', 0))
    #     received_bytes = 0
    #     remaining_bytes = incoming_size
    #     while remaining_bytes > 0:
    #         chunk_size = min(remaining_bytes, 16*1024)
    #         chunk = self.rfile.read(chunk_size)
    #         remaining_bytes -= chunk_size
    #         received_bytes += chunk_size
    #         print(chunk)
    #     self.send_response(200)
    #     self.send_header('Content-Type', 'text/html')
    #     self.end_headers()
    #     print(dir(self.request))
    #     self.write('Thanks')

def generate_opendir(path):
    print('Listdir:', path)
    items = os.listdir(path.relative_path)
    items = [os.path.join(path.relative_path, f) for f in items]
    directories = []
    files = []
    for item in items:
        #item = item.lstrip('/')
        if os.path.isdir(item):
            directories.append(item)
        else:
            files.append(item)
    directories.sort(key=str.lower)
    files.sort(key=str.lower)
    files = directories + files
    #print(files)
    files = [Path(f) for f in files]
    entries = []
    if not any(okay == path.path for okay in OKAY_PATHS):
        # If the path actually equals a okay_path, then we shouldn't
        # let them step up because that would be outisde the okay area.
        entries.append(path.parent.table_row(display_name='up'))
    shaded = True
    for f in files:
        entry = f.table_row(shaded=shaded)
        entries.append(entry)
        shaded = not shaded
    entries = '\n'.join(entries)
    text = OPENDIR_TEMPLATE.format(entries=entries)
    return text

def generate_random_filename(original_filename='', length=8):
    import random
    bits = length * 4
    bits = random.getrandbits(bits)
    identifier = '{:x}'.format(bits).rjust(length, '0')
    return identifier

def path_validation(path):
    if '..' in path:
        return (403, 'I\'m not going to play games with you.')
    if not any(path.startswith(okay) for okay in OKAY_PATHS):
        self.send_error(403, 'Stop that!')
        return

server = http.server.HTTPServer(('', 32768), RequestHandler)
print('server starting')
server.serve_forever()
