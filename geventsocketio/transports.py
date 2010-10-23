import gevent

from urlparse import parse_qsl
from gevent.queue import Empty


class BaseTransport(object):
    def __init__(self, handler):
        self.handler = handler

    def encode(self, data):
        return self.handler.environ['socketio']._encode(data)

    def decode(self, data):
        return self.handler.environ['socketio']._decode(data)


class XHRPollingTransport(BaseTransport):
    def handle_get_response(self, session):
        try:
            message = session.write_queue.get(timeout=5.0)
            message = self.encode(message)
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
        messages = self.decode(data)

        for msg in messages:
            session.messages.put_nowait(msg)

        self.handler.start_response("200 OK", [
            ("Access-Control-Allow-Origin", "*"),
            ("Connection", "close"),
            ("Content-Type", "text/plain; charset=UTF-8"),
            ("Content-Length", 2),
        ])
        self.handler.write("ok")

    def connect(self, session, request_method):
        handler = self.handler

        if session.is_new():
            session_id = self.encode(session.session_id)
            handler.start_response("200 OK", [
                ("Access-Control-Allow-Origin", "*"),
                ("Connection", "close"),
                ("Content-Type", "text/plain; charset=UTF-8"),
                ("Content-Length", len(session_id)),
            ])
            handler.write(session_id)

        elif request_method == "GET":
            self.handle_get_response(session)

        elif request_method == "POST":
            self.handle_post_response(session)

        else:
            raise Exception("No support for such method: " + request_method)

        return []


class WebsocketTransport(BaseTransport):
    def connect(self, session, request_method):
        ws = self.handler.environ['wsgi.websocket']
        ws.send(self.encode(session.session_id))

        def write():
            while True:
                print "write", session.session_id

                message = session.write_queue.get()
                if message is None:
                    print "write break", session.session_id
                    break

                ws.send(self.encode(message))

        def read():
            while True:
                print "read", session.session_id

                message = ws.wait()
                if message is None:
                    print "read break", session.session_id
                    session.write_queue.put_nowait(None) # stop write greenlet
                    break

                session.messages.put_nowait(self.decode(message))

        gr1 = gevent.spawn(write)
        gr2 = gevent.spawn(read)

        return [gr1, gr2]



