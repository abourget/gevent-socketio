
import weakref

class Socket(object):
    """
    Virtual Socket implementation, checks heartbeats, writes to local queues for
    message passing, holds the Namespace objects.

    This is the abstraction on top of the different transports.  It's like
    if you used a WebSocket only...
    """

    STATE_NEW = "NEW"
    STATE_CONNECTED = "CONNECTED"
    STATE_DISCONNECTING = "DISCONNECTING"
    STATE_DISCONNECTED = "DISCONNECTED"

    def __init__(self, server):
        self.server = weakref.proxy(server)
        self.sessid = str(random.random())[2:]
        self.client_queue = Queue() # queue for messages to client
        self.server_queue = Queue() # queue for messages to server
        self.hits = 0
        self.heartbeats = 0
        self.timeout = Event()
        self.wsgi_app_greenlet = None
        self.state = "NEW"
        self.connection_confirmed = False

        def disconnect_timeout():
            self.timeout.clear()
            if self.timeout.wait(10.0):
                gevent.spawn(disconnect_timeout)
            else:
                self.kill()
        gevent.spawn(disconnect_timeout)

    def __str__(self):
        result = ['session_id=%r' % self.sessid]
        if self.state == self.STATE_CONNECTED:
            result.append('connected')
        if self.client_queue.qsize():
            result.append('client_queue[%s]' % self.client_queue.qsize())
        if self.server_queue.qsize():
            result.append('server_queue[%s]' % self.server_queue.qsize())
        if self.hits:
            result.append('hits=%s' % self.hits)
        if self.heartbeats:
            result.append('heartbeats=%s' % self.heartbeats)

        return ' '.join(result)

    @property
    def connected(self):
        return self.state == self.STATE_CONNECTED

    def incr_hits(self):
        self.hits += 1

        if self.hits == 1:
            self.state = self.STATE_CONNECTED

    def clear_disconnect_timeout(self):
        self.timeout.set()

    def heartbeat(self):
        self.clear_disconnect_timeout()

    def kill(self):
        if self.connected:
            self.state = self.STATE_DISCONNECTING
            self.server_queue.put_nowait(None)
            self.client_queue.put_nowait(None)
            #gevent.kill(self.wsgi_app_greenlet)
        else:
            pass # Fail silently

    def put_server_msg(self, msg):
        self.clear_disconnect_timeout()
        self.server_queue.put_nowait(msg)

    def put_client_msg(self, msg):
        self.clear_disconnect_timeout()
        self.client_queue.put_nowait(msg)

    def get_client_msg(self, **kwargs):
        return self.client_queue.get(**kwargs)

    def get_server_msg(self, **kwargs):
        return self.server_queue.get(**kwargs)
