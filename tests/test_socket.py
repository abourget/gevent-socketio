from unittest import TestCase, main

from socketio.namespace import BaseNamespace
from socketio.virtsocket import Socket


class MockSocketIOServer(object):
    """Mock a SocketIO server"""
    def __init__(self, *args, **kwargs):
        self.sockets = {}

    def get_socket(self, socket_id=''):
        return self.sockets.get(socket_id)


class MockSocketIOhandler(object):
    """Mock a SocketIO handler"""
    def __init__(self, *args, **kwargs):
        self.server = MockSocketIOServer()


class MockNamespace(BaseNamespace):
    """Mock a Namespace from the namespace module"""
    pass


class TestSocketAPI(TestCase):
    """Test the virtual Socket object"""

    def setUp(self):
        self.server = MockSocketIOServer()
        self.virtsocket = Socket(self.server, {})

    def test__set_namespaces(self):
        namespaces = {'/': MockNamespace}
        self.virtsocket._set_namespaces(namespaces)
        self.assertEqual(self.virtsocket.namespaces, namespaces)

    def test__set_request(self):
        request = {'test': 'a'}
        self.virtsocket._set_request(request)
        self.assertEqual(self.virtsocket.request, request)

    def test__set_environ(self):
        environ = []
        self.virtsocket._set_environ(environ)
        self.assertEqual(self.virtsocket.environ, environ)

    def test_connected_property(self):
        # not connected
        self.assertFalse(self.virtsocket.connected)
        
        # connected
        self.virtsocket.state = "CONNECTED"
        self.assertTrue(self.virtsocket.connected)

    def test_incr_hist(self):
        self.virtsocket.state = "CONNECTED"

        # cause a hit
        self.virtsocket.incr_hits()
        self.assertEqual(self.virtsocket.hits, 1)
        self.assertEqual(self.virtsocket.state, self.virtsocket.STATE_CONNECTED)

    def test_disconnect(self):
        # kill connected socket
        self.virtsocket.state = "CONNECTED"
        self.virtsocket.active_ns = {'test' : MockNamespace({'socketio': self.virtsocket}, 'test')}
        self.virtsocket.disconnect()
        self.assertEqual(self.virtsocket.state, "DISCONNECTING")
        self.assertEqual(self.virtsocket.active_ns, {})

    def test_kill(self):
        # kill connected socket
        self.virtsocket.state = "CONNECTED"
        self.virtsocket.active_ns = {'test' : MockNamespace({'socketio': self.virtsocket}, 'test')}
        self.virtsocket.kill()
        self.assertEqual(self.virtsocket.state, "DISCONNECTING")

    def test__receiver_loop(self):
        """Test the loop  """
        # most of the method is tested by test_packet.TestDecode and
        # test_namespace.TestBaseNamespace
        pass
        # self.virtsocket._receiver_loop()
        # self.virtsocket.server_queue.put_nowait_msg('2::')


if __name__ == '__main__':
    main()
