import sys
import random
import traceback
import gevent

from socket import error

from gevent.pywsgi import WSGIServer

from socketio.handler import SocketIOHandler
from socketio.policyserver import FlashPolicyServer
from socketio.virtsocket import Socket

__all__ = ['SocketIOServer']

class SocketIOServer(WSGIServer):
    """A WSGI Server with a resource that acts like an SocketIO."""

    def __init__(self, *args, **kwargs):
        self.sockets = {}
        resource = kwargs.pop('resource', None)
        if resource:
            print "DEPRECATED: use `namespace` instead of 'resource' as a SocketIOServer parameter"
            self.namespace = resource
        else:
            self.namespace = kwargs.pop('namespace', 'socket.io')
        self.transports = kwargs.pop('transports', None)

        if kwargs.pop('policy_server', True):
            self.policy_server = FlashPolicyServer()
        else:
            self.policy_server = None

        kwargs['handler_class'] = SocketIOHandler
        super(SocketIOServer, self).__init__(*args, **kwargs)

    def start_accepting(self):
        if self.policy_server is not None:
            try:
                self.policy_server.start()
            except error, ex:
                sys.stderr.write('FAILED to start flash policy server: %s\n' % (ex, ))
            except Exception:
                traceback.print_exc()
                sys.stderr.write('FAILED to start flash policy server.\n\n')
        super(SocketIOServer, self).start_accepting()

    def kill(self):
        if self.policy_server is not None:
            self.policy_server.kill()
        super(SocketIOServer, self).kill()

    def handle(self, socket, address):
        handler = self.handler_class(socket, address, self)
        self.set_environ({'socketio': Socket(handler)})
        handler.handle()

    def get_socket(self, sessid=''):
        """Return an existing or new client Socket."""

        socket = self.sockets.get(sessid)

        if socket is None:
            socket = Socket(self)
            self.sockets[socket.sessid] = socket
        else:
            socket.incr_hits()

        return socket
