import logging
import random
import weakref
from abc import abstractmethod, ABCMeta
from gevent.queue import Queue

from .virtsocket import Socket

logger = logging.getLogger(__name__)

class BaseSocketManager(object):
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def make_queue(self, sessid, name):
        return None
    
    @abstractmethod
    def make_session(self, sessid):
        return None
    
    @abstractmethod
    def socket_transaction(self, sessid):
        return None
    
    @abstractmethod
    def get_socket(self, sessid):
        return None
    
    @abstractmethod
    def handshake(self):
        return
    
    @abstractmethod
    def kill_socket(self, socket):
        return
    
class SocketContextManager(object):
    def __init__(self, socket):
        self.socket = socket
        
    def __enter__(self): 
        return self.socket

    def __exit__(self, *args, **kwargs):
        return
       
class SocketManager(BaseSocketManager):
    """The default, non-distributed manager.
    """
    def __init__(self, server):
        self.server = weakref.ref(server)
        self.handshaked = set()
        self.sockets = {}
    
    def get_socket(self, sessid):
        ret = self.sockets.get(sessid)
        if (not ret) and sessid in self.handshaked:
            server = self.server()
            self.sockets[sessid] = ret = Socket(sessid, server, server.config)
        return ret
    
    def make_queue(self, sessid, name):
        """Returns a gevent based message queue.
        """
        return Queue()
        
    def make_session(self, sessid):
        """Local session is just a dictionary.
        """
        return {}
            
    def socket_transaction(self, sessid, *args, **kwargs):
        """Returns a transaction ``ContextManager`` to be used with a ``with`` (PEP 343) block.
        
        Entering the transaction (i.e. the ``with`` block) will return a new or existing socket for the session with the given ``sessid``
        if it was already handshaken or None if no such session exists.
        
        Example:
        
            with manager.socket_transaction('12345678') as socket:
                if socket:
                    socket.do_something()
                else:
                    bad_session()
                
        """
        return SocketContextManager(self, self.get_socket(sessid))
    
    def handshake(self):
        """Don't create the socket yet, just mark the session as existing.
        """
        sessid = str(random.random())[2:]
        self.handshaked.add(sessid)
        
    def kill_socket(self, sessid):
        socket = self.sockets.get(sessid)
        if socket:
            socket.kill(detach = True)
            
        