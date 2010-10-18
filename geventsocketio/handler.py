import re
from gevent.pywsgi import WSGIHandler
from geventsocketio import transports

class SocketIOHandler(WSGIHandler):
    path_re = re.compile(r"^/(?P<resource>[^/]+)/(?P<transport>[^/]+)/(?P<session_id>[^/]*)/?(?P<rest>.*)$")

    handler_types = {
        'websocket': 'WebSocketHandler',
        'wsgi': WSGIHandler,
        'flashsocket': 'FlashSocketHandler',
        'htmlfile': 'HTMLFileHandler',
        'xhr-multipart': 'XHRMultipartHandler',
        'xhr-polling': transports.XHRPollingTransport,
        'jsonp-polling': 'JSONPollingHandler',
    }

    def __init__(self, *args, **kwargs):
        self.socketio_connection = False
        super(SocketIOHandler, self).__init__(*args, **kwargs)

    def handle_one_response(self):
        self.status = None
        self.headers_sent = False
        self.result = None
        self.response_length = 0
        self.response_use_chunked = False

        path = self.environ.get('PATH_INFO')
        parts = SocketIOHandler.path_re.match(path)

        print "Arrived at", path

        if parts:
            parts = parts.groupdict()
            print parts
        else:
            print "closed"
            self.close_connection = True
            return

        resource = parts.get('resource')
        transport = SocketIOHandler.handler_types.get(parts.get('transport'))
        session_id = parts.get('session_id')
        request_method = self.environ.get("REQUEST_METHOD")

        if not transport:
            return super(SocketIOHandler, self).handle_one_response()
        self.transport = transport(self)

        print request_method
        session = self.server.get_session(session_id)

        if session.is_new():
            session_id = self._encode(session.session_id)
            self.start_response("200 OK", [
                ("Access-Control-Allow-Origin", "*"),
                ("Connection", "close"),
                ("Content-Type", "text/plain; charset=UTF-8"),
                ("Content-Length", len(session_id)),
            ])
            self.write(session_id)

        elif request_method == "GET":
            self.transport.handle_get_response(session)

        elif request_method == "POST":
            self.transport.handle_post_response(session)

        else:
            raise Exception("No support for such method: " + request_method)

    def _encode(self, data):
        return self.environ['socketio']._encode(data)

    def _decode(self, data):
        return self.environ['socketio']._decode(data)
