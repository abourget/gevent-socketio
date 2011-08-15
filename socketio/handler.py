import re
import gevent

from gevent.pywsgi import WSGIHandler
from socketio import transports
from geventwebsocket.handler import WebSocketHandler

class SocketIOHandler(WSGIHandler):
    RE_REQUEST_URL = re.compile(r"""
        ^/(?P<namespace>[^/]+)
         /(?P<protocol_version>[^/]+)
         /(?P<transport_id>[^/]+)
         /(?P<session_id>[^/]+)
         /?(?P<rest>.*)$
         """, re.X)
    RE_HANDSHAKE_URL = re.compile(r"^/(?P<namespace>[^/]+)/1/?(?P<rest>.*)$", re.X)

    handler_types = {
        'websocket': transports.WebsocketTransport,
        'flashsocket': transports.FlashSocketTransport,
        'htmlfile': transports.HTMLFileTransport,
        'xhr-multipart': transports.XHRMultipartTransport,
        'xhr-polling': transports.XHRPollingTransport,
        'jsonp-polling': transports.JSONPolling,
    }

    def __init__(self, *args, **kwargs):
        self.socketio_connection = False
        self.allowed_paths = None

        super(SocketIOHandler, self).__init__(*args, **kwargs)

    def _do_handshake(self, tokens):
        if tokens["namespace"] != self.server.namespace:
            raise Exception("TODO")
        else:
            super(WSGIHandler, self).start_response("200 OK", (), None)

            session = self.server.get_session()
            data = "%s:15:10:" % (session.session_id, ",".join(self.handler_types.keys()))
            self.socket.sendall(data)

    def handle_one_response(self):
        self.status = None
        self.headers_sent = False
        self.result = None
        self.response_length = 0
        self.response_use_chunked = False

        path = self.environ.get('PATH_INFO')
        request_method = self.environ.get("REQUEST_METHOD")
        request_tokens = self.RE_REQUEST_URL.match(path)

        if request_tokens:
            request_tokens = request_tokens.groupdict()
        else:
            handshake_tokens = self.RE_HANDSHAKE_URL.match(path)

            if handshake_tokens:
                return self._do_handshake(handshake_tokens.groupdict())
            else:
                raise Exception("TODO")


        if request_tokens["namespace"] != self.server.namespace:
            raise Exception("TODO")

        transport = self.handler_types.get(request_tokens["transport_id"])
        session_id = request_tokens["session_id"]

        # In case this is WebSocket request, switch to the WebSocketHandler
        if transport in (transports.WebsocketTransport, \
                transports.FlashSocketTransport):
            self.__class__ = WebSocketHandler
            self.handle_one_response(call_wsgi_app=False)
            session = self.server.get_session()
        else:
            session = self.server.get_session(session_id)

        # Make the session object available for WSGI apps
        self.environ['socketio'].session = session

        # Create a transport and handle the request likewise
        self.transport = transport(self)
        jobs = self.transport.connect(session, request_method)

        if not session.wsgi_app_greenlet or not bool(session.wsgi_app_greenlet):
            # Call the WSGI application, and let it run until the Socket.IO
            # is *disconnected*, even though many POST/polling requests
            # come through.
            session.wsgi_app_greenlet = gevent.getcurrent()
            session.connected = True
            self.application(self.environ,
                             lambda status, headers, exc=None: None)
            session.connected = False

        gevent.joinall(jobs)
