import json
from unittest import TestCase
import gevent
from gevent.monkey import patch_all
import requests
from socketio.server import serve
from socketio.engine.parser import Parser as EngineParser


def application(environ, start_response):
    body = 'ok'
    headers = [('Content-Type', 'text/html; charset=utf8'),
               ('Content-Length', str(len(body)))]
    start_response('200 OK', headers)
    return [body]


class ServerTest(TestCase):
    def __init__(self, *args, **kwarg):
        patch_all()

        self.host = '127.0.0.1'
        self.port = 3030
        self.root_url = 'http://%(host)s:%(port)d/socket.io/' % {
            'host': self.host,
            'port': self.port
        }
        super(ServerTest, self).__init__(*args, **kwarg)

    def setUp(self):
        self.job = gevent.spawn(serve, application, host=self.host, port=self.port)

    def tearDown(self):
        gevent.kill(self.job)

    def test_server(self):
        response = requests.get(self.root_url + '?transport=polling')
        sid = None
        for p, i, t in EngineParser.decode_payload(bytearray(response.content)):
            data = json.loads(p['data'])
            sid = data['sid']
            break

        self.assertIsNotNone(sid)
