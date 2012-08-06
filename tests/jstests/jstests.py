from gevent import monkey; monkey.patch_all()

from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace


TestHtml = """
<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <title>Gevent-socketio Tests</title>
  <link rel="stylesheet" href="/static/qunit.css">
  <script>WEB_SOCKET_SWF_LOCATION="/static/WebSocketMain.swf";</script>
</head>
<body>
  <div id="qunit"></div>
  <script src="/static/qunit.js"></script>
  <script src="/static/socket.io.js"></script>
  <script src="/tests/suite.js"></script>
</body>
</html>
"""

class TestNamespace(BaseNamespace):
    def on_requestack(self, val):
        return val, "ack"

class Application(object):
    def __init__(self):
        self.buffer = []
        
    def __call__(self, environ, start_response):
        path = environ['PATH_INFO'].strip('/')

        if not path:
            start_response('200 OK', [('Content-Type', 'text/html')])
            return [TestHtml]

        if path.startswith('static/') or path.startswith('tests/'):
            try:
                data = open(path).read()
            except Exception:
                return not_found(start_response)

            if path.endswith(".js"):
                content_type = "text/javascript"
            elif path.endswith(".css"):
                content_type = "text/css"
            elif path.endswith(".swf"):
                content_type = "application/x-shockwave-flash"
            else:
                content_type = "text/html"

            start_response('200 OK', [('Content-Type', content_type)])
            return [data]

        if path.startswith("socket.io"):
            socketio_manage(environ, {'/test': TestNamespace})
        else:
            return not_found(start_response)


def not_found(start_response):
    start_response('404 Not Found', [])
    return ['<h1>Not Found</h1>']


if __name__ == '__main__':
    print 'Listening on port 8080 and on port 10843 (flash policy server)'
    SocketIOServer(('0.0.0.0', 8080), Application(), resource="socket.io", policy_server=True).serve_forever()
