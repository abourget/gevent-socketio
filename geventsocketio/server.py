from gevent.pywsgi import WSGIServer
from geventsocketio.protocol import SocketIOProtocol


class SocketIOServer(WSGIServer):
    def __init__(self, *args, **kwargs):
        self.sessions = {}
        super(SocketIOServer, self).__init__(*args, **kwargs)

    def handle(self, socket, address):
        handler = self.handler_class(socket, address, self)
        self.set_environ({'socketio': SocketIOProtocol(handler)})
        handler.handle()
