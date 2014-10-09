from unittest import TestCase
import gevent
from socketio.engine.response import Response


class ResponseTest(TestCase):
    def test_join(self):
        response = Response()

        def finish_response(res):
            res.end(status_code=200, body='hello')

        gevent.spawn_later(0.5, finish_response, response)
        response.join()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, 'hello')

        self.assertRaises(Response.ResponseAlreadyEnded, response.end)


