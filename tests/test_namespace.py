from unittest import TestCase, main

from socketio.namespace import BaseNamespace


class MockSocket(object):

    def __init__(self, environ={}):
        self.environ = environ

    def error(self, error_name, error_msg, endpoint, msg_id, quiet=False):
        return (error_name, error_msg, endpoint, msg_id)

class TestBaseNamespace(TestCase):

    def setUp(self):
        self.environ = {}
        self.environ['socketio'] = MockSocket()
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

if __name__ == '__main__':
    main()
