import logging
from redis.client import Lock

from .utils import RedisQueue, RedisMapping
from ...socket_manager import BaseSocketManager

logger = logging.getLogger(__name__)

class SocketLock(Lock):
    def __init__(self, manager, sessid, *args, **kwargs):
        self.sessid = sessid
        self.manager = manager
        name = self.manager.make_key(sessid, "lock")
        super(SocketLock, self).__init__(manager.redis, name, *args, **kwargs)
        
    def __enter__(self): 
        super(SocketLock, self).__enter__()
        self.socket = self.manager.get_socket(self.sessid)
        return self.socket

    def __exit__(self, *args, **kwargs):
        self.manager.return_socket(self.socket)
        return super(SocketLock, self).__exit(*args, **kwargs)
            
class RedisSocketManager(BaseSocketManager):
    def __init__(self):
        self.prefix = "socketio.socket:"
        self.sockets = {}
        
    def make_key(self, sessid, suffix):
        return "%s%s:%s"%(self.prefix, sessid, suffix)
    
    def get_socket(self, sessid):
        #1. If sessid in self.sockets 
        #1.1 Load socket state and session from redis
        #2. Check Redis if session was handshaken
        #2.1 If yes, lo 
        pass
    
    def make_queue(self, sessid, name):
        """Returns a Redis based message queue.
        """
        return RedisQueue(self.redis, self.make_key(sessid, "queue:%s" % name))
        
    def make_session(self, sessid):
        return RedisMapping(self.redis, self.make_key(sessid, "session"))
            
    def socket_transaction(self, sessid):
        return SocketLock(self, sessid)
    
    
    
        