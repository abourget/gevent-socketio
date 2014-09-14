from unittest import TestCase
import gevent
from socketio.server import serve


def application(environ, start_response):
    body = 'ok'
    headers = [('Content-Type', 'text/html; charset=utf8'),
               ('Content-Length', str(len(body)))]
    start_response('200 OK', headers)
    return [body]


class ServerTest(TestCase):
    def __init__(self, *args, **kwarg):
        self.host = '127.0.0.1'
        self.port = '3030'
        super(ServerTest, self).__init__(*args, **kwarg)

    def setUp(self):
        self.job = gevent.spawn(serve, application, host=self.host, port=self.port)

    def tearDown(self):
        gevent.kill(self.job)

    def test_server(self):
        # Seems we need a socketio client to test the server side of socketio
        pass
