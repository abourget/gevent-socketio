import random
import weakref

import gevent
from gevent.queue import Queue
from gevent.event import Event

from socketio.packet import Packet

class Socket(object):
    """
    Virtual Socket implementation, checks heartbeats, writes to local queues for
    message passing, holds the Namespace objects, dispatches de packets to the
    underlying namespaces.

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
        self.request = None
        self.environ = None
        self.namespaces = {}
        self.active_ns = {} # Namespace sessions that were instantiated (/chat)
        self.jobs = []

        def disconnect_timeout():
            self.timeout.clear()
            if self.timeout.wait(10.0):
                gevent.spawn(disconnect_timeout)
            else:
                self.kill()
        gevent.spawn(disconnect_timeout)

    def _set_namespaces(self, namespaces):
        """This is a mapping (dict) of the different '/namespaces' to their
        BaseNamespace object derivative.
        
        This is called by socketio_manage()."""
        self.namespaces = namespaces

    def _set_request(self, request):
        """Saves the request object for future use by the different Namespaces.

        This is called by socketio_manage().
        """
        self.request = request
    
    def _set_environ(self, environ):
        """Save the WSGI environ, for future use.

        This is called by socketio_manage().
        """
        self.environ = environ

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


    def __getitem__(self, key):
        """This will get the nested Namespace using its '/chat' reference.

        Using this, you can go from one Namespace to the other (to emit, add
        ACLs, etc..) with:

          adminnamespace.socket['/chat'].add_acl_method('kick-ban')

        """
        return self.active_ns[key]

    def __hasitem__(self, key):
        """Verifies if the namespace is active (was initialized)"""
        return key in self.active_ns

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
            self.disconnect()
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



    # User facing low-level function
    def disconnect(self):
        """Calling this method will call the disconnect() method on all the
        active Namespaces that were open, and remove them from the ``active_ns``
        map.
        """
        for ns_name, ns in self.active_ns.iteritems():
            ns.disconnect()
        # TODO: Find a better way to remove the Namespaces from the ``active_ns``
        #       zone.  Have the Ns.disconnect() call remove itself from the
        #       underlying socket ?
        self.active_ns = {}

    def send_packet(self, packet):
        """Low-level interface to queue a packet on the wire (encoded as wire
        protocol"""
        self.put_client_msg(packet.encode())

    def spawn(self, fn, *args, **kwargs):
        """Spawn a new Greenlet, attached to this Socket instance.

        It will be monitored by the "watcher" method
        """

        self.debug("Spawning sub-Socket Greenlet: %s" % fn.__name__)
        job = gevent.spawn(fn, *args, **kwargs)
        self.jobs.append(job)
        return job

    def _reader_loop(self):
        """This is the loop that takes messages from the queue for the server
        to consume, decodes them and dispatches them.
        """

        while True:
            raw_msg = self.get_server_msg()

            if raw_msg:
                #try:
                packet = Packet.decode(raw_msg)
                #except DontKnowError, e:
                #    manage error ? send a message! no valid error processing?!

                # Find out to which endpoint (Namespace obj)
                # Find the endpoint, instantiate if required
                # Dispatch the message to the Namespace
                #   .. see if we need to connect..
                endpoint = packet.endpoint
                if endpoint not in self.namespaces:
                    #log.debug("unknown packet arriving: ", endpoint)
                    print "WE DON'T HAVE SUCH A NAMESPACE"
                    continue
                elif endpoint in self.active_ns:
                    active_ns = self.active_ns[endpoint]
                else:
                    new_ns_class = self.namespaces[endpoint]
                    new_ns = new_ns_class(self.environ, endpoint,
                                          request=self.request)
                    if not new_ns.connect():
                        continue
                    self.active_ns[endpoint] = new_ns

                active_ns.process_packet(packet)

            if not self.connected:
                self.kill() # ?? what,s the best clean-up when its not a
                            # user-initiated disconnect
                return

    def _spawn_reader_loop(self):
        """Spawns the reader loop.  This is called internall by socketio_manage()
        """
        job = gevent.spawn(self._reader_loop)
        self.jobs.append(job)
        return job
    def _watcher(self):
        """Watch if any of the greenlets for a request have died. If so, kill the
        request and the socket.
        """
        # TODO: add that if any of the request.jobs die, kill them all and exit
        gevent.sleep(5.0)

        while True:
            gevent.sleep(1.0)

            if not self.connected:
                # Killing Socket-level jobs
                gevent.killall(self.jobs)
                for ns_name, ns in self.active_ns:
                    ns.disconnect()
                    ns.kill_local_jobs()

    def _spawn_watcher(self):
        job = gevent.spawn(self._watcher)
        return job
    
