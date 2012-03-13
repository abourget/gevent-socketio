import gevent
import urlparse

from gevent.queue import Empty
from socketio import packet

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

    def write(self, data=""):
        if 'Content-Length' not in self.handler.response_headers_list:
            self.handler.response_headers.append(('Content-Length', len(data)))
            self.handler.response_headers_list.append('Content-Length')

        self.handler.write(data)

    def start_response(self, status, headers, **kwargs):
        if "Content-Type" not in [x[0] for x in headers]:
            headers.append(self.content_type)

        headers.extend(self.headers)
        #print headers
        self.handler.start_response(status, headers, **kwargs)


class XHRPollingTransport(BaseTransport):
    def __init__(self, *args, **kwargs):
        super(XHRPollingTransport, self).__init__(*args, **kwargs)

    def options(self):
        self.start_response("200 OK", ())
        self.write()
        return []

    def get(self, socket):
        socket.clear_disconnect_timeout();

        try:
            message = socket.get_client_msg(timeout=5.0)
        except Empty:
            message = "8::" # NOOP

        self.start_response("200 OK", [])
        self.write(message)

        return []

    def _request_body(self):
        return self.handler.wsgi_input.readline()

    def post(self, socket):
        socket.put_server_msg(self._request_body())

        self.start_response("200 OK", [
            ("Connection", "close"),
            ("Content-Type", "text/plain")
        ])
        self.write("1")

        return []

    def connect(self, socket, request_method):
        if not socket.connection_confirmed:
            socket.connection_confirmed = True
            self.start_response("200 OK", [
                ("Connection", "close"),
            ])
            self.write("1::") # 'connect' packet

            return []
        elif request_method in ("GET", "POST", "OPTIONS"):
            return getattr(self, request_method.lower())(socket)
        else:
            raise Exception("No support for the method: " + request_method)


class JSONPolling(XHRPollingTransport):
    def __init__(self, handler):
        super(JSONPolling, self).__init__(handler)
        self.content_type = ("Content-Type", "text/javascript; charset=UTF-8")

    def _request_body(self):
        data = super(JSONPolling, self)._request_body()
        # resolve %20%3F's, take out wrapping d="...", etc..
        return urlparse.unquote(data)[3:-1].replace(r'\"', '"')

    def write(self, data):
        super(JSONPolling, self).write("io.j[0]('%s');" % data)


class XHRMultipartTransport(XHRPollingTransport):
    def __init__(self, handler):
        super(JSONPolling, self).__init__(handler)
        self.content_type = (
            "Content-Type",
            "multipart/x-mixed-replace;boundary=\"socketio\""
        )

    def connect(self, socket, request_method):
        if request_method == "GET":
            # TODO: double verify this, because we're not sure. look at git revs.
            heartbeat = socket._spawn_heartbeat()
            return [heartbeat] + self.get(socket)
        elif request_method == "POST":
            return self.post(socket)
        else:
            raise Exception("No support for such method: " + request_method)

    def get(self, socket):
        header = "Content-Type: text/plain; charset=UTF-8\r\n\r\n"

        self.start_response("200 OK", [("Connection", "keep-alive")])
        self.write_multipart("--socketio\r\n")
        self.write_multipart(header)
        self.write_multipart(str(socket.sessid) + "\r\n")
        self.write_multipart("--socketio\r\n")

        def chunk():
            while True:
                message = socket.get_client_msg()

                if message is None:
                    socket.kill()
                    break
                else:
                    try:
                        self.write_multipart(header)
                        self.write_multipart(message)
                        self.write_multipart("--socketio\r\n")
                    except socket.error:
                        socket.kill()
                        break

        return [gevent.spawn(chunk)]


class WebsocketTransport(BaseTransport):
    def connect(self, socket, request_method):
        websocket = self.handler.environ['wsgi.websocket']
        websocket.send("1::") # 'connect' packet

        def send_into_ws():
            while True:
                message = socket.get_client_msg()

                if message is None:
                    socket.kill()
                    break

                websocket.send(message)

        def read_from_ws():
            while True:
                message = websocket.receive()

                if not message:
                    socket.kill()
                    break
                else:
                    if message is not None:
                        socket.put_server_msg(message)

        gr1 = gevent.spawn(send_into_ws)
        gr2 = gevent.spawn(read_from_ws)
        heartbeat1, heartbeat2 = socket._spawn_heartbeat()

        return [gr1, gr2, heartbeat1, heartbeat2]


class FlashSocketTransport(WebsocketTransport):
    pass


class HTMLFileTransport(XHRPollingTransport):
    """Not tested at all!"""

    def __init__(self, handler):
        super(HTMLFileTransport, self).__init__(handler)
        self.content_type = ("Content-Type", "text/html")

    def write_packed(self, data):
        self.write("<script>parent.s._('%s', document);</script>" % data)

    def handle_get_response(self, socket):
        self.start_response("200 OK", [
            ("Connection", "keep-alive"),
            ("Content-Type", "text/html"),
            ("Transfer-Encoding", "chunked"),
        ])
        self.write("<html><body>" + " " * 244)

        try:
            message = socket.get_client_msg(timeout=5.0)
        except Empty:
            message = ""

        self.write_packed(message)
