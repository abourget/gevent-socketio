import gevent
import socket
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
            ("Connection", "close"),
        ]
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

    def start_response(self, *args, **kwargs):
        self.headers.append(self.content_type)
        self.handler.start_response(*args, **kwargs)


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

    def post(self, session):
        data = self.handler.wsgi_input.readline().replace("data=", "")
        print data # 5:1+::{"name":"nickname","args":["test"]}
        session.put_server_msg(self.decode(data))

        self.start_response("200 OK", [])
        self.write("1")

        return []

    def connect(self, session, request_method):
        if not session.connection_confirmed:
            session.connection_confirmed = True
            self.start_response("200 OK", [])
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

    def write_packed(self, data):
        self.write("io.JSONP[0]._('%s');" % data)


class XHRMultipartTransport(XHRPollingTransport):
    def connect(self, session, request_method):
        if request_method == "GET":
            heartbeat = self.handler.environ['socketio'].start_heartbeat()
            response = self.handle_get_response(session)

            return [heartbeat] + response

        elif request_method == "POST":
            return self.handle_post_response(session)

        elif request_method == "OPTIONS":
            return self.handle_options_response()

        else:
            raise Exception("No support for such method: " + request_method)


    def get(self, session):
        header = "Content-Type: text/plain; charset=UTF-8\r\n\r\n"

        self.start_response("200 OK", [
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Credentials", "true"),
            ("Connection", "keep-alive"),
            ("Content-Type", "multipart/x-mixed-replace;boundary=\"socketio\""),
        ])
        self.write_multipart("--socketio\r\n")
        self.write_multipart(header)
        self.write_multipart(self.encode(session.session_id) + "\r\n")
        self.write_multipart("--socketio\r\n")

        def send_part():
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

        return [gevent.spawn(send_part)]


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
