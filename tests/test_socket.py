from unittest import TestCase

from socketio.server import SocketIOServer
from socketio.virtsocket import Socket


class MockSocketIOServer(object):
    """
    Mock a SocketIO server.
    """
    def __init__(self, *args, **kwargs):
        self.sockets = {'1': Socket()}

    def get_socket(self, socket_id=''):
        return self.sockets.get(socket_id)


class MockSocketIOhandler(object):
    """
    Mock a SocketIO handler.
    """
    def __init__(self, *args, **kwargs):
        self.server = MockSocketIOServer()


class TestSocketAPI(TestCase):

    def setUp(self):
        self.server = MockSocketIOServer()
        self.virtsocket = Socket(self.server)

    def test__set_namespaces(self):
        namespaces = {'test': 'a'}
        self.virtsocket._set_namespaces(namespaces)
        self.asserEqual(self.virtsocket.namespaces, namespaces)

    def test__set_request(self):
        request = {'test': 'a'}
        self.virtsocket._set_request(request)
        self.asserEqual(self.virtsocket.request, request)
