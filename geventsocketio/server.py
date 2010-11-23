import sys
import random
import traceback
from socket import error

from gevent.pywsgi import WSGIServer
from gevent.queue import Queue
from geventsocketio.protocol import SocketIOProtocol
from geventsocketio.handler import SocketIOHandler
from geventsocketio.policyserver import FlashPolicyServer


__all__ = ['SocketIOServer']

class SocketIOServer(WSGIServer):
    """A WSGI Server with a resource that acts like an SocketIO."""

    def __init__(self, *args, **kwargs):
        self.sessions = {}
        self.resource = kwargs.pop('resource')
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
        self.set_environ({'socketio': SocketIOProtocol(handler)})
        handler.handle()

    def get_session(self, session_id=''):
        """Return an existing or new client Session."""

        session = self.sessions.get(session_id)

        if session is None:
            session = Session()
            self.sessions[session.session_id] = session
        else:
            session.incr_hits()

        return session


class Session(object):
    """
    Client session which checks the connection health and the queues for
    message passing.
    """

    def __init__(self):
        self.session_id = str(random.random())[2:]
        self.client_queue = Queue() # queue for messages to client
        self.server_queue = Queue() # queue for messages to server
        self.hits = 0
        self.heartbeats = 0
        self.connected = False

    def incr_hits(self):
        self.hits += 1

    def heartbeats(self):
        self.heartbeats += 1
        return self.heartbeats

    def valid_heartbeat(self, counter):
        return self.heartbeats == counter

    def is_new(self):
        return self.hits == 0

    def kill(self):
        if self.connected:
            self.connected = False
            self.server_queue.put_nowait(None)
            self.client_queue.put_nowait(None)
        else:
            pass # Fail silently

    def put_server_msg(self, msg):
        self.server_queue.put_nowait(msg)

    def put_client_msg(self, msg):
        self.client_queue.put_nowait(msg)

    def get_client_msg(self, **kwargs):
        return self.client_queue.get(**kwargs)

    def get_server_msg(self, **kwargs):
        return self.server_queue.get(**kwargs)
