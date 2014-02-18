import logging

import gevent
from gevent.queue import Empty
from redis.client import Redis

from socketio.contrib.redis.utils import RedisQueue, RedisMapping, GroupLock, DefaultDict
from socketio.socket_manager import BaseSocketManager
from socketio.virtsocket import Socket
import uuid
import json

logger = logging.getLogger(__name__)
       
class SessionContextManager(object):
    """
    """
    def __init__(self, manager, sessid):
        self.sessid = sessid
        self.manager = manager
        
    def __enter__(self): 
        lock = self.manager.locks[self.sessid]
        #register as a lock holder
        lock.acquire(self) #blocks if necessary
        return self.manager.get_socket(self.sessid)

    def __exit__(self, *args, **kwargs):
        lock = self.manager.locks[self.sessid]
        #unregister as a lock holder and release the lock if necessary
        #the socket is saved to Redis at release time
        lock.release(self, self.on_lock_release)
          
    def on_lock_release(self):
        self.manager.save_socket(self.sessid)
          
class RedisSocketManager(BaseSocketManager):
    
    def __init__(self, *args, **kwargs):
        super(RedisSocketManager, self).__init__(*args, **kwargs)
        
        self.settings = self.config.get("socket_manager", {})
        self.prefix = "socketio.socket:"
        
        redis_settings = {}
        for k, v in self.settings.items():
            if k.startswith('redis_'):
                redis_settings[k.replace("redis_", "", 1)] = v
        self.redis_settings = redis_settings

        self.alive_key = "%s:alive" % self.prefix
        self.hits_key = "%s:hits" % self.prefix
        
        lock_factory = lambda sessid: GroupLock(self.redis, self.make_session_key(sessid, "lock"))
        self.locks = DefaultDict(lock_factory)
        self.uuid = str(uuid.uuid1())
        
        self.sync_handlers = {
                              "heartbeat.*": self.on_heartbeat_sync,
                              "endpoint.*": self.on_endpoint_sync,
                              }
        
    def start(self):
        self.redis = Redis(**self.redis_settings)
        
        #start listening for syncing messages from other managers
        self.sync_job = gevent.spawn(self.sync_listener)
    
    def stop(self):
        self.sync_job.kill()
        
    def make_session_key(self, sessid, suffix):
        return "%s%s:%s"%(self.prefix, sessid, suffix)
    
    def get_socket(self, sessid):
        socket = super(RedisSocketManager, self).get_socket(sessid)
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
            
    def lock_socket(self, sessid):
        """Locks the given session to the local socket for the  duration of a ``with`` block.
        
        Entering the ``with`` block returns a socket with ``sessid`` or None if it was not handshaken yet.
        
        Example:
        
            with manager.lock_socket('12345678') as socket:
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
        
    def load_socket(self, socket):
        """Reads from Redis and sets any internal state of the socket that must 
        be shared between all sockets in the same session.
        """
        socket.hits = self.redis.hincrby(self.hits_key, socket.sessid, 1)
                
    def save_socket(self, sessid):
        """Stores into Redis any internal state that must be shared between all sockets in the same session.
        """
        return
            
    def activate_endpoint(self, sessid, endpoint):
        key = self.make_session_key(sessid, "endpoints")
        self.redis.sadd(key, endpoint)
        self.redis.publish("endpoint.activated", self.make_endpoint_message(sessid, endpoint))
    
    def deactivate_endpoint(self, sessid, endpoint):
        key = self.make_session_key(sessid, "endpoints")
        
        ret = self.redis.srem(key, endpoint) > 0
        if ret:#only notify if the endpoint was still in Redis (this prevents an infinite loop)
            self.redis.publish("endpoint.deactivated", self.make_endpoint_message(sessid, endpoint))
        return ret
    
    def active_endpoints(self, sessid):
        key = self.make_session_key(sessid, "endpoints")
        return self.redis.smembers(key)
    
    def emit_to_endpoint(self, endpoint, sessid, event, *args, **kwargs):
        self.redis.publish("endpoint.event", self.make_endpoint_message(sessid, endpoint, event=event, args=args, kwargs = kwargs))
        
    def heartbeat_received(self, sessid):
        super(RedisSocketManager, self).heartbeat_received(sessid)
        self.redis.publish("heartbeat.received", self.make_heartbeat_message(sessid))
                    
    def heartbeat_sent(self, sessid):
        self.redis.publish("heartbeat.sent", self.make_heartbeat_message(sessid))
    
    def sync_listener(self):
        """Listens to a Redis PubSub for heartbeat messages."""
        pubsub = self.redis.pubsub()
        pubsub.psubscribe(['heartbeat.*', "endpoint.*"])
        
        for msg in pubsub.listen():
            handler = self.sync_handlers.get(msg.get('pattern'))
            if handler:
                handler(msg)
            
            gevent.sleep(0) 
            
    def make_heartbeat_message(self, sessid):
        return "%s:%s"%(self.uuid, sessid)
    
    def make_endpoint_message(self, sessid, endpoint, **kwargs):
        ret = dict(uuid = self.uuid, sessid = sessid, endpoint = endpoint, **kwargs)
            
        return json.dumps(ret)
        
    def on_heartbeat_sync(self, message):
        channel = message.get('channel')
        uuid, sessid =  message.get('data').split(":", 1)
        if channel == "hearbeat.received":
            if uuid != self.uuid:
                super(RedisSocketManager, self).heartbeat_received(sessid)
        elif channel == "hearbeat.sent":
            if uuid != self.uuid:
                socket = self.sockets.get(sessid)
                if socket:
                    socket.heartbeat_sent()
                    
    def on_endpoint_sync(self, message):
        channel = message.get('channel')
        if channel == "endpoint.deactivated":
            #disconnect the namespace
            msg = json.loads(message.get('data'))
            if msg.get('uuid') != self.uuid:
                socket = self.sockets.get(msg.get('sessid'))
                if socket:
                    ns = socket.active_ns.get(msg.get('endpoint'))
                    if ns:
                        #the sync sender should have sent a disconnect message to the client, so we keep it quiet
                        ns.disconnect(True)
        elif channel == "endpoint.event":
            msg = json.loads(message.get('data'))
            endpoint = msg.get('endpoint')
            sessid = msg.get('sessid')
            event = msg.get('event')
            args = msg.get('args')
            kwargs = msg.get('args')
            #use the non-distributed version
            super(RedisSocketManager, self).emit_to_endpoint(endpoint, sessid, event, *args, **kwargs)