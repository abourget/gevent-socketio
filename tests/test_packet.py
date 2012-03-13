"""
Tests based on the Socket.IO spec: https://github.com/LearnBoost/socket.io-spec
"""

from unittest import TestCase, main

from socketio.packet import Packet


class TestEncodeMessage(TestCase):

    def setUp(self):
        self.packet = Packet('error')

    def test_encode_disconnect(self):
        """encoding a disconnection packet """
        encoded_message = self.packet.encode({'type': 'disconnect',
                                                'endpoint': '/woot'
                                                })
        self.assertEquals(encoded_message, '0::/woot')

    def test_encode_connect(self):
        """encoding a connection packet """
        encoded_message = self.packet.encode({'type': 'connect',
                                              'endpoint': '/tobi',
                                              'qs': '',
                                              })
        self.assertEquals(encoded_message, '1::/tobi')

        # encoding a connection packet with query string
        encoded_message = self.packet.encode({'type': 'connect',
                                              'endpoint': '/test',
                                              'qs': '?/test=1'
                                              })
        self.assertEquals(encoded_message, '1::/test:?test=1')

    def test_encode_heartbeat(self):
        """encoding a connection packet """
        encoded_message = self.packet.encode({'type': 'heartbeat',
                                              'endpoint': ''
                                              })
        self.assertEquals(encoded_message, '2::')

    def test_encode_message(self):
        """encoding a message packet """        
        encoded_message = self.packet.encode({'type': 'message',
                                              'endpoint': '',
                                              'data': 'woot'
                                              })
        self.assertEquals(encoded_message, '3::woot')

        # encoding a message packet with id and endpoint
        encoded_message = self.packet.encode({'type': 'message',
                                              'endpoint': '/tobi',
                                              'id': 5,
                                              'ack': True,
                                              'data': ''
                                              })
        self.assertEquals(encoded_message, '3:5:/tobi')

    def test_encode_json(self):
        """encoding JSON packet """
        encoded_message = self.packet.encode({'type': 'json',
                                              'endpoint': '',
                                              'data': 2
                                              })
        self.assertEquals(encoded_message, '4:::"2"')
        
        # encoding json packet with message id and ack data
        encoded_message = self.packet.encode({'type': 'json',
                                              'id': 1,
                                              'ack': 'data',
                                              'endpoint': '',
                                              'data': {'a' : 'b'}
                                              })
        self.assertEquals(encoded_message, '4:1+::{"a":"b"}')

    def test_encode_event(self):
        """encoding an event packet """
        encoded_message = self.packet.encode({'type': 'event',
                                              'endpoint': '',
                                              'data': 'woot',
                                              'args': []
                                              })
        self.assertEquals(encoded_message, '5:::{"name":"woot"}')

        # encoding an event packet with message id and ack
        encoded_message = self.packet.encode({'type': 'event',
                                              'name': 'tobi',
                                              'id': 1,
                                              'ack': True,
                                              'data': ''
                                              })
        self.assertEquals(encoded_message, '5:1+::{"name":"tobi"}')

        # encoding an event packet with data
        encoded_message = self.packet.encode({'type': 'event',
                                              'name': 'edwald',
                                              'ack': True,
                                              'endpoint': '',
                                              'args': [{'a':'b'}, 2, '3']
                                              })
        self.assertEquals(encoded_message,
                          '5:::{"name":"edwald","args":[{"a":"b"},2,"3"]}')

    def test_encode_ack(self):
        """encoding ack packet """
        encoded_message = self.packet.encode({'type': 'ack',
                                              'ackId': 140,
                                              'endpoint': '',
                                              'args': []
                                              })
        self.assertEquals(encoded_message, '6:::140')

        # encoding ack packet with args
        encoded_message = self.packet.encode({'type': 'ack',
                                              'ackId': 12,
                                              'endpoint': '',
                                              'args': ['woot', 'wa']
                                              })
        self.assertEquals(encoded_message, '6:::12+["woot","wa"]')

    def test_encode_error(self):
        """encoding error packet """
        encoded_message = self.packet.encode({'type': 'error',
                                              'reason': '',
                                              'advice': '',
                                              'endpoint': ''
                                              })
        self.assertEquals(encoded_message, '7:::')

        # encoding error packet with reason
        encoded_message = self.packet.encode({'type': 'error',
                                              'reason': 'transport not supported',
                                              'advice': '',
                                              'endpoint': ''
                                              })
        self.assertEquals(encoded_message, '7:::0')

        # encoding error packet with reason and advice
        encoded_message = self.packet.encode({'type': 'error',
                                              'reason': 'unauthorized',
                                              'advice': 'reconnect',
                                              'endpoint': ''
                                              })
        self.assertEquals(encoded_message, '7:::2+0')

        # encoding error packet with endpoint
        encoded_message = self.packet.encode({'type': 'error',
                                              'reason': '',
                                              'advice': '',
                                              'endpoint': '/woot'
                                              })
        self.assertEquals(encoded_message, '7:::/woot')


