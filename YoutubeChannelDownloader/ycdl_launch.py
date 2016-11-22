import gevent.monkey
gevent.monkey.patch_all()

import ycdl_site
import gevent.pywsgi
import gevent.wsgi
import sys

if len(sys.argv) == 2:
    port = int(sys.argv[1])
else:
    port = 5000

if port == 443:
    http = gevent.pywsgi.WSGIServer(
        listener=('', port),
        application=ycdl_site.site,
        keyfile='https\\flasksite.key',
        certfile='https\\flasksite.crt',
    )
else:
    http = gevent.pywsgi.WSGIServer(
        listener=('', port),
        application=ycdl_site.site,
    )


print('Starting server')
http.serve_forever()
