from functools import partial
from socketio.server import SocketIOServer
import logging

logger = logging.getLogger(__name__)


class namespace(object):
    def __init__(self, name=''):
        self.name = name

    def __call__(self, handler):
        methods = [method for method in dir(handler) if callable(getattr(handler, method)) and method.startswith('on_')]
        if SocketIOServer.global_server is None:
            logger.warning('namespace decorator called but SocketIOServer not initialised')
            return
        ns = SocketIOServer.global_server.of(self.name)

        def register(socket):
            class Listener(object):
                    def __init__(self, handler, method, socket):
                        self.method = getattr(handler, m)
                        self.socket = socket

                    def __call__(self, data, *args, **kwargs):
                        self.method(socket, data)
            for m in methods:
                socket.on(m.lstrip('on_'), Listener(handler, m, socket))

        ns.on('connect', register)