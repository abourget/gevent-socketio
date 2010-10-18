from urlparse import parse_qsl
from gevent.queue import Empty

class XHRPollingTransport(object):
    def __init__(self, handler):
        self.handler = handler

    def handle_get_response(self, session):
        try:
            message = session.messages.get(timeout=5.0)
            message = self.handler._encode(message)
        except Empty:
            message = ""

        self.handler.start_response("200 OK", [
            ("Access-Control-Allow-Origin", "*"),
            ("Connection", "close"),
            ("Content-Type", "text/plain; charset=UTF-8"),
            ("Content-Length", len(message)),
        ])
        self.handler.write(message)

    def handle_post_response(self, session):
        data = self.handler.wsgi_input.readline().replace("data=", "")
        messages = self.handler._decode(data)

        for msg in messages:
            session.messages.put_nowait(msg)

        self.handler.start_response("200 OK", [
            ("Access-Control-Allow-Origin", "*"),
            ("Connection", "close"),
            ("Content-Type", "text/plain; charset=UTF-8"),
            ("Content-Length", 2),
        ])
        self.handler.write("ok")
