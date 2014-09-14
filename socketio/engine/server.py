from __future__ import absolute_import

import sys
import traceback
import logging
from socket import error

from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
from socketio.engine.handler import EngineHandler

from socketio.policyserver import FlashPolicyServer

__all__ = ['Server']

logger = logging.getLogger(__name__)


class Server(WSGIServer):

    def __init__(self, *args, **kwargs):
        self.sockets = {}
        self.transports = kwargs.pop('transports', None)

        self.resource = kwargs.pop('resource', 'socketio')
        self.server_side = kwargs.pop('server_side', True)

        if kwargs.pop('policy_server', True):
            try:
                address = args[0][0]
            except TypeError:
                try:
                    address = args[0].address[0]
                except AttributeError:
                    try:
                        address = args[0].cfg_addr[0]
                    except AttributeError:
                        address = args[0].getsockname()[0]

            policylistener = kwargs.pop('policy_listener', (address, 10843))
            self.policy_server = FlashPolicyServer(policylistener)
        else:
            self.policy_server = None

        # Extract other config options
        self.config = {
            'heartbeat_timeout': 60,
            'close_timeout': 60,
            'heartbeat_interval': 25,
        }
        for f in ('heartbeat_timeout', 'heartbeat_interval', 'close_timeout'):
            if f in kwargs:
                self.config[f] = int(kwargs.pop(f))

        if not 'handler_class' in kwargs:
            kwargs['handler_class'] = EngineHandler

        if not 'ws_handler_class' in kwargs:
            self.ws_handler_class = WebSocketHandler
        else:
            self.ws_handler_class = kwargs.pop('ws_handler_class')

        super(Server, self).__init__(*args, **kwargs)

    def start_accepting(self):
        if self.policy_server is not None:
            try:
                if not self.policy_server.started:
                    self.policy_server.start()
            except error, ex:
                sys.stderr.write(
                    'FAILED to start flash policy server: %s\n' % (ex, ))
            except Exception:
                traceback.print_exc()
                sys.stderr.write('FAILED to start flash policy server.\n\n')
        super(Server, self).start_accepting()

    def stop(self, timeout=None):
        if self.policy_server is not None:
            self.policy_server.stop()
        super(Server, self).stop(timeout=timeout)

    def handle(self, socket, address):
        # Pass in the config about timeouts, heartbeats, also...
        handler = self.handler_class(self.config, socket, address, self)
        handler.on('connection', self.on_connection)
        handler.handle()

    def on_connection(self, engine_socket):
        raise NotImplementedError()