class TestDecodeMessage(TestCase):
    
    def setUp(self):
        self.packet = Packet('error')

    def test_decode_deconnect(self):
        """decoding a disconnection packet """
        decoded_message = self.packet.decode('0::/woot')
        self.assertEquals(decoded_message, {'type': 'disconnect',
                                            'endpoint': '/woot'
                                            })
        
    def test_decode_connect(self):
        """decoding a connection packet """
        decoded_message = self.packet.decode('1::/tobi')
        self.assertEquals(decoded_message, {'type': 'connect',
                                            'endpoint': '/tobi',
                                            'qs': ''
                                            })

        # decoding a connection packet with query string
        decoded_message = self.packet.decode('1::/test:?test=1')
        self.assertEquals(decoded_message, {'type': 'connect',
                                            'endpoint': '/test',
                                            'qs': '?test=1'
                                            })

    def test_decode_heartbeat(self):
        """decoding a heartbeat packet """
        decoded_message = self.packet.decode('2:::')
        self.assertEquals(decoded_message, {'type': 'heartbeat',
                                            'endpoint': ''
                                            })

    def test_decode_message(self):
        """decoding a message packet """
        decoded_message = self.packet.decode('3:::woot')
        self.assertEquals(decoded_message, {'type': 'message',
                                            'endpoint': '',
                                            'data': 'woot'})

        # decoding a message packet with id and endpoint
        decoded_message = self.packet.decode('3:5:/tobi')
        self.assertEquals(decoded_message, {'type': 'message',
                                            'id': 5,
                                            'ack': True,
                                            'endpoint': '/tobi',
                                            'data': ''})

    def test_decode_json(self):
        """decoding json packet """
        decoded_message = self.packet.decode('4:::"2"')
        self.assertEquals(decoded_message, {'type': 'json',
                                            'endpoint': '',
                                            'data': 2})

        # decoding json packet with message id and ack data
        decoded_message = self.packet.decode('4:1+::{"a":"b"}')
        self.assertEquals(decoded_message, {'type': 'json',
                                            'id': 1,
                                            'endpoint': '',
                                            'data': {'a': 'b'}})

    def test_decode_event(self):
        """decoding an event packet """
        decoded_message = self.packet.decode('5:::{"name":"woot"}')
        self.assertEquals(decoded_message, {'type': 'event',
                                            'name': 'woot',
                                            'endpoint': '',
                                            'args': []})

        # decoding an event packet with message id and ack
        decoded_message = self.packet.decode('5:1+::{"name":"tobi"}')
        self.assertEquals(decoded_message, {'type': 'event',
                                            'id': 1,
                                            'ack': 'data',
                                            'name': 'tobi',
                                            'endpoint': '',
                                            'args': []})

    def test_decode_ack(self):
        """decoding a ack packet """
        decoded_message = self.packet.decode('6:::140')
        self.assertEquals(decoded_message, {'type': 'ack',
                                            'ackId': 140,
                                            'endpoint': '',
                                            'args': []})

    def test_decode_error(self):
        """decoding error packet """
        decoded_message = self.packet.decode('7:::')
        self.assertEquals(decoded_message, {'type': 'error',
                                            'reason': '',
                                            'advice': '',
                                            'endpoint': ''})

        decoded_message = self.packet.decode('7:::0')
        self.assertEquals(decoded_message, {'type': 'error',
                                            'reason': 'transport not supported',
                                            'advice': '',
                                            'endpoint': ''})

        # decoding error packet with reason and advice
        decoded_message = self.packet.decode('7:::2+0')
        self.assertEquals(decoded_message, {'type': 'error',
                                            'reason': 'unauthorized',
                                            'advice': 'reconnect',
                                            'endpoint': ''})

        # decoding error packet with endpoint
        decoded_message = self.packet.decode('7::/woot')
        self.assertEquals(decoded_message, {'type': 'error',
                                            'reason': '',
                                            'advice': '',
                                            'endpoint': '/woot'})

    def test_decode_new_line(self):
        """test decoding newline """
        decoded_message = self.packet.decode('3:::\n')
        self.assertEquals(decoded_message, {'type': 'message',
                                            'data': '\n',
                                            'endpoint': ''})

if __name__ == '__main__':
    main()
