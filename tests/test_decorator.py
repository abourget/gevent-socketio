from collections import namedtuple
from unittest import TestCase
from socketio.server import SocketIOServer
from socketio.decorators import namespace
from socketio.socket import Socket


def application(environ, start_response):
    body = 'ok'
    headers = [('Content-Type', 'text/html; charset=utf8'),
               ('Content-Length', str(len(body)))]
    start_response('200 OK', headers)
    return [body]


def packet(*args):
    pass

Client = namedtuple('Client', ['id', 'engine_socket', 'request', 'packet'])
Request = namedtuple('Request', ['GET', 'scheme', 'headers', 'url'])
EngineSocket = namedtuple('EngineSocket', ['ready_state'])


class DjangoTestCase(TestCase):

    def test_namespace_decorator(self):
        s = SocketIOServer(listener=8000, application=application)
        ns = s.of('/chat')

        m = {}

        @namespace('/chat')
        class TestNameSpace(object):
            @classmethod
            def on_test(cls, socket, message):
                m['message'] = message

        socket = ns.add(Client(id=1, engine_socket=EngineSocket(ready_state='OPEN'), packet=packet, request=Request(
            GET='test', scheme='http', headers={}, url='http://test'
        )))

        socket.on_event({
            'type': 2,
            'data': ['test', 'hello']
        })

        self.assertEqual(m['message'], 'hello')
