import http.server
import os

f = open('favicon.png', 'rb')
FAVI = f.read()
f.close()

# The paths of the root folder which the user may access
# Attempting to access any other files in the root folder
# will 403
OKAY_BASE_PATHS = set(x.lower() for x in ['/', '/favicon.ico'])
FORBIDDEN_PATHS = set(x.lower() for x in ['/admin'])

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def write(self, string):
        if isinstance(string, str):
            string = string.encode('utf-8')
        self.wfile.write(string)

    def read_filebytes(self, path):
        #print(path)
        if os.path.isfile(path):
            f = open(path, 'rb')
            fr = f.read()
            f.close()
            return fr
        if os.path.isdir(path):
            return self.read_filebytes(os.path.join(path, 'index.html'))
        self.send_error(404)
        return b''

    def do_GET(self):
        #print(dir(self))
        path = self.path.lower()
        if os.path.dirname(path) in FORBIDDEN_PATHS:
            self.send_error(403, 'Forbidden path!')
            return            
        if path not in OKAY_BASE_PATHS and (os.path.dirname(path) == '/'):
            self.send_error(403, 'Stop that!')
            return
        path = os.path.join(os.getcwd(), path[1:])
        d = self.read_filebytes(path)
        self.write(d)

server = http.server.HTTPServer(('', 80), RequestHandler)
print('server starting')
server.serve_forever()