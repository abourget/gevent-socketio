from gevent import monkey; monkey.patch_all()
from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace
from socketio.mixins import RoomsMixin, BroadcastMixin


class ChatNamespace(BaseNamespace, RoomsMixin, BroadcastMixin):
    def on_nickname(self, nickname):
        self.environ['nicknames'].append(nickname)
        self.socket.session = nickname
        self.broadcast_event('anouncement', '%s has connected' % nickname)
        self.broadcast_event('nicknames', self.environ['nicknames'])

    def on_user_message(self, room_name, msg):
        self.emit_to_room('msg_to_room', room_name, msg)

    def recv_message(self, message):
        print "PING!!!", message


class Application(object):
    def __init__(self):
        self.buffer = []

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO'].strip('/')
        environ['nicknames'] = []

        if not path:
            start_response('200 OK', [('Content-Type', 'text/html')])
            return ['<h1>Welcome. '
                'Try the <a href="/chat.html">chat</a> example.</h1>']

        if path in ['socket.io.js', 'chat.html', 'stylesheets/style.css']:
            try:
                data = open(path).read()
            except Exception:
                return not_found(start_response)

            if path.endswith(".js"):
                content_type = "text/javascript"
            elif path.endswith(".css"):
                content_type = "text/css"
            else:
                content_type = "text/html"

            start_response('200 OK', [('Content-Type', content_type)])
            return [data]

        if path.startswith("socket.io"):
            socketio_manage(environ, {'': ChatNamespace})
        else:
            return not_found(start_response)


def not_found(start_response):
    start_response('404 Not Found', [])
    return ['<h1>Not Found</h1>']


if __name__ == '__main__':
    print 'Listening on port 8080 and on port 843 (flash policy server)'
    SocketIOServer(('127.0.0.1', 8080), Application(),
        namespace="socket.io", policy_server=False).serve_forever()
