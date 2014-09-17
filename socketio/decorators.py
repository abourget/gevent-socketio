from functools import partial
from socketio.server import SocketIOServer


class namespace(object):
    def __init__(self, name=''):
        self.name = name

    def __call__(self, handler):
        methods = [method for method in dir(handler) if callable(getattr(handler, method)) and method.startswith('on_')]
        ns = SocketIOServer.global_server.of(self.name)

        def register(socket):
            for m in methods:
                def listener(data):
                    method = getattr(handler, m)
                    method(socket, data)
                socket.on(m.lstrip('on_'), listener)

        ns.on('connect', register)