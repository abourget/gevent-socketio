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
    def __init__(self, *args, **kwargs):
        self.use_set = args[0]

        super(ChatNamespace, self).__init__(*args[1:], **kwargs)

    def get_initial_acl(self):
        acls = ['on_foo']

        if self.use_set == True:
            return set(acls)
        else:
            return acls

    def on_foo(self):
        return 'a'

    def on_bar(self):
        return 'b'

    def on_baz(foo, bar, baz):
        return 'c'

class GlobalNamespace(BaseNamespace):
    def on_woot(self):
        return ''

    def on_tobi(self):
        return ''

class TestBaseNamespace(TestCase):
    def setUp(self):
        server = MockSocketIOServer()
        self.environ = {}
        socket = MockSocket(server, {})
        socket.error = MagicMock()
        self.environ['socketio'] = socket
        self.ns = GlobalNamespace(self.environ, '/woot')

    def test_process_packet_disconnect(self):
        pkt = {'type': 'disconnect',
               'endpoint': '/woot'
               }
        self.ns.process_packet(pkt)
        assert not self.environ['socketio'].error.called

    def test_process_packet_connect(self):
        """processing a connection packet """
        pkt = {'type': 'connect',
               'endpoint': '/tobi',
               'qs': ''
               }
        self.ns.process_packet(pkt)
        assert not self.environ['socketio'].error.called

        # processing a connection packet with query string
        pkt = {'type': 'connect',
               'endpoint': '/test',
               'qs': '?test=1'
               }
        self.ns.process_packet(pkt)
        assert not self.environ['socketio'].error.called

    def test_process_packet_heartbeat(self):
        """processing a heartbeat packet """

        pkt = {'type': 'heartbeat',
               'endpoint': ''
               }
        self.ns.process_packet(pkt)
        assert not self.environ['socketio'].error.called

    def test_process_packet_message(self):
        """processing a message packet """

        pkt = {'type': 'message',
               'endpoint': '',
               'data': 'woot'}
        data = self.ns.process_packet(pkt)
        self.assertEqual(data, pkt['data'])
        assert not self.environ['socketio'].error.called

        # processing a message packet with id and endpoint
        pkt = {'type': 'message',
               'id': 5,
               'ack': True,
               'endpoint': '/tobi',
               'data': ''}
        data = self.ns.process_packet(pkt)
        self.assertEqual(data, pkt['data'])
        assert not self.environ['socketio'].error.called

    def test_process_packet_json(self):
        """processing json packet """
        pkt = {'type': 'json',
               'endpoint': '',
               'data': '2'}
        data = self.ns.process_packet(pkt)
        self.assertEqual(data, pkt['data'])
        assert not self.environ['socketio'].error.called

    # processing json packet with message id and ack data
        pkt = {'type': 'json',
               'id': 1,
               'endpoint': '',
               'ack': 'data',
               'data': {u'a': u'b'}}
        data = self.ns.process_packet(pkt)
        self.assertEqual(data, pkt['data'])
        assert not self.environ['socketio'].error.called

    def test_process_packet_event(self):
        """processing an event packet """
        pkt = {'type': 'event',
               'name': 'woot',
               'endpoint': '',
               'args': []}
        self.ns.process_packet(pkt)
        assert not self.environ['socketio'].error.called

        # processing an event packet with message id and ack
        pkt = {'type': 'event',
               'id': 1,
               'ack': 'data',
               'name': 'tobi',
               'endpoint': '',
               'args': []}
        self.ns.process_packet(pkt)
        assert not self.environ['socketio'].error.called

    def test_process_packet_ack(self):
        """processing a ack packet """
        pkt = {'type': 'ack',
               'ackId': 140,
               'endpoint': '',
               'args': []}
        self.ns.process_packet(pkt)
        assert not self.environ['socketio'].error.called

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
        assert not self.environ['socketio'].error.called

    def test_del_acl_method(self):
        pkt = {'type': 'event',
               'name': 'foo',
               'endpoint': '/chat',
               'args': []}

        message =  ("Trying to delete an ACL method, but none were"
                + " defined yet! Or: No ACL restrictions yet, why would you"
                + " delete one?")
        try:
            self.ns.del_acl_method('on_foo')
            self.ns.process_packet(pkt)
        except ValueError as e:
            self.assertEqual(
                message,
                e.message,
            )
        else:
            raise Exception("""We should not be able to delete an acl that
            doesn't exist""")

    def test_allowed_event_name_regex(self):
        pkt = {'type': 'event',
               'name': '$foo',
               'endpoint': '/chat',
               'args': []}

        self.ns.process_packet(pkt)
        args = ['unallowed_event_name',
                'name must only contains alpha numerical characters',
                ]
        kwargs = dict(msg_id=None, endpoint='/woot', quiet=False)

        self.environ['socketio'].error.assert_called_with(*args, **kwargs)

    def test_method_not_found(self):
        """ test calling a method that doesn't exist """

        pkt = {'type': 'event',
               'name': 'foo',
               'endpoint': '/chat',
               'args': []
               }

        self.ns.process_packet(pkt)

        kwargs = dict(
            msg_id=None,
            endpoint='/woot',
            quiet=False
        )

        self.environ['socketio'].error.assert_called_with(
            'no_such_method',
            'The method "%s" was not found' % 'on_foo',
            **kwargs
        )

