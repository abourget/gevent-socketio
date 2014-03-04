import logging
import random
from collections import defaultdict
from abc import abstractmethod, ABCMeta

from gevent.queue import Queue

from socketio.virtsocket import Socket

logger = logging.getLogger(__name__)

class BaseSocketManager(object):
    """A layer of abstraction between the ``server`` and the ``virtsocket``.
    
    
     Allows for pluggable socket distribution and lifecycle management on top of various backends. 
     
    """
    __metaclass__ = ABCMeta
    
    def __init__(self, config):
        self.config = config
        self.sockets = {}
        self.socket_listeners = defaultdict(lambda : defaultdict(list))
        self.endpoint_listeners = defaultdict(lambda : defaultdict(list))
        
    def add_socket_listener(self, sessid, event, listener):
        """Add a callable to be notified for when socket ``sessid`` triggers ``event``.
        
        The callable's signature should be:
        fn(socket_manager, sessid, event, *args, **kwargs) 
        where *args and **kwargs are the arguments with which the ``notify`` method was called
        """
        self.socket_listeners[sessid][event].append(listener)
        
    def remove_socket_listener(self, sessid, event, listener):
        """Removes ``listener`` for the given ``sessid`` and ``event`` combination.
        
        Raises ValueError if ``listener`` was not registered for ``sessid`` / ``event``.
        """
        self.socket_listeners[sessid][event].remove(listener)
        
    def notify_socket(self, sessid, event, *args, **kwargs):
        """Notify all listeners of socket ``sessid`` with ``event``.
        """
        for l in self.socket_listeners[sessid][event]:
            l(self, sessid, event, *args, **kwargs)
            
    def add_endpoint_listener(self, endpoint, event, listener):
        """Add a callable to be notified when namespace ``endpoint`` triggers ``event``.
        
        The callable's signature should be:
        fn(socket_manager, endpoint_name, event, *args, **kwargs) 
        where *args and **kwargs are the arguments with which the ``notify`` method was called
        """
        self.endpoint_listeners[endpoint][event].append(listener)
        
    def remove_endpoint_listener(self, endpoint, event, listener):
        """Removes ``listener`` for the given ``endpoint`` / ``event`` combination.
        
        Raises ValueError if ``listener`` was not registered for ``endpoint`` / ``event``.
        """
        self.endpoint_listeners[endpoint][event].remove(listener)
        
    def notify_endpoint(self, endpoint, event, *args, **kwargs):
        """
        Trigger ``event`` for all listeners of namespace ``endpoint``.
        """
        for l in self.endpoint_listeners[endpoint][event]:
            l(self, endpoint, event, *args, **kwargs)
        
    def next_socket_id(self):
        """The rule for generating a new session id for the socket.
        """
        return str(random.random())[2:].ljust(12, "0")#keep all sessid of same size
      
    def start(self):
        """Called when starting the owning server.
        """
        pass
    
    def stop(self):
        """Called when stopping the owning server.
        """
        pass
      
    def detach(self, sessid):
        """Detaches the socket from the manager and cleans up any socket-specific data.
        """
        try:
            del self.sockets[sessid]
        except KeyError:
            pass
        
        try:
            del self.socket_listeners[sessid]
        except KeyError:
            pass
    
    def heartbeat_received(self, sessid):
        """Called when a heartbeat for the given socket arrives.
        """
        socket = self.sockets.get(sessid)
        if socket:
            self.notify_socket(sessid, 'heartbeat_received')
            socket.heartbeat()
            
    def heartbeat_sent(self, sessid):
        """Notifies the manager that a heartbeat was sent by the session's socket.
        
        The manager should notify any other distributed socket managers, to avoid multiple heartbeats for the same session.
        """
        self.notify_socket(sessid, 'heartbeat_sent')
     
    def get_socket(self, sessid):
        """Returns a socket if the session exists (i.e. was handshaken) or None.
        """
        socket = self.sockets.get(sessid)
        if (not socket) and self.is_handshaken(sessid):
            socket = Socket(sessid, self, self.config)
            self.sockets[sessid] = socket
        if socket:
            socket = self.load_socket(socket) 
        return socket
        
    def load_socket(self, socket):
        """Called by ``get_socket`` to updates the socket's internal state in a backend specific way before returning it to the caller.
        """
        socket.incr_hits()
        return socket
    
    def init_connection(self, socket, *args, **kwargs):
        """Setup the socket in a connected state.
        
        This is executed on the *first* packet of the establishment of the virtual Socket connection or 
        when a new instance of an already connected distributed socket is created by a different socket manager (i.e. worker).
        """
        socket.connection_established = True
        socket.state = socket.STATE_CONNECTED
        socket._spawn_heartbeat()
        socket._spawn_watcher()
        
        
    @abstractmethod
    def activate_endpoint(self, sessid, endpoint):
        """Add a namespace endpoint to the active ones for this session.
        """
        return
    
    @abstractmethod
    def deactivate_endpoint(self, sessid, endpoint):
        """Remove the endpoint from the active ones for this session.
        """
        return None
    
    @abstractmethod
    def active_endpoints(self, sessid):
        """Check if there are any active namespaces across all sockets for the given session.
        """
        return None
        
    @abstractmethod
    def make_queue(self, sessid, name):
        """Returns an object to be used as the message queue of the given ``name`` in the socket session with the given ``sessid``.
        """
        return None
    
    @abstractmethod
    def read_queue(self, queue, **kwargs):
        """Pops all available messages from the queue.
        
        Optional ``timeout`` and ``block`` parameters can be passed and they work the same as the queue's ``get`` method.
        Returns a list of all messages.
        Raises ``gevent.queue.Empty`` (``Queue.Empty`` in python 2.x, ``queue.Empty`` in python 3.x)
        """
        return None
    
    @abstractmethod
    def make_session(self, sessid):
        """Returns an object to be used as a session storage in the socket session with the given ``sessid``.
        """
        return None
    
    @abstractmethod
    def lock_socket(self, sessid):
        """Lock the session to the local socket for the duration of a ``with`` (PEP 343) block.
        
        Entering the context (i.e. the ``with`` block) will return a new or existing socket holding the 
        lock for the session with the given ``sessid``.
        If the session is not known (i.e. was not handshaken) the returned socket will be None.
        
        Example:
        
            with manager.lock_socket('12345678') as socket:
                if socket:
                    socket.do_something()
                else:
                    bad_session()
                
        Nested or parallel locks of the same session using the same manager won't block on each other 
        and should result in the same socket.
        """
        return None
    
    @abstractmethod
    def handshake(self, sessid):
        """Mark the session as handshaken/alive.
        """
        return
    
    @abstractmethod
    def is_handshaken(self, sessid):
        return False
    
    
