import json
from unittest import TestCase
import gevent
from gevent.monkey import patch_all
import sys
from socketio.engine.handler import EngineHandler
from socketio.engine.parser import Parser
from socketio.engine.socket import Socket
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
    def __init__(self, *args, **kwargs):
        patch_all()
        super(EngineHandlerTestCase, self).__init__(*args, **kwargs)

        self.port = 3030
        self.host = 'localhost'
        self.root_url = 'http://%(host)s:%(port)d/socket.io/' % {
            'host': self.host,
            'port': self.port
        }
        self.job = None

    def setUp(self):
        self.job = gevent.spawn(serve, application, host=self.host, port=self.port)

    def tearDown(self):
        gevent.kill(self.job)

    def test_handshake(self):
        response = requests.get(self.root_url + '?transport=polling')
        self.assertEqual(response.status_code, 200)
        for p, i, t in Parser.decode_payload(bytearray(response.content)):
            self.assertIsNotNone(p)
            self.assertEqual(p['type'], 'open')
            data = json.loads(p['data'])
            self.assertIsNotNone(data['sid'])

    def test_heartbeat(self):
        response = requests.get(self.root_url + '?transport=polling')
        sid = None
        for p, i, t in Parser.decode_payload(bytearray(response.content)):
            data = json.loads(p['data'])
            sid = data['sid']
            break

        self.assertIsNotNone(sid)

        def get_request(url):
            return requests.get(url)

        get_job = gevent.spawn(get_request, self.root_url + ('?transport=polling&sid=%s' % sid))

        encoded = Parser.encode_payload([{
            "type": "ping"
        }])

        # Work around the bug which not sending pre buffered message
        response = requests.post(self.root_url + ('?transport=polling&sid=%s' % sid),
                                 data=encoded,
                                 headers={'Content-Type': 'application/octet-stream'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'ok')

        get_job.join()
        response = get_job.value
        for p, i, t in Parser.decode_payload(bytearray(response.content)):
            self.assertEqual(p['type'], 'pong')
            break

    def test_data_transfer(self):
        response = requests.get(self.root_url + '?transport=polling')
        sid = None
        for p, i, t in Parser.decode_payload(bytearray(response.content)):
            data = json.loads(p['data'])
            sid = data['sid']
            break

        def get_request(url):
            return requests.get(url)

        get_job = gevent.spawn(get_request, self.root_url + ('?transport=polling&sid=%s' % sid))
        socket = EngineHandler.clients[sid]
        self.assertIsNotNone(socket)

        socket.send_packet('message', 'hello')
        get_job.join()

        response = get_job.value
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len([Parser.decode_payload(bytearray(response.content))]), 1)
        for p, i, t in Parser.decode_payload(bytearray(response.content)):
            self.assertEqual(p['type'], 'message')
            data = p['data']
            self.assertEqual(data, 'hello')
