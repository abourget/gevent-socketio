import redis

from unittest import TestCase, main
from socketio import socketstorage

class TestRedis(TestCase):
    def setUp(self):
        kwargs = {
            'host': 'localhost',
            'port': 6379,
            # XXX : yes, arbitrary
            'db': 5,
        }
        self.conn = redis.StrictRedis(**kwargs)
        self.storage = socketstorage.Redis(**kwargs)

    def tearDown(self):
        self.conn.flushdb()

    def test_set_get_del_contains_len(self):
        key = "foo"
        value = {"a": 1, "b": "foo"}

        self.storage[key] = value
        self.assertEqual(len(self.storage), 1)
        self.assertEqual(self.storage[key], value)

        self.assertTrue(key in self.storage)

        del self.storage[key]
        self.assertEqual(len(self.storage), 0)

    def test_loop(self):
        values = {
            "foo": "bar",
            "bar": "baz",
        }

        for k, v in values.iteritems():
            self.storage[k] = v

        obtained = {}
        for k, v in self.storage.iteritems():
            obtained[k] = v

        self.assertEqual(obtained, values)

if __name__ == '__main__':
    main()

