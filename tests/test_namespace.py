from unittest import TestCase, main

from socketio.namespace import BaseNamespace
from socketio.virtsocket import Socket
from mock import MagicMock


class MockSocketIOServer(object):
    """Mock a SocketIO server"""
    def __init__(self, *args, **kwargs):
        self.sockets = {}

    def get_socket(self, socket_id=''):
        return self.sockets.get(socket_id)


class MockSocket(Socket):
    pass

class ChatNamespace(BaseNamespace):
    def get_initial_acl(self):
        return 'on_foo'

    def on_foo(self):
        return 'a'

    def on_bar(self):
        return 'b'

class TestBaseNamespace(TestCase):
    def setUp(self):
        server = MockSocketIOServer()
        self.environ = {}
        self.environ['socketio'] = MockSocket(server)
        self.ns = BaseNamespace(self.environ, '/woot')

    def test_process_packet_disconnect(self):
        pkt = {'type': 'disconnect',
               'endpoint': '/woot'
               }
        self.ns.process_packet(pkt)

    def test_process_packet_connect(self):
        """processing a connection packet """
        pkt = {'type': 'connect',
               'endpoint': '/tobi',
               'qs': ''
               }
        self.ns.process_packet(pkt)

        # processing a connection packet with query string
        pkt = {'type': 'connect',
               'endpoint': '/test',
               'qs': '?test=1'
               }
        self.ns.process_packet(pkt)

    def test_process_packet_heartbeat(self):
        """processing a heartbeat packet """

        pkt = {'type': 'heartbeat',
               'endpoint': ''
               }
        self.ns.process_packet(pkt)

    def test_process_packet_message(self):
        """processing a message packet """

        pkt = {'type': 'message',
               'endpoint': '',
               'data': 'woot'}
        data = self.ns.process_packet(pkt)
        self.assertEqual(data, pkt['data'])

        # processing a message packet with id and endpoint
        pkt = {'type': 'message',
               'id': 5,
               'ack': True,
               'endpoint': '/tobi',
               'data': ''}
        data = self.ns.process_packet(pkt)
        self.assertEqual(data, pkt['data'])

    def test_process_packet_json(self):
        """processing json packet """
        pkt = {'type': 'json',
               'endpoint': '',
               'data': '2'}
        data = self.ns.process_packet(pkt)
        self.assertEqual(data, pkt['data'])

    # processing json packet with message id and ack data
        pkt = {'type': 'json',
               'id': 1,
               'endpoint': '',
               'ack': 'data',
               'data': {u'a': u'b'}}
        data = self.ns.process_packet(pkt)
        self.assertEqual(data, pkt['data'])

    def test_process_packet_event(self):
        """processing an event packet """
        pkt = {'type': 'event',
               'name': 'woot',
               'endpoint': '',
               'args': []}
        self.ns.process_packet(pkt)

        # processing an event packet with message id and ack
        pkt = {'type': 'event',
               'id': 1,
               'ack': 'data',
               'name': 'tobi',
               'endpoint': '',
               'args': []}
        self.ns.process_packet(pkt)

    def test_process_packet_ack(self):
        """processing a ack packet """
        pkt = {'type': 'ack',
               'ackId': 140,
               'endpoint': '',
               'args': []}
        self.ns.process_packet(pkt)

    def test_process_packet_error(self):
        """processing error packet """
        pkt = {'type': 'error',
               'reason': '',
               'advice': '',
               'endpoint': ''}
        self.ns.process_packet(pkt)

        pkt = {'type': 'error',
               'reason': 'transport not supported',
               'advice': '',
               'endpoint': ''}
        self.ns.process_packet(pkt)

        # processing error packet with reason and advice
        pkt = {'type': 'error',
               'reason': 'unauthorized',
               'advice': 'reconnect',
               'endpoint': ''}
        self.ns.process_packet(pkt)

        # processing error packet with endpoint
        pkt = {'type': 'error',
               'reason': '',
               'advice': '',
               'endpoint': '/woot'}
        self.ns.process_packet(pkt)

    def test_process_packet_message_with_new_line(self):
        """processing a newline in a message"""
        pkt = {'type': 'message',
               'data': '\n',
               'endpoint': ''}
        self.ns.process_packet(pkt)

class TestChatNamespace(TestCase):
    def setUp(self):
        server = MockSocketIOServer()
        self.environ = {}
        socket = MockSocket(server)
        socket.error = MagicMock()
        self.environ['socketio'] = socket
        self.ns = ChatNamespace(
            self.environ,
            '/chat'
        )

    def test_allowed_event(self):
        pkt = {'type': 'event',
               'name': 'foo',
               'endpoint': '/chat',
               'args': []}
        self.ns.process_packet(pkt)

    def test_blocked_event(self):
        pkt = {'type': 'event',
               'name': 'bar',
               'endpoint': '/chat',
               'args': []}

        self.ns.process_packet(pkt)

        args = [ 
                'method_access_denied',
                'You do not have access to method "on_bar"',
        ]

        kwargs = dict( 
                msg_id=None,
                endpoint='/chat',
                quiet=False
        )

        self.environ['socketio'].error.assert_called_with(*args, **kwargs)

if __name__ == '__main__':
    main()
