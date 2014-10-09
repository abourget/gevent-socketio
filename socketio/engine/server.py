from __future__ import absolute_import

from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
from .handler import EngineHandler
import logging

__all__ = ['Server']

logger = logging.getLogger(__name__)


class Server(WSGIServer):
    """
    EngineIO Server holds all opened sockets
    """
    ws_handler_class = WebSocketHandler
    config = {
        'heartbeat_timeout': 60,
        'close_timeout': 60,
        'heartbeat_interval': 25,
    }

    def __init__(self, *args, **kwargs):
        self.sockets = {}
        self.transports = kwargs.pop('transports', None)
        self.resource = kwargs.pop('resource', 'socketio')

        super(Server, self).__init__(*args, **kwargs)

    def handle(self, socket, address):
        """
        Create a EngineHandler.
        """
        handler = EngineHandler(socket, address, self)
        handler.on('connection', self.on_connection)
        handler.handle()

    def on_connection(self, engine_socket):
        """
        Called when there is a new connection, should be implemented by inherited class
        :param engine_socket: The underlying engine_socket
        :return: None
        """
        raise NotImplementedError()
