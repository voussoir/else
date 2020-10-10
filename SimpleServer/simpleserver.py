import argparse
import cgi
import http.cookies
import http.server
import math
import mimetypes
import os
import pathlib
import random
import socketserver
import sys
import threading
import types
import urllib.parse
import zipstream

# pip install voussoirkit
from voussoirkit import bytestring
from voussoirkit import pathclass
from voussoirkit import ratelimiter

FILE_READ_CHUNK = bytestring.MIBIBYTE
RATELIMITER = ratelimiter.Ratelimiter(16 * bytestring.MIBIBYTE)

OPENDIR_TEMPLATE = '''
<html>
<body>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<style type="text/css">Body {{font-family:Consolas}}</style>
<table style="width: 100%">
{table_rows}
</table>

</body>
</html>
'''

PASSWORD_PROMPT_HTML = '''
<html>
<body>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<style type="text/css">Body {{font-family:Consolas}}</style>

<form action="/password" method="post">
    <input type="text" name="password" placeholder="password" autocomplete="off"/>
    <input type="hidden" name="goto" value="{goto}"/>
    <input type="submit" value="Submit"/>
</form>
</body>
</html>
'''

ROOT_DIRECTORY = pathclass.Path(os.getcwd())
TOKEN_COOKIE_NAME = 'simpleserver_token'

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, passw=None, accepted_tokens=None, **kwargs):
        self.accepted_tokens = accepted_tokens
        self.password = passw
        super().__init__(*args, **kwargs)

    def check_password(self, attempt):
        if self.password is None:
            return True

        if attempt == self.password:
            return True

        return False

    def check_has_password(self):
        if self.password is None:
            return True

        if self.headers.get('password', None) == self.password:
            return True

        if self.headers.get('Cookie'):
            cookie = http.cookies.SimpleCookie()
            cookie.load(self.headers.get('Cookie'))
            token = cookie.get(TOKEN_COOKIE_NAME)
            if token and token.value in self.accepted_tokens:
                return True

        return False

    def write(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        if isinstance(data, types.GeneratorType):
            for chunk in data:
                self.wfile.write(chunk)
                RATELIMITER.limit(len(chunk))
        else:
            self.wfile.write(data)

    def do_GET(self):
        if not self.check_has_password():
            self.send_response(401)
            self.end_headers()
            self.write(PASSWORD_PROMPT_HTML.format(goto=self.path))
            return

        path = url_to_path(self.path)
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

        if path.is_file:
            headers['Content-type'] = mimetypes.guess_type(path.absolute_path)[0]
            response = read_filebytes(path, range_min=range_min, range_max=range_max)

        elif path.is_dir:
            headers['Content-type'] = 'text/html'
            response = generate_opendir(path)
            response = response.encode('utf-8')

        elif self.path.endswith('.zip'):
            path = url_to_path(self.path.rsplit('.zip', 1)[0])
            headers['Content-type'] = 'application/octet-stream'
            download_as = urllib.parse.quote(path.basename)
            download_as += '.zip'
            headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{download_as}'
            response = zip_directory(path)
            response = iter(response)
            # response = (print(chunk) or chunk for chunk in response)

        else:
            status_code = 404
            self.send_error(status_code)
            response = bytes()

        self.send_response(status_code)
        for (key, value) in headers.items():
            self.send_header(key, value)

        self.end_headers()
        self.write(response)

    def do_HEAD(self):
        if not self.check_has_password():
            self.send_response(401)
            self.end_headers()
            return

        path = url_to_path(self.path)
        if self.send_path_validation_error(path):
            return

        status_code = 200
        self.send_response(status_code)

        if path.is_dir:
            mime = 'text/html'
        else:
            mime = mimetypes.guess_type(path.absolute_path)[0]
            self.send_header('Content-length', path.size)

        if mime is not None:
            self.send_header('Content-type', mime)

        self.end_headers()

    def do_POST(self):
        ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
        if ctype == 'multipart/form-data':
            form = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers.get('content-length'))
            form = urllib.parse.parse_qs(self.rfile.read(length), keep_blank_values=1)
        else:
            form = {}

        if self.path == '/password':
            attempt = form.get(b'password')[0].decode('utf-8')
            goto = form.get(b'goto')[0].decode('utf-8')
            if self.check_password(attempt):
                cookie = http.cookies.SimpleCookie()
                token = random_hex(32)
                cookie[TOKEN_COOKIE_NAME] = token
                self.accepted_tokens.add(token)

                self.send_response(302)
                self.send_header('Set-Cookie', cookie.output(header='', sep=''))
                self.send_header('Location', goto)
            else:
                self.send_response(401)
        else:
            self.send_response(400)
        self.end_headers()

    def send_path_validation_error(self, path):
        if not allowed(path):
            self.send_error(403, 'Stop that!')
            return True
        return False


