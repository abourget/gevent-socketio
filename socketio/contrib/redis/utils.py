import json
import collections

from gevent.queue import Empty
        
class RedisQueue(object):
    """Simple queue on top of Redis following the ``gevent.Queue`` interface."""
    
    def __init__(self, redis, name):
        self.redis = redis
        self.name = name

    def copy(self):
        """Copy makes no sense as the name (i.e. the Redis' list key) must be the same
        """
        raise NotImplementedError("RedisQueue doesn't support copy()")
    
    def qsize(self):
        """Return the size of the queue."""
        return self.redis.llen(self.name)

    def empty(self):
        """Return True if the queue is empty, False otherwise."""
        return self.qsize() == 0
    
    def full(self):
        """Never full"""
        return False 

    def put(self, item, *args, **kwargs):
        """Put item into the queue."""
        self.redis.rpush(self.name, item)

    def put_nowait(self, item):
        """Put item into the queue."""
        self.put(item)
    
    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue.

        If optional argument ``block`` is true and ``timeout`` is None (the default), block if necessary 
        until an item is available. If ``timeout`` is a positive number, it blocks at most timeout 
        seconds and returns None after. 
        
        Otherwise (``block`` is false), return an item if one is immediately available, else return None 
        (``timeout`` is ignored in that case).
        """
        if block:
            item = self.redis.blpop(self.key, timeout=timeout)
        else:
            item = self.redis.lpop(self.key)

        if item:
            return item[1]
        else:
            raise Empty

    def get_nowait(self):
        """Remove and return an item from the queue without blocking.

        Only get an item if one is immediately available. Otherwise return None.
        """
        return self.get(False)
    
    def get_all(self):
        """Remove and return all items currently in the queue.
        """
        pipe = self.redis.pipeline()
        ret = pipe.lrange(0, -1).ltrim(0, -1).execute()
        ret = ret[0]
        if not ret:
            raise Empty
        return ret
    
    def peek(self, block=True, timeout=None):
        """Return an item from the queue without removing it.
        
        If optional argument ``block`` is true and ``timeout`` is None (the default), block if necessary until an item is available. 
        If ``timeout`` is a positive number, it blocks at most ``timeout`` seconds and returns None if no item was available within 
        that time. 
        
        Otherwise (``block`` is false), return an item if one is immediately available, else return None (``timeout`` is ignored in that case).
        """
        if not block:
            return self.peek_nowait()
        else:
            #Kinda ugly, pop and then push back.
            #@todo Maybe implement using Lua or something if it's used frequently
            item = self.get(block, timeout)
            if item:
                self.redis.lpush(self.name, item)
                return item
            else:
                raise Empty
    
    def peek_nowait(self):
        """Return an item from the queue without removing it and without blocking."""
        ret = self.redis.lindex(self.name, 0)
        if ret:
            return ret
        else:
            raise Empty
    
    def __iter__(self):
        return self

    def next(self):
        try:
            return self.get_nowait()
        except Empty:
            raise StopIteration
    
class RedisMapping(collections.MutableMapping):
    """A map-like object backed by Redis. 
    
    Uses the ``json`` module to serialize the stored values to a string.
    """
    def __init__(self, redis, name):
        self.redis = redis
        self.name = name

    def __setitem__(self, key, value):
        if not key:
            return None

        self.redis.hset(self.name, key, json.dumps(value))

    def __delitem__(self, key):
        if not key:
            return None

        self.conn.hdel(self.hash_name, key)

    def __getitem__(self, key):
        if not key:
            return None

        ret = self.redis.hget(self.name, key)
        if ret:
            ret = json.loads(ret)
        return ret

    def __iter__(self):
        return iter(self.redis.hkeys(self.name))

    def __contains__(self, key):
        return self.redis.hexists(self.name, key)

    def __len__(self):
        return self.redis.hlen(self.name)