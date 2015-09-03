import http.server

f = open('favicon.png', 'rb')
FAVI = f.read()
f.close()

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def write(self, string):
        if isinstance(string, str):
            string = string.encode('utf-8')
        self.wfile.write(string)

    def do_GET(self):
        #print(dir(self))
        print(self.path)
        if self.path == '/favicon.ico':
            self.write(FAVI)
        self.write('heyo')

server = http.server.HTTPServer(('', 80), RequestHandler)
print('server starting')
server.serve_forever()