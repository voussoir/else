import argparse
import base64
import cgi
import http.cookies
import http.server
import math
import mimetypes
import os
import sys
import types
import urllib.parse
import zipstream

from voussoirkit import betterhelp
from voussoirkit import bytestring
from voussoirkit import gentools
from voussoirkit import passwordy
from voussoirkit import pathclass
from voussoirkit import ratelimiter

CHUNK_SIZE = bytestring.MIBIBYTE

OPENDIR_TEMPLATE = '''
<html>
<head>
<title>{title}</title>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<style type="text/css">
body {{font-family:Consolas;}}
.column_name {{word-break: break-all;}}
.column_size {{white-space: nowrap;}}
</style>
</head>

<body>
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
    <input type="text" autofocus autocapitalize="off" name="password" placeholder="password" autocomplete="off"/>
    <input type="hidden" name="goto" value="{goto}"/>
    <input type="submit" value="Submit"/>
</form>
</body>
</html>
'''

ROOT_DIRECTORY = pathclass.Path(os.getcwd())
HIDDEN_FILENAMES = {'thumbs.db', 'desktop.ini', '$recycle.bin', 'system volume information'}
TOKEN_COOKIE_NAME = 'simpleserver_token'

# SERVER ###########################################################################################

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, request, client_info, server, individual_ratelimit):
        self.individual_ratelimit = ratelimiter.Ratelimiter(individual_ratelimit)
        super().__init__(request, client_info, server)

    @property
    def auth_cookie(self):
        cookie = self.headers.get('Cookie')
        if not cookie:
            return None

        cookie = http.cookies.SimpleCookie(cookie)
        token = cookie.get(TOKEN_COOKIE_NAME)
        if not token:
            return None

        return token

    @property
    def auth_header(self):
        authorization = self.headers.get('Authorization')
        if not authorization:
            return None

        (auth_type, authorization) = authorization.split(' ', 1)
        if auth_type != 'Basic':
            return None

        authorization = base64.b64decode(authorization).decode()
        (username, password) = authorization.split(':', 1)
        return password

    @property
    def remote_addr(self):
        return self.request.getpeername()[0]

    def check_password(self, attempt):
        if self.server.password is None:
            return True

        if attempt == self.server.password:
            return True

        return False

    def check_has_password(self):
        if self.server.password is None:
            return True

        if self.auth_header == self.server.password:
            return True

        if self.server.accepted_tokens is not None and self.auth_cookie in self.server.accepted_tokens:
            return True

        if self.server.accepted_ips is not None and self.remote_addr in self.server.accepted_ips:
            return True

        return False

    def write(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')

        if isinstance(data, bytes):
            databytes = data
            data = (databytes[i*CHUNK_SIZE:(i+1)*CHUNK_SIZE] for i in range(math.ceil(len(data)/CHUNK_SIZE)))

        for chunk in data:
            self.wfile.write(chunk)
            chunksize = len(chunk)
            self.server.overall_ratelimit.limit(chunksize)
            self.individual_ratelimit.limit(chunksize)

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
            response = generate_opendir(path, enable_zip=self.server.enable_zip)
            response = response.encode('utf-8')

        elif self.path.endswith('.zip') and self.server.enable_zip:
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
        (ctype, pdict) = cgi.parse_header(self.headers.get('content-type'))
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
                self.send_response(302)

                if self.server.accepted_tokens is not None:
                    cookie = http.cookies.SimpleCookie()
                    token = passwordy.random_hex(32)
                    cookie[TOKEN_COOKIE_NAME] = token
                    self.server.accepted_tokens.add(token)
                    self.send_header('Set-Cookie', cookie.output(header='', sep=''))
                if self.server.accepted_ips is not None:
                    self.server.accepted_ips.add(self.remote_addr)

                self.send_header('Location', goto)
            else:
                self.send_response(401)
        elif not self.check_has_password():
            self.send_response(401)
            self.end_headers()
            return
        else:
            self.send_response(400)
        self.end_headers()

    def send_path_validation_error(self, path):
        if not allowed(path):
            self.send_error(403, 'Stop that!')
            return True
        return False

class SimpleServer:
    def __init__(
            self,
            port,
            *,
            password,
            authorize_by_ip,
            enable_zip,
            overall_ratelimit,
            individual_ratelimit,
        ):
        self.port = port
        self.password = password
        self.authorize_by_ip = authorize_by_ip
        self.enable_zip = enable_zip
        self.overall_ratelimit = ratelimiter.Ratelimiter(overall_ratelimit)
        self.individual_ratelimit = individual_ratelimit

        if authorize_by_ip:
            self.accepted_ips = set()
            self.accepted_tokens = None
        else:
            self.accepted_tokens = set()
            self.accepted_ips = None

    def make_request_handler(self, request, client_info, _server):
        # We ignore the given _server and use self instead because _server will
        # be the ThreadingHTTPServer instance.
        return RequestHandler(request, client_info, self, individual_ratelimit=self.individual_ratelimit)

    def start(self):
        server = http.server.ThreadingHTTPServer(('0.0.0.0', self.port), self.make_request_handler)
        print(f'Server starting on {self.port}')
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('Goodbye.')
            server.shutdown()


# HELPERS ##########################################################################################

def allowed(path):
    return path == ROOT_DIRECTORY or path in ROOT_DIRECTORY

def atag(path, display_name=None):
    if display_name is None:
        display_name = path.basename

    if path.is_dir:
        # Folder emoji
        icon = '\U0001F4C1'
    else:
        # Gift emoji
        icon = '\U0001F381'

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

def generate_opendir(path, enable_zip):
    try:
        path.correct_case()
        items = path.listdir()
    except FileNotFoundError:
        items = []

    # This places directories above files, each ordered alphabetically
    directories = []
    files = []

    for item in sorted(items, key=lambda p: p.basename.lower()):
        if item.basename.lower() in HIDDEN_FILENAMES:
            continue
        if item.is_dir:
            directories.append(item)
        else:
            files.append(item)

    items = directories + files
    table_rows = []

    shaded = False

    is_root = path.absolute_path == ROOT_DIRECTORY.absolute_path
    if is_root:
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

    if len(items) > 0 and enable_zip:
        entry = table_row(path.replace_extension('.zip'), display_name='zip', shaded=shaded)
        shaded = not shaded
        table_rows.append(entry)

    table_rows = '\n'.join(table_rows)
    title = '/' if is_root else path.basename
    text = OPENDIR_TEMPLATE.format(title=title, table_rows=table_rows)
    return text

def read_filebytes(path, range_min=None, range_max=None):
    if range_min is None:
        range_min = 0

    if range_max is None:
        range_max = path.size

    range_span = range_max - range_min

    f = path.open('rb')
    f.seek(range_min)
    sent_amount = 0
    while sent_amount < range_span:
        chunk = f.read(CHUNK_SIZE)
        if len(chunk) == 0:
            break

        yield chunk
        sent_amount += len(chunk)

    f.close()

def table_row(path, display_name=None, shaded=False):
    form = '''
    <tr style="background-color:#{bg}">
    <td class="column_name">{anchor}</td>
    <td class="column_size">{size}</td></tr>
    '''.replace('\n', ' ')
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
    url = path.relative_to(ROOT_DIRECTORY, simple=True)
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

# COMMAND LINE #####################################################################################

DOCSTRING = '''
simpleserver
============

Run a simple file server from your computer.

> simpleserver port <flags>

port:
    Port number, an integer.

flags:
--password X:
    A password string. The user will be prompted to enter it before proceeding
    to any URL. A token is stored in a cookie unless authorize_by_ip is used.

--authorize_by_ip:
    After the user enters the password, their entire IP becomes authorized for
    all future requests. This reduces security, because a single IP can be home
    to many different people, but increases convenience, because the user can
    use download managers / scripts where adding auth is not convenient.

--enable_zip:
    Add a 'zip' link to every directory and allow the user to download the
    entire directory as a zip file.

--overall_ratelimit X:
    An integer number of bytes, the maximum bytes/sec of the server overall.

--individual_ratelimit X:
    An integer number of bytes, the maximum bytes/sec for any single request.
'''

def simpleserver_argparse(args):
    server = SimpleServer(
        port=args.port,
        password=args.password,
        authorize_by_ip=args.authorize_by_ip,
        enable_zip=args.enable_zip,
        overall_ratelimit=args.overall_ratelimit,
        individual_ratelimit=args.individual_ratelimit,
    )
    server.start()

def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('port', nargs='?', type=int, default=40000)
    parser.add_argument('--password', dest='password', default=None)
    parser.add_argument('--authorize_by_ip', '--authorize-by-ip', dest='authorize_by_ip', action='store_true')
    parser.add_argument('--enable_zip', '--enable-zip', dest='enable_zip', action='store_true')
    parser.add_argument('--overall_ratelimit', '--overall-ratelimit', type=bytestring.parsebytes, default=20*bytestring.MIBIBYTE)
    parser.add_argument('--individual_ratelimit', '--individual-ratelimit', type=bytestring.parsebytes, default=10*bytestring.MIBIBYTE)
    parser.set_defaults(func=simpleserver_argparse)

    return betterhelp.single_main(argv, parser, DOCSTRING)

if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
