import logging

import gevent
from gevent.queue import Empty
from redis.client import Redis

from .utils import RedisQueue, RedisMapping
from ...socket_manager import BaseSocketManager
from ...virtsocket import Socket
import time
import uuid

logger = logging.getLogger(__name__)

class GroupLock(object):
    """
    A shared, distributed lock backed by Redis.
    
    The Lock can be held by a group of 'holders' and is only released once all holders have released it.
    """

    def __init__(self, redis, name, sleep=0.1):
        """
        Create a new Lock instance named ``name`` using the Redis client
        supplied by ``redis``.

        ``sleep`` indicates the amount of time to sleep per loop iteration
        when other group of holders are currently holding the lock.
        """
        self.redis = redis
        self.name = name
        self.acquired = False
        self.sleep = sleep
        self.holders = set()

    def acquire(self, holder):
        """
        Adds the new holder to this instance's holders group.
        This method blocks indefinitely until the group holds the lock and returns immediately after.
        """
        while 1:
            if self.acquired:
                self.holders.add(holder)
                return True
            
            if self.redis.setnx(self.name, int(time.time())):
                self.acquired = True
                self.holders.add(holder)
                return True
            gevent.sleep(self.sleep)

    def release(self, holder, callback = None):
        """Removes the given holder from the group and releases the lock if it's the last holder.
        
        If the lock is going to be released calls ``callback`` before releasing.
        """
        if not self.acquired:
            raise ValueError("Cannot release an unlocked lock")
        self.holders.remove(holder)
        if len(self.holders) < 1:
            #release the lock 
            if callback:
                callback()
            self.redis.delete(self.name)
            self.acquired = None
       
class SessionContextManager(object):
    """
    """
    def __init__(self, manager, sessid):
        self.sessid = sessid
        self.manager = manager
        
    def __enter__(self): 
        lock = self.manager.locks.get(self.sessid)
        #register as a lock holder
        lock.aquire(self) #blocks if necessary
        return self.manager.get_socket(self.sessid)

    def __exit__(self, *args, **kwargs):
        lock = self.manager.locks.get(self.sessid)
        #unregister as a lock holder and release the lock if necessary
        #the socket is saved to Redis at release time
        lock.release(self, self.on_lock_release)
          
    def on_lock_release(self):
        self.manager.save_socket(self.sessid)

class Locks(dict):
    def __init__(self, manager):
        self.manager = manager
    def __missing__(self, sessid):
        return GroupLock(self.manager.redis, self.manager.make_session_key(sessid, "lock"))
          
class RedisSocketManager(BaseSocketManager):
    def __init__(self, config):
        self.config = config
        self.options = config.get("socket_manager", {})
        self.prefix = self.options.get("namespace_prefix", "socketio.socket:")

        self.alive_key = "%s:alive" % self.prefix
        self.hits_key = "%s:hits" % self.prefix
        self.sockets = {}
        self.locks = Locks(self)
        self.uuid = str(uuid.uuid1())
        
    def start(self):
        redis_cfg = self.options.get("redis", {})
        self.redis = Redis(**redis_cfg)
        self.pubsub = Redis(**redis_cfg).pubsub()
        
        self.started = True
        #start listening for syncing messages from other managers
        self.sync_job = gevent.spawn(self.hearbeat_listener)
    
    def stop(self):
        self.started = False
        self.sync_job.kill()
        
    def make_session_key(self, sessid, suffix):
        return "%s%s:%s"%(self.prefix, sessid, suffix)
    
    def get_socket(self, sessid):
        socket = self.sockets.get(sessid)
        if not socket:
            #check if handshaken
            if self.redis.hget(self.alive_key, sessid):
                socket = Socket(sessid, self, self.config)
                self.sockets[sessid] = socket
                
        if socket:
            self.load_socket(socket)
        return socket
    
    def make_queue(self, sessid, name):
        """Returns a Redis based message queue.
        """
        return RedisQueue(self.redis, self.make_session_key(sessid, "queue:%s" % name))
        
    def read_queue(self, queue, **kwargs):
        """Optimized for faster bulk read from Redis, while still supporting ``block`` and ``timeout`` for the first read.
        
        Returns a list of all messages currently in the Queue.
        Raises ``gevent.queue.Empty`` if the queue is empty
        """
        ret = []
        block = kwargs.get('block', True)
        if block:
            ret.append(queue.get(**kwargs)) #block while reading the first
        ret += queue.get_all() #bulk reads the rest, if any
        if not ret:
            raise Empty
        return ret
    
    def make_session(self, sessid):
        """Returns a Redis backed session storage. 
        
        All changes are immediately written to Redis.
        """
        return RedisMapping(self.redis, self.make_session_key(sessid, "session"))
            
    def lock_session(self, sessid):
        """Locks the socket session with the given ``sessid`` for the  duration of a ``with`` block.
        
        Entering the ``with`` block returns a socket for the given session or None if it was not handsheken yet.
        
        Example:
        
            with manager.socket_transaction('12345678') as socket:
                if socket:
                    socket.do_something()
                else:
                    bad_session()
                    
        """
        
        return SessionContextManager(self, sessid)

    def handshake(self, sessid):
        """Don't create the socket yet, just mark the session as existing.
        """
        self.redis.hset(self.alive_key, sessid, "1")
        
    def kill_session(self, sessid):
        if not sessid:
            return
        #@todo Distribute this
        socket = self.sockets.get(sessid)
        if socket:
            socket.kill(detach = True)
        self.redis.hdel(self.alive_key, sessid)
    
    def load_socket(self, socket):
        """Reads from Redis and sets any internal state of the socket that must 
        be shared between all sockets in the same session.
        """
        socket.hits = self.redis.hincrby(self.hits_key, socket.sessid, 1)
                
    def save_socket(self, sessid):
        """Stores into Redis any internal state that must be shared between all sockets in the same session.
        """
        return
            
    def make_heartbeat_message(self, sessid):
        return "%s:%s"%(self.uuid, sessid)
    
    def parse_heartbeat_message(self, message):
        return message.split(":", 1)
    
    def heartbeat_received(self, sessid):
        socket = self.sockets.get(sessid)
        if socket:
            socket.heartbeat()
        self.redis.publish("heartbeat.received", self.make_heartbeat_message(sessid))
                    
    def heartbeat_sent(self, sessid):
        self.redis.publish("heartbeat.sent", self.make_heartbeat_message(sessid))
    
    def hearbeat_listener(self):
        """Listens to a Redis PubSub for heartbeat messages."""
        self.pubsub.psubscribe('heartbeat.*')
        while self.connected:
            msg = self.pubsub.listen()
            channel = msg.get('channel')
            uuid, sessid = self.parse_heartbeat_message(msg.get('data'))
            if channel == "hearbeat.received":
                if uuid != self.uuid:
                    socket = self.sockets.get(sessid)
                    if socket:
                        socket.heartbeat()
            elif channel == "hearbeat.sent":
                if uuid != self.uuid:
                    socket = self.sockets.get(sessid)
                    if socket:
                        socket.heartbeat_sent()
            gevent.sleep(0) 