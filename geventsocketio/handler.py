import re
import gevent

from gevent.pywsgi import WSGIHandler
from geventsocketio import transports
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket import WebSocket

class SocketIOHandler(WSGIHandler):
    path_re = re.compile(r"^/(?P<resource>[^/]+)/(?P<transport>[^/]+)(/(?P<session_id>[^/]*)/?(?P<rest>.*))?$")

    handler_types = {
        'websocket': transports.WebsocketTransport,
        'wsgi': WSGIHandler,
        'flashsocket': transports.FlaskSocketTransport,
        'htmlfile': transports.HTMLFileTransport,
        'xhr-multipart': transports.XHRMultipartTransport,
        'xhr-polling': transports.XHRPollingTransport,
        'jsonp-polling': transports.JSONPolling,
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

        if parts:
            parts = parts.groupdict()
        else:
            return super(SocketIOHandler, self).handle_one_response()

        resource = parts.get('resource')
        transport = SocketIOHandler.handler_types.get(parts.get('transport'))
        session_id = parts.get('session_id')
        request_method = self.environ.get("REQUEST_METHOD")

        if resource != self.server.resource or not transport:
            return super(SocketIOHandler, self).handle_one_response()

        if transport == transports.WebsocketTransport or \
           transport == transports.FlaskSocketTransport:
            self.__class__ = WebSocketHandler
            self.handle_one_response(call_wsgi_app=False)
            session = self.server.get_session()
        else:
            session = self.server.get_session(session_id)

        self.environ['socketio'].session = session
        self.transport = transport(self)
        jobs = self.transport.connect(session, request_method)
        session.connected = True

        self.application(self.environ, lambda x: x())

        session.connected = False
        gevent.joinall(jobs)
