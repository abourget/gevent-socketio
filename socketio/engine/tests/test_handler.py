from unittest import TestCase
import gevent
from gevent.monkey import patch_all
import sys
from socketio.engine.parser import Parser
from socketio.server import serve
import requests
import logging

logging.basicConfig(stream=sys.stderr)

def application(environ, start_response):
    body = 'ok'
    headers = [('Content-Type', 'text/html; charset=utf8'),
               ('Content-Length', str(len(body)))]
    start_response('200 OK', headers)
    return [body]


class EngineHandlerTestCase(TestCase):
    def setUp(self):
        patch_all()
        # start the server
        self.job = gevent.spawn(serve, application, host='localhost', port='3030')

    def tearDown(self):
        gevent.kill(self.job)

    def test_handshake(self):
        response = requests.get('http://localhost:3030/socket.io/?transport=polling')
        self.assertEqual(response.status_code, 200)
        for p, i, t in Parser.decode_payload(bytearray(response.content)):
            self.assertIsNotNone(p)
            self.assertEqual(p['type'], 'open')