def allowed(path):
    return path == ROOT_DIRECTORY or path in ROOT_DIRECTORY

def atag(path, display_name=None):
    path.correct_case()
    if display_name is None:
        display_name = path.basename

    if path.is_dir:
        # Folder emoji
        icon = '\U0001F4C1'
    else:
        # Diamond emoji
        #icon = '\U0001F48E'
        icon = '\U0001F381'

    #print('anchor', path)
    if display_name.endswith('.placeholder'):
        a = '<a>{icon} {display}</a>'
    else:
        a = '<a href="{full}">{icon} {display}</a>'
    a = a.format(
        full=path_to_url(path),
        icon=icon,
        display=display_name,
    )
    return a

def generate_opendir(path):
    #print('Listdir:', path)

    # This places directories above files, each ordered alphabetically
    try:
        items = path.listdir()
    except FileNotFoundError:
        items = []

    directories = []
    files = []

    for item in sorted(items, key=lambda p: p.basename.lower()):
        if item.is_dir:
            directories.append(item)
        else:
            if item.basename.lower() == 'thumbs.db':
                continue
            if item.basename.lower() == 'desktop.ini':
                continue
            files.append(item)

    items = directories + files
    table_rows = []

    shaded = False

    if path.absolute_path == ROOT_DIRECTORY.absolute_path:
        # This is different than a permission check, we're seeing if they're
        # actually at the top, in which case they don't need an up button.
        entry = table_row(path, display_name='.', shaded=shaded)
        table_rows.append(entry)
        shaded = not shaded
    else:
        entry = table_row(path.parent, display_name='up', shaded=shaded)
        table_rows.append(entry)
        shaded = not shaded

    for item in items:
        entry = table_row(item, shaded=shaded)
        table_rows.append(entry)
        shaded = not shaded

    if len(items) > 0:
        entry = table_row(path.replace_extension('.zip'), display_name='zip', shaded=shaded)
        shaded = not shaded
        table_rows.append(entry)

    table_rows = '\n'.join(table_rows)
    text = OPENDIR_TEMPLATE.format(table_rows=table_rows)
    return text

def generate_random_filename(original_filename='', length=8):
    import random
    bits = length * 44
    bits = random.getrandbits(bits)
    identifier = '{:x}'.format(bits).rjust(length, '0')
    return identifier

def random_hex(length=12):
    randbytes = os.urandom(math.ceil(length / 2))
    token = ''.join('{:02x}'.format(x) for x in randbytes)
    token = token[:length]
    return token

def read_filebytes(path, range_min=None, range_max=None):
    #print(path)
    if range_min is None:
        range_min = 0

    if range_max is None:
        range_max = path.size

    range_span = range_max - range_min

    #print('read span', range_min, range_max, range_span)
    f = path.open('rb')
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

def table_row(path, display_name=None, shaded=False):
    form = '<tr style="background-color:#{bg}"><td style="">{anchor}</td><td>{size}</td></tr>'
    if path.is_file:
        size = bytestring.bytestring(path.size)
    else:
        size = ''

    bg = 'ddd' if shaded else 'fff'

    anchor = atag(path, display_name=display_name)

    row = form.format(
        bg=bg,
        anchor=anchor,
        size=size,
        )
    return row

def path_to_url(path):
    url = path.relative_path[2:]
    url = url.replace(os.sep, '/')
    url = '/' + url
    url = urllib.parse.quote(url)
    return url

def url_to_path(path):
    path = urllib.parse.unquote(path)
    path = path.strip('/')
    return pathclass.Path(path)

def zip_directory(path):
    zipfile = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_STORED)

    for item in path.walk():
        if item.is_dir:
            continue
        arcname = item.relative_to(path).lstrip('.' + os.sep)
        zipfile.write(filename=item.absolute_path, arcname=arcname)

    return zipfile

def RRR(password=None):
    accepted_tokens = set()
    def R(*args, **kwargs):
        handler = RequestHandler(passw=password, accepted_tokens=accepted_tokens, *args, **kwargs)
        return handler

    return R

def simpleserver(port, password=None):
    server = http.server.ThreadingHTTPServer(('', port), RRR(password=password))
    print(f'server starting on {port}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('goodbye.')
        t = threading.Thread(target=server.shutdown)
        t.daemon = True
        t.start()
        server.shutdown()
        print('really goodbye.')
        return 0

def simpleserver_argparse(args):
    return simpleserver(
        port=args.port,
        password=args.password,
    )

def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('port', nargs='?', type=int, default=40000)
    parser.add_argument('--password', dest='password', default=None)
    parser.set_defaults(func=simpleserver_argparse)

    args = parser.parse_args(argv)
    return args.func(args)

if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
