import logging
import random
from collections import defaultdict
from abc import abstractmethod, ABCMeta

from gevent.queue import Queue

from .virtsocket import Socket

logger = logging.getLogger(__name__)

class BaseSocketManager(object):
    """A layer of abstraction between the server and the virtsocket.
    
    
     Allows for plugable socket distribution and lifecycle management on top of various backends. 
     
    """
    __metaclass__ = ABCMeta
    
    def __init__(self, config):
        self.config = config
        self.sockets = {}
    
    def next_socket_id(self):
        """The rule for generating a new session id for the socket.
        """
        return str(random.random())[2:]
      
    def start(self):
        pass
    
    def stop(self):
        pass
      
    def get_socket(self, sessid):
        """Returns a socket if the session exists (i.e. was handshaken) or None.
        """
        return self.sockets.get(sessid)
    
    def detach(self, sessid):
        try:
            del self.sockets[sessid]
        except KeyError:
            pass
        
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
    def heartbeat_sent(self, sessid):
        """Notifies the manager that a heartbeat was sent by the session's socket.
        
        The manager should notify any other distributed socket managers, to avoid multiple heartbeats for the same session.
        """
        return
    
    @abstractmethod
    def heartbeat_received(self, sessid):
        return
    
class SessionContextManager(object):
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
    
    def get_socket(self, sessid):
        ret = super(SocketManager, self).get_socket(sessid)
        if (not ret) and sessid in self.alive_sessions:
            self.sockets[sessid] = ret = Socket(sessid, self, self.config)
        ret.incr_hits()
        return ret
    
    def make_queue(self, sessid, name):
        """Returns a gevent.queue based message queue.
        """
        return Queue()
    
    def read_queue(self, queue, **kwargs):
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
        
    def heartbeat_received(self, sessid):
        socket = self.sockets.get(sessid)
        if socket:
            socket.heartbeat()
            
    def heartbeat_sent(self, sessid):
        return        
    
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
