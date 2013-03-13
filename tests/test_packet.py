"""
Tests based on the Socket.IO spec: https://github.com/LearnBoost/socket.io-spec
"""

from unittest import TestCase, main

from socketio.packet import encode, decode
import decimal

class TestEncodeMessage(TestCase):

    def test_encode_disconnect(self):
        """encoding a disconnection packet """
        encoded_message = encode({'type': 'disconnect',
                                  'endpoint': '/woot'
                                  })
        self.assertEqual(encoded_message, '0::/woot')

    def test_encode_connect(self):
        """encoding a connection packet """

        encoded_message = encode({'type': 'connect',
                                  'endpoint': '/tobi',
                                  'qs': '',
                                  })
        self.assertEqual(encoded_message, '1::/tobi')

        # encoding a connection packet with query string
        encoded_message = encode({'type': 'connect',
                                  'endpoint': '/test',
                                  'qs': '?test=1'
                                  })
        self.assertEqual(encoded_message, '1::/test:?test=1')

    def test_encode_heartbeat(self):
        """encoding a connection packet """
        encoded_message = encode({'type': 'heartbeat',
                                  'endpoint': ''
                                  })
        self.assertEqual(encoded_message, '2::')

    def test_encode_message(self):
        """encoding a message packet """        
        encoded_message = encode({'type': 'message',
                                  'endpoint': '',
                                  'data': 'woot'
                                  })
        self.assertEqual(encoded_message, '3:::woot')

        # encoding a message packet with id and endpoint
        encoded_message = encode({'type': 'message',
                                  'endpoint': '/tobi',
                                  'id': 5,
                                  'ack': True,
                                  'data': ''
                                  })
        self.assertEqual(encoded_message, '3:5:/tobi')

    def test_encode_json(self):
        """encoding JSON packet """
        encoded_message = encode({'type': 'json',
                                  'endpoint': '',
                                  'data': '2'
                                  })
        self.assertEqual(encoded_message, '4:::"2"')

        # encoding json packet with message id and ack data
        encoded_message = encode({'type': 'json',
                                  'id': 1,
                                  'ack': 'data',
                                  'endpoint': '',
                                  'data': {'a' : 'b'}
                                  })
        self.assertEqual(encoded_message, '4:1+::{"a":"b"}')

    def test_encode_json_decimals(self):
        """encoding JSON packet with a decimal"""
        # encoding json packet with message id and ack data
        encoded_message = encode({'type': 'json',
                                  'id': 1,
                                  'ack': 'data',
                                  'endpoint': '',
                                  'data': {'a' : decimal.Decimal('%f' % (0.5))}
                                  })
        self.assertEqual(encoded_message, '4:1+::{"a":0.5}')


    def test_encode_event(self):
        """encoding an event packet """
        encoded_message = encode({'type': 'event',
                                  'endpoint': '',
                                  'name': 'woot',
                                  'args': []
                                  })
        self.assertEqual(encoded_message, '5:::{"name":"woot"}')

        # encoding an event packet with message id and ack
        encoded_message = encode({'type': 'event',
                                  'name': 'tobi',
                                  'id': 1,
                                  'ack': True,
                                  'data': ''
                                  })
        self.assertEqual(encoded_message, '5:1::{"name":"tobi"}')

        # encoding an event packet with message id and ack = 'data'
        encoded_message = encode({'type': 'event',
                                  'name': 'tobi',
                                  'id': 1,
                                  'ack': 'data',
                                  'data': ''
                                  })
        self.assertEqual(encoded_message, '5:1+::{"name":"tobi"}')

        # encoding an event packet with data
        encoded_message = encode({'type': 'event',
                                  'name': 'edwald',
                                  'ack': True,
                                  'endpoint': '',
                                  'args': [{"a":"b"}, 2,"3"]
                                  })
        self.assertEqual(encoded_message,
                          '5:::{"args":[{"a":"b"},2,"3"],"name":"edwald"}')

    def test_encode_ack(self):
        """encoding ack packet """
        encoded_message = encode({'type': 'ack',
                                              'ackId': 140,
                                  'endpoint': '',
                                  'args': []
                                  })
        self.assertEqual(encoded_message, '6:::140')

        # encoding ack packet with args
        encoded_message = encode({'type': 'ack',
                                  'ackId': 12,
                                  'endpoint': '',
                                  'args': ["woot","wa"]
                                  })
        self.assertEqual(encoded_message, '6:::12+["woot","wa"]')

        # encoding ack packet with args and endpoint
        encoded_message = encode({'type': 'ack',
                                  'ackId': 12,
                                  'endpoint': '/chat',
                                  'args': ["woot","wa"]
                                  })
        self.assertEqual(encoded_message, '6::/chat:12+["woot","wa"]')

    def test_encode_error(self):
        """encoding error packet """
        encoded_message = encode({'type': 'error',
                                  'reason': '',
                                  'advice': '',
                                  'endpoint': ''
                                  })
        self.assertEqual(encoded_message, '7:::')

        # encoding error packet with reason
        encoded_message = encode({'type': 'error',
                                  'reason': 'transport not supported',
                                  'advice': '',
                                  'endpoint': ''
                                  })
        self.assertEqual(encoded_message, '7:::0')

        # encoding error packet with reason and advice
        encoded_message = encode({'type': 'error',
                                  'reason': 'unauthorized',
                                  'advice': 'reconnect',
                                  'endpoint': ''
                                  })
        self.assertEqual(encoded_message, '7:::2+0')

        # encoding error packet with endpoint
        encoded_message = encode({'type': 'error',
                                  'reason': '',
                                  'advice': '',
                                  'endpoint': '/woot'
                                  })
        self.assertEqual(encoded_message, '7:::/woot')

    def test_encode_noop(self):
        """encoding a noop packet """
        encoded_message = encode({'type': 'noop',
                                  'endpoint': '',
                                  'data': ''
                                  })
        self.assertEqual(encoded_message, '8::')


