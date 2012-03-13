import unittest

from socketio.server import SocketIOServer
from socketio.socket import Socket


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


class TestMessageAPI(TestCase):

    def setUp(self):
        self.handler = MockSocketIOhandler()
        self.protocol = SocketIOProtocol(self.handler)
        self.protocol.socket = self.handler.server.get_socket('1')

    def test_connnect(self):
        """
        '1::' [path] [query]
        """
        self.protocol.connect('')
        pass

    def test_emit(self):
        """
        An event is like a json message, but has mandatory name and args fields.
        name is a string and args an array.

        An event is sent through the emit method.

        '5:' [message id ('+')] ':' [message endpoint] ':' [json encoded event]
        """
        self.protocol.emit('open')
        self.assertEquals(self.protocol.socket.get_client_msg(), '5::open:')

    def test_ack(self):
        """
        '6:::' [message id] '+' [data]
        """
        # simple ack
        self.protocol.ack(140)
        self.assertEquals(self.protocol.socket.get_client_msg(), '6:::4')
        
        # complex ack with args
        self.protocol.ack(12, ['A', 'B'])
        self.assertEquals(self.protocol.socket.get_client_msg(), 
                          '6:::4+["A","B"]')

    def test_error(self):
        """
        '7::' [endpoint] ':' [reason] '+' [advice]
        """
        self.protocol.send_error()
        self.assertEquals(self.protocol.socket.get_client_msg(), '7:::')

        self.protocol.send_error(0)
        self.assertEquals(self.protocol.socket.get_client_msg(), '7:::0')

        self.protocol.send_error(1)
        self.assertEquals(self.protocol.socket.get_client_msg(), '7:::2+0')

        self.protocol.send_error('/woot')
        self.assertEquals(self.protocol.socket.get_client_msg(), '7:::/woot')
