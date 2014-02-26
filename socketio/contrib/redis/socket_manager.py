import logging

import gevent
from gevent.queue import Empty
from redis.client import Redis

from socketio.contrib.redis.utils import RedisQueue, RedisMapping, GroupLock, DefaultDict
from socketio.socket_manager import BaseSocketManager
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
                k = k.replace("redis_", "", 1)
                if k == 'port':
                    v = int(v)
                redis_settings[k] = v
                
        self.redis_settings = redis_settings

        self.alive_key = "%s:alive" % self.prefix
        self.hits_key = "%s:hits" % self.prefix
        self.connected_key = "%s:connected" % self.prefix
        
        lock_factory = lambda sessid: GroupLock(self.redis, self.make_session_key(sessid, "lock"))
        self.locks = DefaultDict(lock_factory)
        self.uuid = str(uuid.uuid1())
        
        self.event_handlers = {
                              "socket.events": self.on_socket_event,
                              "endpoint.events": self.on_endpoint_event,
                              }
        
    def start(self):
        self.redis = Redis(**self.redis_settings)
        
        #start listening for syncing messages from other managers
        self.sync_job = gevent.spawn(self._redis_listener)
    
    def stop(self):
        self.sync_job.kill()
        self.redis = None
        
    def detach(self, sessid):
        #delete the session data from Redis
        self.redis.pipeline().delete(self.make_session_key(sessid, "session")).hdel(self.alive_key, sessid).execute()
        try:
            del self.locks[sessid]
        except KeyError:
            pass
        super(RedisSocketManager, self).detach(sessid)
        
    def make_session_key(self, sessid, suffix):
        return "%s%s:%s"%(self.prefix, sessid, suffix)
    
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
        try:
            ret += queue.get_all() #bulk reads the rest, if any
        except Empty:
            pass
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
        
    def is_handshaken(self, sessid):
        return bool(self.redis.hget(self.alive_key, sessid))
    
    def load_socket(self, socket):
        """Reads from Redis and sets any internal state of the socket that must 
        be shared between all sockets in the same session.
        """
        socket.hits = self.redis.hincrby(self.hits_key, socket.sessid, 1)
        if not socket.connection_established:
            connected = self.redis.sismember(self.connected_key, socket.sessid)
            if connected:
                self.init_connection(socket, nosync = True)
            
        return socket
                
    def save_socket(self, sessid):
        """Stores into Redis any internal state that must be shared between all sockets in the same session.
        """
        return
            
    def init_connection(self, socket, *args, **kwargs):
        super(RedisSocketManager, self).init_connection(socket, *args, **kwargs)
        if not kwargs.get('nosync', False):
            self.redis.sadd(self.connected_key, socket.sessid)
            
    def activate_endpoint(self, sessid, endpoint):
        key = self.make_session_key(sessid, "endpoints")
        self.redis.sadd(key, endpoint)
        self.notify_socket(sessid, "endpoint_activated", endpoint = endpoint)
    
    def deactivate_endpoint(self, sessid, endpoint):
        key = self.make_session_key(sessid, "endpoints")
        ret = self.redis.srem(key, endpoint) > 0
        if ret:#only notify if the endpoint was actually removed by this manager (or we'll get in infinite loop when disconnect triggers deactivate_endpoint)
            self.notify_socket(sessid, "endpoint_deactivated", endpoint = endpoint)
        return ret
    
    def active_endpoints(self, sessid):
        key = self.make_session_key(sessid, "endpoints")
        return self.redis.smembers(key)
    
    def notify_socket(self, sessid, event, *args, **kwargs):
        msg = json.dumps(dict(uuid = self.uuid, sessid = sessid, event=event, args=args, kwargs = kwargs))
        self.redis.publish("socket.events", msg)
        
    def notify_endpoint(self, endpoint, sessid, event, *args, **kwargs):
        msg = json.dumps(dict(uuid = self.uuid, endpoint = endpoint, sessid = sessid, event=event, args=args, kwargs = kwargs))
        self.redis.publish("endpoint.events", msg)
    
    def _redis_listener(self):
        """Listens to a Redis PubSub for event messages."""
        pubsub = self.redis.pubsub()
        pubsub.subscribe(self.event_handlers.keys())
        
        for msg in pubsub.listen():
            if msg.get('type') == 'message':
                handler = self.event_handlers.get(msg.get('channel'))
                if handler:
                    handler(msg)
            
            gevent.sleep(0) 
            
    def on_socket_event(self, message):
        """Receiving a socket event from the Redis channel.
        """
        msg = json.loads(message.get('data'))
        sessid = msg.get('sessid')
        event = msg.get('event')
        args = msg.get('args', [])
        kwargs = msg.get('kwargs', {})
        if msg.get('uuid') != self.uuid:
            if event in ('heartbeat_received', 'heartbeat_sent', 'endpoint_deactivated'):
                #global handling for special events from other managers
                socket = self.sockets.get(sessid)
                if socket:
                    if event == 'heartbeat_received':
                        socket.heartbeat()
                    elif socket == 'heartbeat_sent':
                        socket.heartbeat_sent()
                    elif socket == 'endpoint_deactivated':
                        endpoint = kwargs.get('endpoint')
                        ns = socket.active_ns.get(endpoint)
                        if ns:
                            #the sync sender should have sent a disconnect message to the client already, so we keep it quiet(= True)
                            ns.disconnect(True)
                    
        #notify the local listeners
        super(RedisSocketManager, self).notify_socket(sessid, event, *args, **kwargs)
                       
    def on_endpoint_event(self, message):
        """Receiving an endpoint event from the Redis channel.
        """
        msg = json.loads(message.get('data'))
        endpoint = msg.get('endpoint')
        sessid = msg.get('sessid')
        event = msg.get('event')
        args = msg.get('args', [])
        kwargs = msg.get('kwargs', {})
        #notify the local listeners
        super(RedisSocketManager, self).notify_endpoint(endpoint, event, *args, sender = sessid, **kwargs)