class TestChatNamespace(TestCase):
    def setUp(self):
        server = MockSocketIOServer()
        self.environ = {}
        socket = MockSocket(server, {})
        socket.error = MagicMock()
        self.environ['socketio'] = socket
        self.ns = ChatNamespace(
            False,
            self.environ,
            '/chat'
        )

    def test_allowed_event(self):
        pkt = {'type': 'event',
               'name': 'foo',
               'endpoint': '/chat',
               'args': []}
        self.ns.process_packet(pkt)
        assert not self.environ['socketio'].error.called

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

    def test_add_acl_method(self):
        pkt = {'type': 'event',
               'name': 'bar',
               'endpoint': '/chat',
               'args': []}

        self.ns.add_acl_method('on_bar')

        self.ns.process_packet(pkt)

        assert not self.environ['socketio'].error.called

    def test_del_acl_method(self):
        pkt = {'type': 'event',
               'name': 'foo',
               'endpoint': '/chat',
               'args': []}

        self.ns.del_acl_method('on_foo')

        self.ns.process_packet(pkt)

        args = [ 
                'method_access_denied',
                'You do not have access to method "on_foo"',
        ]

        kwargs = dict(
                msg_id=None,
                endpoint='/chat',
                quiet=False
        )

        self.environ['socketio'].error.assert_called_with(*args, **kwargs)

    def test_lift_acl_restrictions(self):
        pkt1 = {'type': 'event',
               'name': 'foo',
               'endpoint': '/chat',
               'args': []}

        self.ns.lift_acl_restrictions()

        self.ns.process_packet(pkt1)

        assert not self.environ['socketio'].error.called

        pkt2 = {'type': 'event',
               'name': 'bar',
               'endpoint': '/chat',
               'args': []}

        self.ns.process_packet(pkt2)

        assert not self.environ['socketio'].error.called

    def test_use_set_on_acl(self):
        self.ns = ChatNamespace(
            True,
            self.environ,
            '/chat'
        )

        pkt = {'type': 'event',
               'name': 'bar',
               'endpoint': '/chat',
               'args': []}

        self.ns.add_acl_method('on_bar')

        self.ns.process_packet(pkt)

        assert not self.environ['socketio'].error.called

    def test_call_method_invalid_definition(self):
        pkt = {'type': 'event',
               'name': 'baz',
               'endpoint': '/chat',
               'args': []}

        self.ns.add_acl_method('on_baz')

        self.ns.process_packet(pkt)
        kwargs = dict(msg_id=None, endpoint='/chat', quiet=False)
        self.environ['socketio'].error.assert_called_with(
            "invalid_method_args",
            "The server-side method is invalid, as it doesn't "
            "have 'self' as its first argument"
        , **kwargs)

if __name__ == '__main__':
    main()
