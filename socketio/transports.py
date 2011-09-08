import gevent
import socket
import urlparse

from gevent.queue import Empty

class BaseTransport(object):
    """Base class for all transports. Mostly wraps handler class functions."""

    def __init__(self, handler):
        self.content_type = ("Content-Type", "text/plain; charset=UTF-8")
        self.headers = [
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Credentials", "true"),
            ("Access-Control-Allow-Methods", "POST, GET, OPTIONS"),
            ("Access-Control-Max-Age", 3600),
        ]
        self.headers_list = []
        self.handler = handler

    def encode(self, data):
        return self.handler.environ['socketio'].encode(data)

    def decode(self, data):
        return self.handler.environ['socketio'].decode(data)

    def write(self, data=""):
        if 'Content-Length' not in self.handler.response_headers_list:
            self.handler.response_headers.append(('Content-Length', len(data)))
            self.handler.response_headers_list.append('Content-Length')

        self.handler.write(data)

    def start_response(self, status, headers, **kwargs):
        if "Content-Type" not in [x[0] for x in headers]:
            headers.append(self.content_type)

        headers.extend(self.headers)
        print headers
        self.handler.start_response(status, headers, **kwargs)


class XHRPollingTransport(BaseTransport):
    def __init__(self, *args, **kwargs):
        super(XHRPollingTransport, self).__init__(*args, **kwargs)

    def options(self):
        self.start_response("200 OK", ())
        self.write()
        return []

    def get(self, session):
        session.clear_disconnect_timeout();

        try:
            message = session.get_client_msg(timeout=5.0)
            message = self.encode(message)
        except Empty:
            message = "8::" # NOOP

        self.start_response("200 OK", [])
        self.write(message)

        return []

    def _request_body(self):
        return self.handler.wsgi_input.readline()

    def post(self, session):
        session.put_server_msg(self.decode(self._request_body()))

        self.start_response("200 OK", [
            ("Connection", "close"),
            ("Content-Type", "text/plain")
        ])
        self.write("1")

        return []

    def connect(self, session, request_method):
        if not session.connection_confirmed:
            session.connection_confirmed = True
            self.start_response("200 OK", [
                ("Connection", "close"),
            ])
            self.write("1::")

            return []
        elif request_method in ("GET", "POST", "OPTIONS"):
            return getattr(self, request_method.lower())(session)
        else:
            raise Exception("No support for the method: " + request_method)


class JSONPolling(XHRPollingTransport):
    def __init__(self, handler):
        super(JSONPolling, self).__init__(handler)
        self.content_type = ("Content-Type", "text/javascript; charset=UTF-8")

    def _request_body(self):
        data = super(JSONPolling, self)._request_body()
        return urlparse.unquote(data).replace("d=", "")

    def write(self, data):
        super(JSONPolling, self).write("io.j[0]('%s');" % data)


class XHRMultipartTransport(XHRPollingTransport):
    def __init__(self, handler):
        super(JSONPolling, self).__init__(handler)
        self.content_type = (
            "Content-Type",
            "multipart/x-mixed-replace;boundary=\"socketio\""
        )

    def connect(self, session, request_method):
        if request_method == "GET":
            heartbeat = self.handler.environ['socketio'].start_heartbeat()
            return [heartbeat] + self.get(session)
        elif request_method == "POST":
            return self.post(session)
        else:
            raise Exception("No support for such method: " + request_method)

    def get(self, session):
        header = "Content-Type: text/plain; charset=UTF-8\r\n\r\n"

        self.start_response("200 OK", [("Connection", "keep-alive")])
        self.write_multipart("--socketio\r\n")
        self.write_multipart(header)
        self.write_multipart(self.encode(session.session_id) + "\r\n")
        self.write_multipart("--socketio\r\n")

        def chunk():
            while True:
                message = session.get_client_msg()

                if message is None:
                    session.kill()
                    break
                else:
                    message = self.encode(message)

                    try:
                        self.write_multipart(header)
                        self.write_multipart(message)
                        self.write_multipart("--socketio\r\n")
                    except socket.error:
                        session.kill()
                        break

        return [gevent.spawn(chunk)]


class WebsocketTransport(BaseTransport):
    def connect(self, session, request_method):
        websocket = self.handler.environ['wsgi.websocket']
        websocket.send("1::")

        def send_into_ws():
            while True:
                message = session.get_client_msg()

                if message is None:
                    session.kill()
                    break

                websocket.send(self.encode(message))

        def read_from_ws():
            while True:
                message = websocket.wait()

                if message is None:
                    session.kill()
                    break
                else:
                    decoded_message = self.decode(message)
                    if decoded_message is not None:
                        session.put_server_msg(decoded_message)

        gr1 = gevent.spawn(send_into_ws)
        gr2 = gevent.spawn(read_from_ws)

        heartbeat = self.handler.environ['socketio'].start_heartbeat()

        return [gr1, gr2, heartbeat]


class FlashSocketTransport(WebsocketTransport):
    pass


class HTMLFileTransport(XHRPollingTransport):
    """Not tested at all!"""

    def __init__(self, handler):
        super(HTMLFileTransport, self).__init__(handler)
        self.content_type = ("Content-Type", "text/html")

    def write_packed(self, data):
        self.write("<script>parent.s._('%s', document);</script>" % data)

    def handle_get_response(self, session):
        self.start_response("200 OK", [
            ("Connection", "keep-alive"),
            ("Content-Type", "text/html"),
            ("Transfer-Encoding", "chunked"),
        ])
        self.write("<html><body>" + " " * 244)

        try:
            message = session.get_client_msg(timeout=5.0)
            message = self.encode(message)
        except Empty:
            message = ""

        self.write_packed(message)
