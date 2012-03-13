
import weakref

from socketio.packet import Packet

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
        self.ack_callbacks = {}

        def disconnect_timeout():
            self.timeout.clear()
            if self.timeout.wait(10.0):
                gevent.spawn(disconnect_timeout)
            else:
                self.kill()
        gevent.spawn(disconnect_timeout)

    def set_namespaces(self, namespaces):
        """This is call by socketio_manage()"""
        self.namespaces = namespaces

    def __str__(self):
        result = ['sessid=%r' % self.sessid]
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
        """Used by the transports"""
        self.clear_disconnect_timeout()
        self.server_queue.put_nowait(msg)

    def put_client_msg(self, msg):
        """Used by the transports"""
        self.clear_disconnect_timeout()
        self.client_queue.put_nowait(msg)

    def get_client_msg(self, **kwargs):
        """Used by the transports"""
        return self.client_queue.get(**kwargs)

    def get_server_msg(self, **kwargs):
        """Used by the transports"""
        return self.server_queue.get(**kwargs)


    #
    def _reader_loop(self):
        """This is the loop that takes messages from the queue for the server
        to consume, decodes them and dispatches them.
        """

        while True:
            message = self.get_server_msg()

            if message:
                packet = Packet.decode(message)
                # Find out to which endpoint (Namespace obj)
                # Find the endpoint, instantiate if required
                # Dispatch the message to the Namespace
                #   .. see if we need to connect..
                if packet.endpoint not in self.namespaces:
                    #log.debug("unknown packet arriving: ", packet.endpoint)
                    print "WE DON'T HAVE SUCH A NAMESPACE"
                elif packet.endpoint in self.
                    
                if not isinstance(message, dict):
                    context.error("bad_request",
                                "Your message needs to be JSON-formatted")
                elif in_type not in message:
                    context.error("bad_request",
                                "You need a 'type' attribute in your message")
                else:
                    # Call msg in context.
                    newctx = context(message)

                    # Switch context ?
                    if newctx:
                        context = newctx

            if not io.session.connected:
                context.kill()
                return

    def _spawn_reader_loop(self):
        """Spawns the reader loop.  This is called internall by socketio_manage()
        """
        self.jobs.append(gevent.spawn(self._reader_loop))

    # User facing low-level function
    def disconnect(self):
        # TODO: force the disconnection.
        pass

    def send_packet(self, packet):
        """Low-level interface to queue a packet on the wire (encoded as wire
        protocol"""
        self.put_client_msg(packet.encode())
