import random

from gevent.pywsgi import WSGIServer
from gevent.queue import Queue
from geventsocketio.protocol import SocketIOProtocol



class SocketIOServer(WSGIServer):
    def __init__(self, *args, **kwargs):
        self.sessions = {}
        self.resource = kwargs['resource']
        del kwargs['resource'] # FIXME : hack
        super(SocketIOServer, self).__init__(*args, **kwargs)

    def handle(self, socket, address):
        handler = self.handler_class(socket, address, self)
        self.set_environ({'socketio': SocketIOProtocol(handler)})
        handler.handle()

    def get_session(self, session_id):
        session = self.sessions.get(session_id, Session())

        if session.session_id in self.sessions:
            session.incr_hits()
            return session
        else:
            self.sessions[session.session_id] = session
            return session


class Session(object):
    def __init__(self):
        self.session_id = str(random.random())[2:]
        self.write_queue = Queue()
        self.messages = Queue()
        self.hits = 0

    def incr_hits(self):
        self.hits += 1

    def is_new(self):
        return self.hits == 0
