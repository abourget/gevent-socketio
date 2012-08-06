import gevent
import urllib
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
        self.handler = handler

    def write(self, data=""):
        # Gevent v 0.13
        if hasattr(self.handler, 'response_headers_list'):
            if 'Content-Length' not in self.handler.response_headers_list:
                self.handler.response_headers.append(('Content-Length', len(data)))
                self.handler.response_headers_list.append('Content-Length')
        elif self.handler.provided_content_length is None:
            # Gevent bitbucket
            l = len(data)
            self.handler.provided_content_length = l
            self.handler.response_headers.append(('Content-Length', l))
            
        self.handler.write(data)

    def start_response(self, status, headers, **kwargs):
        if "Content-Type" not in [x[0] for x in headers]:
            headers.append(self.content_type)

        headers.extend(self.headers)
        self.handler.start_response(status, headers, **kwargs)


class XHRPollingTransport(BaseTransport):
    def __init__(self, *args, **kwargs):
        super(XHRPollingTransport, self).__init__(*args, **kwargs)

    def options(self):
        self.start_response("200 OK", ())
        self.write()
        return []

    def get(self, socket):
        socket.heartbeat()

        payload = self.get_messages_payload(socket, timeout=5.0)
        if not payload:
            payload = "8::"  # NOOP

        self.start_response("200 OK", [])
        self.write(payload)

        return []

    def _request_body(self):
        return self.handler.wsgi_input.readline()

    def post(self, socket):
        for message in self.decode_payload(self._request_body()):
            socket.put_server_msg(message)

        self.start_response("200 OK", [
            ("Connection", "close"),
            ("Content-Type", "text/plain")
        ])
        self.write("1")

        return []

    def get_messages_payload(self, socket, timeout=None):
        """This will fetch the messages from the Socket's queue, and if
        there are many messes, pack multiple messages in one payload and return
        """
        try:
            msgs = socket.get_multiple_client_msgs(timeout=timeout)
            data = self.encode_payload(msgs)
        except Empty:
            data = ""
        return data

    def encode_payload(self, messages):
        """Encode list of messages. Expects messages to be unicode.

        ``messages`` - List of raw messages to encode, if necessary

        """
        if not messages or messages[0] is None:
            return ''

        if len(messages) == 1:
            return messages[0].encode('utf-8')

        payload = u''.join(u'\ufffd%d\ufffd%s' % (len(p), p)
                          for p in messages)

        return payload.encode('utf-8')

    def decode_payload(self, payload):
        """This function can extract multiple messages from one HTTP payload.
        Some times, the XHR/JSONP/.. transports can pack more than one message
        on a single packet.  They are encoding following the WebSocket
        semantics, which need to be reproduced here to unwrap the messages.

        The semantics are:

          \ufffd + [length as a string] + \ufffd + [payload as a unicode string]

        This function returns a list of messages, even though there is only
        one.

        Inspired by socket.io/lib/transports/http.js
        """
        payload = payload.decode('utf-8')
        if payload[0] == u"\ufffd":
            ret = []
            while len(payload) != 0:
                len_end = payload.find(u"\ufffd", 1)
                length = int(payload[1:len_end])
                msg_start = len_end + 1
                msg_end = length + msg_start
                message = payload[msg_start:msg_end]
                ret.append(message)
                payload = payload[msg_end:]
            return ret
        return [payload]

    def connect(self, socket, request_method):
        if not socket.connection_confirmed:
            socket.connection_confirmed = True
            self.start_response("200 OK", [
                ("Connection", "close"),
            ])
            self.write("1::")  # 'connect' packet

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
        data = urllib.unquote_plus(data)[3:-1] \
                     .replace(r'\"', '"') \
                     .replace(r"\\", "\\")

        # For some reason, in case of multiple messages passed in one
        # query, IE7 sends it escaped, not utf-8 encoded. This dirty
        # hack handled it
        if data[0] == "\\":
            data = data.decode("unicode_escape").encode("utf-8")
        return data

    def write(self, data):
        """Just quote out stuff before sending it out"""
        args = urlparse.parse_qs(self.handler.environ.get("QUERY_STRING"))
        if "i" in args:
            i = args["i"]
        else:
            i = "0"
        # TODO: don't we need to quote this data in here ?
        super(JSONPolling, self).write("io.j[%s]('%s');" % (i, data))


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
                payload = self.get_messages_payload(socket)

                if not payload:
                    # That would mean the call to Queue.get() returned Empty,
                    # so it was in fact killed, since we pass no timeout=..
                    socket.kill()
                    break
                else:
                    try:
                        self.write_multipart(header)
                        self.write_multipart(payload)
                        self.write_multipart("--socketio\r\n")
                    except socket.error:
                        socket.kill()
                        break

        return [gevent.spawn(chunk)]


class WebsocketTransport(BaseTransport):
    def connect(self, socket, request_method):
        websocket = self.handler.environ['wsgi.websocket']
        websocket.send("1::")  # 'connect' packet

        def send_into_ws():
            while True:
                message = socket.get_client_msg()

                if message is None:
                    break

                websocket.send(message)

        def read_from_ws():
            while True:
                message = websocket.receive()

                if message is None:
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
        self.write("<script>_('%s');</script>" % data)
        
    def write(self, data):
        l = 1024 * 5
        super(HTMLFileTransport, self).write("%d\r\n%s%s\r\n" % (l, data, " " * (l - len(data))))
        
    def connect(self, socket, request_method):
        socket.connection_confirmed = True
        return super(HTMLFileTransport, self).connect(socket, request_method)

    def get(self, socket):
        self.start_response("200 OK", [
            ("Connection", "keep-alive"),
            ("Content-Type", "text/html"),
            ("Transfer-Encoding", "chunked"),
        ])
        self.write("<html><body><script>var _ = function (msg) { parent.s._(msg, document); };</script>")
        self.write_packed("1::")  # 'connect' packet
        

        def chunk():
            while True:
                payload = self.get_messages_payload(socket)

                if not payload:
                    # That would mean the call to Queue.get() returned Empty,
                    # so it was in fact killed, since we pass no timeout=..
                    socket.kill()
                    break
                else:
                    try:
                        self.write_packed(payload)
                    except socket.error:
                        socket.kill()
                        break
        return [gevent.spawn(chunk)]