class TestDecodeMessage(TestCase):
    
    def test_decode_deconnect(self):
        """decoding a disconnection packet """
        decoded_message = decode('0::/woot')
        self.assertEqual(decoded_message, {'type': 'disconnect',
                                           'endpoint': '/woot'
                                           })
        
    def test_decode_connect(self):
        """decoding a connection packet """
        decoded_message = decode('1::/tobi')
        self.assertEqual(decoded_message, {'type': 'connect',
                                           'endpoint': '/tobi',
                                           'qs': ''
                                           })

        # decoding a connection packet with query string
        decoded_message = decode('1::/test:?test=1')
        self.assertEqual(decoded_message, {'type': 'connect',
                                           'endpoint': '/test',
                                           'qs': '?test=1'
                                           })

    def test_decode_heartbeat(self):
        """decoding a heartbeat packet """
        decoded_message = decode('2:::')
        self.assertEqual(decoded_message, {'type': 'heartbeat',
                                           'endpoint': ''
                                           })

    def test_decode_message(self):
        """decoding a message packet """
        decoded_message = decode('3:::woot')
        self.assertEqual(decoded_message, {'type': 'message',
                                           'endpoint': '',
                                           'data': 'woot'})

        # decoding a message packet with id and endpoint
        decoded_message = decode('3:5:/tobi')
        self.assertEqual(decoded_message, {'type': 'message',
                                           'id': 5,
                                           'ack': True,
                                           'endpoint': '/tobi',
                                           'data': ''})

    def test_decode_json(self):
        """decoding json packet """
        decoded_message = decode('4:::"2"')
        self.assertEqual(decoded_message, {'type': 'json',
                                           'endpoint': '',
                                           'data': '2'})

        # decoding json packet with message id and ack data
        decoded_message = decode('4:1+::{"a":"b"}')
        self.assertEqual(decoded_message, {'type': 'json',
                                           'id': 1,
                                           'endpoint': '',
                                           'ack': 'data',
                                           'data': {u'a': u'b'}})
    def test_decode_event(self):
        """decoding an event packet """
        decoded_message = decode('5:::{"name":"woot", "args": ["foo"]}')
        self.assertEqual(decoded_message, {'type': 'event',
                                           'name': 'woot',
                                           'endpoint': '',
                                           'args': ["foo"]})

        decoded_message = decode('5:::{"name":"woot"}')
        self.assertEqual(decoded_message, {'type': 'event',
                                           'name': 'woot',
                                           'endpoint': '',
                                           'args': []})

        # decoding an event packet with message id and ack
        decoded_message = decode('5:1+::{"name":"tobi"}')
        self.assertEqual(decoded_message, {'type': 'event',
                                           'id': 1,
                                           'ack': 'data',
                                           'name': 'tobi',
                                           'endpoint': '',
                                           'args': []})

    def test_decode_event_error(self):
        """decoding an event packet """
        decoded_message = decode('5:::')
        self.assertEqual(decoded_message, {'args': [],
                                            'type': 'event',
                                           'endpoint': '',
                                           })

    def test_decode_ack(self):
        """decoding a ack packet """
        decoded_message = decode('6:::140')
        self.assertEqual(decoded_message, {'type': 'ack',
                                           'ackId': 140,
                                           'endpoint': '',
                                           'args': []})
        
        # Decode with endpoint
        decoded_message = decode('6::/chat:140')
        self.assertEqual(decoded_message, {'type': 'ack',
                                           'ackId': 140,
                                           'endpoint': '/chat',
                                           'args': []})

        # With args
        decoded_message = decode('6::/chat:140+["bob", "bob2"]')
        self.assertEqual(decoded_message, {'type': 'ack',
                                           'ackId': 140,
                                           'endpoint': '/chat',
                                           'args': [u"bob", u"bob2"]})

    def test_decode_error(self):
        """decoding error packet """
        decoded_message = decode('7:::')
        self.assertEqual(decoded_message, {'type': 'error',
                                           'reason': '',
                                           'advice': '',
                                           'endpoint': ''})

        decoded_message = decode('7:::0')
        self.assertEqual(decoded_message, {'type': 'error',
                                           'reason': 'transport not supported',
                                           'advice': '',
                                           'endpoint': ''})

        # decoding error packet with reason and advice
        decoded_message = decode('7:::2+0')
        self.assertEqual(decoded_message, {'type': 'error',
                                           'reason': 'unauthorized',
                                           'advice': 'reconnect',
                                           'endpoint': ''})

        # decoding error packet with endpoint
        decoded_message = decode('7::/woot')
        self.assertEqual(decoded_message, {'type': 'error',
                                           'reason': '',
                                           'advice': '',
                                           'endpoint': '/woot'})

    def test_decode_new_line(self):
        """test decoding newline """
        decoded_message = decode('3:::\n')
        self.assertEqual(decoded_message, {'type': 'message',
                                           'data': '\n',
                                           'endpoint': ''})

    def test_decode_noop(self):
        """decoding a noop packet """
        decoded_message = decode('8::')
        self.assertEqual(decoded_message, {'type': 'noop',
                                            'endpoint': ''
                                            })

    def test_except_on_invalid_message_type(self):
        """decoding a noop packet """
        try:
            decoded_message = decode('99::')
        except Exception as e:
            self.assertEqual(e.message, "Unknown message type: 99")
        else:
            self.assertEqual(decoded_message, None,
                    "We should not get a valid message")
if __name__ == '__main__':
    main()
