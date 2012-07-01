from gevent import monkey; monkey.patch_all()
import gevent

from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin


class CPUNamespace(BaseNamespace, BroadcastMixin):
    def recv_connect(self):
        def sendcpu():
            prev = None
            while True:
                vals = map(int, [x for x in open('/proc/stat').readlines()
                                 if x.startswith('cpu ')][0].split()[1:5])
                if prev:
                    percent = (100.0 * (sum(vals[:3]) - sum(prev[:3])) /
                               (sum(vals) - sum(prev)))
                    self.emit('cpu_data', {'point': percent})
                prev = vals
                gevent.sleep(0.5)
        self.spawn(sendcpu)


class Application(object):
    def __init__(self):
        self.buffer = []

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO'].strip('/') or 'index.html'

        if path.startswith('static/') or path == 'index.html':
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
            socketio_manage(environ, {'/cpu': CPUNamespace})
        else:
            return not_found(start_response)


def not_found(start_response):
    start_response('404 Not Found', [])
    return ['<h1>Not Found</h1>']


if __name__ == '__main__':
    print 'Listening on port 8080 and on port 843 (flash policy server)'
    SocketIOServer(('0.0.0.0', 8080), Application(),
        namespace="socket.io", policy_server=True,
        policy_listener=('0.0.0.0', 843)).serve_forever()
