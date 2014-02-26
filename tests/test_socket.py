from unittest import TestCase, main

from collections import defaultdict

from socketio.namespace import BaseNamespace
from socketio.virtsocket import Socket
from gevent.queue import Queue

class MockSocketManager(object):
    """Mock a SocketIO manager
    """
    def __init__(self, *args, **kwargs):
        self.sockets = {}
        self.ns_registry = defaultdict(set)

    def make_session(self, sessid):
        return {}
    
    def make_queue(self, sessid, name):
        return Queue()
    
    def deactivate_endpoint(self, sessid, endpoint):
        self.ns_registry[sessid].remove(endpoint)
    
    def activate_endpoint(self, sessid, endpoint):
        self.ns_registry[sessid].add(endpoint)
        
    def active_endpoints(self, sessid):
        return self.ns_registry[sessid]

    def detach(self, sessid):
        pass
    
class MockSocketIOServer(object):
    """Mock a SocketIO server"""
    def __init__(self, *args, **kwargs):
        self.manager = MockSocketManager()

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
        sessid = '12345678'
        self.virtsocket = Socket(sessid, self.server.manager, {})

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

    def test_incr_hits(self):
        self.virtsocket.state = "CONNECTED"

        # cause a hit
        self.virtsocket.incr_hits()
        self.assertEqual(self.virtsocket.hits, 1)
        self.assertEqual(self.virtsocket.state, self.virtsocket.STATE_CONNECTED)

    def test_disconnect(self):
        # kill connected socket
        namespaces = {'test': MockNamespace}
        self.virtsocket._set_namespaces(namespaces)
        environ = {'socketio': self.virtsocket}
        self.virtsocket._set_environ(environ)
        
        self.virtsocket.state = "CONNECTED"
        self.virtsocket.add_namespace('test')
        self.virtsocket.disconnect()
        self.assertEqual(self.virtsocket.state, "DISCONNECTING")
        self.assertEqual(self.virtsocket.active_ns, {})
        self.assertEqual(self.virtsocket.manager.active_endpoints(self.virtsocket.sessid), set())

    def test_kill(self):
        # kill connected socket
        namespaces = {'test': MockNamespace}
        self.virtsocket._set_namespaces(namespaces)
        environ = {'socketio': self.virtsocket}
        self.virtsocket._set_environ(environ)
        
        self.virtsocket.state = "CONNECTED"
        self.virtsocket.add_namespace('test')
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
