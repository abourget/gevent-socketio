import re
from gevent.pywsgi import WSGIHandler
from geventsocketio import transports
from geventsocketio.protocol import Session


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

        if request_method == "GET":
            if session_id == '':
                # Create a new session and close connection
                session = Session()
                self.server.sessions[session.session_id] = session

                message = self.environ['socketio']._encode(session.session_id)
                self.start_response("200 OK", [
                    ("Connection", "close"),
                    ("Access-Control-Allow-Origin", "*"),
                    ("Content-Type", "text/plain; charset=UTF-8"),
                    ("Content-Length", len(message)),
                ])
                self.write(message)
            else:
                # Session has been found, handle this request using a Socket.IO transport
                self.socketio_connection = True
                session = self.server.sessions.get(session_id)

                if session is None:
                    print "Close connection"
                    self.close_connection = True
                else:
                    print "eeej?"
                    self.transport.handle_get_response()


        elif request_method == "POST":
            self.close_connection = True
            #self.transport.handle_post_response()

        self.socketio_connection = False

    def start_response(self, status, headers, exc_info=None):
        if self.socketio_connection:
            self.status = status

            towrite = []
            towrite.append('%s %s\r\n' % (self.request_version, self.status))

            for header in headers:
                towrite.append("%s: %s\r\n" % header)

            self.wfile.writelines(towrite)
            self.headers_sent = True
        else:
            super(SocketIOHandler, self).start_response(status, headers, exc_info)

    def write_more_headers(self, headers):
        towrite = []

        for header in headers:
            towrite.append("%s: %s\r\n" % header)

        towrite.append("\r\n")
        self.wfile.writelines(towrite)