class SessionContextManager(object):
    """Returned by the default SocketManager.lock_socket to 'fake' a locked session to be used with a ``with`` block
    """
    def __init__(self, socket):
        self.socket = socket
        
    def __enter__(self): 
        return self.socket

    def __exit__(self, *args, **kwargs):
        return
       
class SocketManager(BaseSocketManager):
    """The default, non-distributed manager.
    """
    def __init__(self, *args, **kwargs):
        super(SocketManager, self).__init__(*args, **kwargs)
        self.alive_sessions = set()
        self.ns_registry = defaultdict(set)
    
    def make_queue(self, sessid, name):
        """Returns a gevent.queue based message queue.
        """
        return Queue()
    
    def read_queue(self, queue, **kwargs):
        """Reads all available messages in the queue (blocks if ``block``=True was set)
        """
        ret = [queue.get(**kwargs)]
        while queue.qsize():
            ret.append(queue.get())
        return ret

    def make_session(self, sessid):
        """The local socket's session is a plain dictionary.
        """
        return {}
            
    def lock_socket(self, sessid):
        """Creates a dummy lock (i.e. nothing is locked), just makes it all work with a ``with`` block."""
        return SessionContextManager(self.get_socket(sessid))
    
    def handshake(self, sessid):
        """Don't create the socket yet, just mark the session as existing.
        """
        self.alive_sessions.add(sessid)
         
    def is_handshaken(self, sessid):
        return sessid in self.alive_sessions       
    
    def activate_endpoint(self, sessid, endpoint):
        self.ns_registry[sessid].add(endpoint)
    
    def deactivate_endpoint(self, sessid, endpoint):
        try:
            self.ns_registry[sessid].remove(endpoint)
            return True
        except KeyError:
            return False
    
    def active_endpoints(self, sessid):
        return self.ns_registry[sessid]
    
    def detach(self, sessid):
        """Detaches the socket from the manager and cleans up any socket-specific data.
        """
        super(SocketManager, self).detach(sessid)
        try:
            del self.ns_registry[sessid]
        except KeyError:
            pass
        
        try:
            self.alive_sessions.remove(sessid)
        except KeyError:
            pass
