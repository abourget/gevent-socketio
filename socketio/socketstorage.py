import collections
import redis
import pickle

class Redis(collections.MutableMapping):
    hash_name = "socketio.socketstorage.redis"

    def __init__(self, *args, **kwargs):
        self.conn = redis.StrictRedis(**kwargs)

    def __setitem__(self, key, value):
        if key is None or key == '':
            return None

        self.conn.hset(self.hash_name, key, pickle.dumps(value))

    def __getitem__(self, key):
        if key is None or key == '':
            return None

        val = self.conn.hget(self.hash_name, key)
        if val is None:
            return val

        return pickle.loads(val)

    def __delitem__(self, key):
        if key is None or key == '':
            return None

        self.conn.hdel(self.hash_name, key)

    def __iter__(self):
        return iter(self.conn.hkeys(self.hash_name))

    def __contains__(self, key):
        return self.conn.hexists(self.hash_name, key)

    def __len__(self):
        return self.conn.hlen(self.hash_name)
