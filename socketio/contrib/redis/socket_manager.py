import logging
import uuid
import json
import time
import random

import gevent
from gevent.queue import Empty
from redis.client import Redis

from socketio import virtsocket
from socketio.socket_manager import BaseSocketManager
from socketio.contrib.redis.utils import RedisQueue, RedisMapping, GroupLock, DefaultDict
from socketio.contrib.redis import lua_scripts

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
        
        self.prefix = self.settings.get("key_prefix", "socketio")
        self.buckets_count = self.settings.get("buckets_count", 1000)
        
        redis_settings = {}
        for k, v in self.settings.items():
            if k.startswith('redis_'):
                k = k.replace("redis_", "", 1)
                if k == 'port':
                    v = int(v)
                redis_settings[k] = v
                
        self.redis_settings = redis_settings
        
        self.connected_key = "%s:connected" % self.prefix
        
        lock_factory = lambda sessid: GroupLock(self.redis, self.make_session_key(sessid, "lock"))
        self.locks = DefaultDict(lock_factory)
        self.uuid = str(uuid.uuid1())
        
        self.event_handlers = {
                              "socket.events": self.on_socket_event,
                              "endpoint.events": self.on_endpoint_event,
                              }
        
        self.jobs = []
        
    def spawn(self, fn, *args, **kwargs):
        new = gevent.spawn(fn, *args, **kwargs)
        self.jobs.append(new)
        return new
    
    def start(self):
        self.redis = Redis(**self.redis_settings)
        
        self.script_bucket_hdel = self.redis.register_script(lua_scripts.LUA_BUCKET_HDEL)
        self.script_bucket_filter_lt = self.redis.register_script(lua_scripts.LUA_BUCKETS_FILTER_LT)
            
        self.spawn(self._redis_listener)
        self.spawn(self._orphan_cleaner)
    
    def stop(self):
        gevent.killall(self.jobs)
        self.redis = None
        
    def clean_redis(self, sessid, client = None):
        single = client is None
        if client is None:
            client = self.redis.pipeline()
        client.delete(self.make_session_key(sessid, "session"))
        client.delete(self.make_session_key(sessid, "lock"))
        client.delete(self.make_session_key(sessid, "endpoints"))
        for qname in virtsocket.QUEUE_NAMES:
            client.delete(self.make_session_key(sessid, "queue:%s" % qname))
        
        self.bucket_hdel("alive", sessid, client = client)
        self.bucket_hdel('hits', sessid, client = client)
        client.srem(self.connected_key, sessid)
        if single:
            client.execute()
            
    def detach(self, sessid):
        super(RedisSocketManager, self).detach(sessid)
        self.clean_redis(sessid)
        try:
            del self.locks[sessid]
        except KeyError:
            pass
       
    def make_buckets_type(self, name):
        return "%s:buckets:%s" % (self.prefix, name)
        
    def make_bucket_name(self, key, sessid):
        return "%s:%s:b%s" % (self.prefix, key, self.bucket_id(sessid))
    
    def make_session_key(self, sessid, suffix):
        return "%s:%s:%s"%(self.prefix, sessid, suffix)
    
    def make_queue(self, sessid, name):
        """Returns a Redis based message queue.
        """
        return RedisQueue(self.redis, self.make_session_key(sessid, "queue:%s" % name))
    
    def bucket_id(self, sessid):
        """Returns the id of the corresponding bucket for a socket
        
        We'll keep socket hashed data in buckets.
        As we use random sessid these should be normally be quite sparse.
        """
        nid = int(sessid.lstrip("0") or 0)
        return str(nid % self.buckets_count)
    
    def bucket_hset(self, key, sessid, value, client = None):
        """Set the value in the corresponding bucket hash and (atomically) register the bucket.
        
        If `client` is given and `client` is a pipeline it's the responsibility of the caller
        to call execute()!
        """
        single = client is None
        if client is None:
            client = self.redis.pipeline()
        bname = self.make_bucket_name(key, sessid)
        client.hset(bname, sessid, value) 
        btype = self.make_buckets_type(key)
        client.sadd(btype, bname)
        if single:
            client.execute()
            
    def bucket_hincrby(self, key, sessid, value, client = None):
        """Increment the value in the corresponding bucket and (atomically) register the bucket.
        
        If `client` is given and `client` is a pipeline it's the responsibility of the caller
        to call execute()!
        """
        single = client is None
        if client is None:
            client = self.redis.pipeline()
        bname = self.make_bucket_name(key, sessid)
        client.hincrby(bname, sessid, value) 
        btype = self.make_buckets_type(key)
        client.sadd(btype, bname)
        if single:
            client.execute()
            
    def bucket_hget(self, key, sessid, client = None):
        """Returns the value from the bucket corresponding to the given socket.
        """
        if client is None:
            client = self.redis
        bname = self.make_bucket_name(key, sessid)
        return client.hget(bname, sessid)
        
    def bucket_hdel(self, key, sessid, client = None):
        """Delete a value for the given socket from the corresponding bucket and (atomically) unregister the bucket if it's empty.
        """
        single = client is None
        if client is None:
            client = self.redis.pipeline()
        bname = self.make_bucket_name(key, sessid)
        btype = self.make_buckets_type(key)
        self.script_bucket_hdel(keys = [bname, btype], args = [sessid], client = client)
        if single:
            client.execute()
    
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

    def heartbeat_received(self, sessid):
        """Called when a heartbeat for the given socket arrives.
        """
        socket = self.sockets.get(sessid)
        if socket:
            self.bucket_hset("alive", sessid, str(time.time()))
        super(RedisSocketManager, self).heartbeat_received(sessid)
            
    def handshake(self, sessid):
        """Don't create the socket yet, just mark the session as existing.
        """
        self.bucket_hset("alive", sessid, str(time.time()))
        
    def is_handshaken(self, sessid):
        return bool(self.bucket_hget("alive", sessid))
    
    def load_socket(self, socket):
        """Reads from Redis and sets any internal state of the socket that must 
        be shared between all sockets in the same session.
        """
        socket.hits = self.bucket_hincrby("hits", socket.sessid, 1)
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
        uuid = msg.get('uuid')
        if uuid != self.uuid:
            #global handling for special events from other managers
            if event in ('heartbeat_received', 'heartbeat_sent', 'endpoint_deactivated'):
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
        
    def _orphan_cleaner(self):
        """This will check and cleanup sockets' data that is left orphaned in Redis due to sockets somehow not being 
        disconnected properly, the most obvious case being a server crash.
        
        The algorithm is to poke randomly around the socket buckets, small batches at a time, and clean up whatever is found.
        This is not a replacement for proper heartbeat and disconnect cleanup logic.
        """
        timeout = float(self.config['heartbeat_timeout'])
        lock_timeout = 5 #Should finish in less than 5 sec (hopefully much, much faster) or lock gets released
        interval = float(self.settings.get('orphan_cleaner_interval', 1.2 * timeout))
        interval *= (0.9 + 0.2 * random.random()) #between 90% and 110% so not all managers check at the same time
        lock_name = "%s:orphan.cleaner" % self.prefix
        batch_size = int(float(self.settings.get('orphan_cleaner_batch', 0.1)) * self.buckets_count)
        limit = int(self.settings.get('orphan_cleaner_limit', 100))#max number of orphans to cleanup at once
        while True:
            next_interval = interval
            with self.redis.lock(lock_name, timeout = lock_timeout):#one check at a time across all workers
                #get a random subset of buckets
                buckets = self.redis.srandmember(self.make_buckets_type('alive'), batch_size)
                if buckets:
                    delta = int(time.time()) - timeout - 1
                    orphans = self.script_bucket_filter_lt(keys = buckets, args = [delta, limit])
                    if orphans:
                        next_interval = 0#there are orphans, so don't wait until it all looks clean again
                        logger.warning('Cleaning up %s orphaned sockets...' % len(orphans))
                        with self.redis.pipeline() as pipe:
                            for sessid in orphans:
                                self.clean_redis(sessid, pipe)
                            pipe.execute()
                        for sessid in orphans:
                            self.notify_socket(sessid, 'dead')
            gevent.sleep(next_interval)