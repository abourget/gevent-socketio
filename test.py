import re
import gevent
from gevent import pywsgi
from gevent.event import AsyncResult
from geventwebsocket.handler import WebSocketHandler

from gevent.server import StreamServer
from gevent.pywsgi import WSGIHandler, WSGIServer

from geventwebsocket.handler import WebSocketHandler


class SocketIOServer(WSGIServer):
    def __init__(self, *args, **kwargs):
        self.sessions = {}
        super(SocketIOServer, self).__init__(*args, **kwargs)

    def handle(self, socket, address):
        print "new connection"
        handler = self.handler_class(socket, address, self)
        self.set_environ({'socketio': SocketIOHandler(handler)})
        handler.handle()
        print "end of connection"


class XHRPollingHandler(WSGIHandler):
    def handle_get_response(self):
        data = None
        self.status = "200 OK"

        #towrite = [
        #    '%s %s\r\n' % (self.request_version, "200 OK"),
        #    "Access-Control-Allow-Origin: *\r\n",
        #]
        self.start_response("200 OK", [("Access-Control-Allow-Origin", "*"),])

        print "wrote header"

        gevent.sleep(5)
        self.write_headers([
            ("Connection", "close"),
            ("Content-Type", "text/plain; charset=UTF-8"),
            ("Content-Length", '0'),
        ])
        self.write("\r\n")
        self.close_connection = True

    def handle_post_response(self):
        self.close_connection = True
        data = self.wsgi_input.readline()
        print "POST data", data

        self.start_response("200 OK", [("Access-Control-Allow-Origin", "*"),])

        print "wrote header"

        self.write_headers([
            ("Connection", "close"),
            ("Content-Type", "text/plain; charset=UTF-8"),
            ("Content-Length", '2'),
        ])
        self.write("\r\nok\r\n")
        self.close_connection = True


    #def write(self, data):
    #    self.wfile.writelines(data)

    def start_response(self, status, headers, exc_info=None):
        self.status = status

        towrite = []
        towrite.append('%s %s\r\n' % (self.request_version, self.status))

        for header in headers:
            towrite.append("%s: %s\r\n" % header)

        #towrite.append("\r\n")
        self.wfile.writelines(towrite)

        self.headers_sent = True

    def write_headers(self, headers):
        towrite = []

        for header in headers:
            towrite.append("%s: %s\r\n" % header)

        towrite.append("\r\n")
        self.wfile.writelines(towrite)

        #self.result = self.application(self.environ, self.start_response)


class Handler(WSGIHandler):
    path_re = re.compile(r"^/(?P<resource>[^/]+)/(?P<protocol>[^/]+)/(?P<session_id>[^/]*)/?(?P<rest>.*)$")

    handler_types = {
        'websocket': WebSocketHandler,
        'wsgi': WSGIHandler,
        'flashsocket': 'FlashSocketHandler',
        'htmlfile': 'HTMLFileHandler',
        'xhr-multipart': 'XHRMultipartHandler',
        'xhr-polling': XHRPollingHandler,
        'jsonp-polling': 'JSONPollingHandler',
    }

    def handle_one_response(self):
        self.status = None
        self.headers_sent = False
        self.result = None
        self.response_length = 0
        self.response_use_chunked = False

        path = self.environ.get('PATH_INFO')
        parts = Handler.path_re.match(path)

        print "Arrived at", path

        if parts:
            parts = parts.groupdict()
            print parts
        else:
            print "closed"
            self.close_connection = True
            return

        resource = parts.get('resource')
        protocol = Handler.handler_types.get(parts.get('protocol'))
        session_id = parts.get('session_id')
        request_method = self.environ.get("REQUEST_METHOD")
        self.__class__ = protocol

        print request_method

        if request_method == "GET":
            if session_id == '':
                session = Session()
                self.server.sessions[session.session_id] = session
                #self.send_one_message(session.session_id)

                message = self.environ['socketio']._encode(session.session_id)
                self.start_response("200 OK", [
                    ("Connection", "close"),
                    ("Access-Control-Allow-Origin", "*"),
                    ("Content-Type", "text/plain; charset=UTF-8"),
                    ("Content-Length", len(message)),
                ])
                self.write("\r\n" + message)
                self.close_connection = 1
            else:
                session = self.server.sessions.get(session_id)

                if session is None:
                    print "Close connection"
                    self.close_connection = True
                else:
                    print "eeej?"
                    self.handle_get_response()


        elif request_method == "POST":
            self.close_connection = True
            self.handle_post_response()



MSG_FRAME = "~m~"
HEARTBEAT_FRAME = "~h~"
JSON_FRAME = "~j~"


import random
class Session(object):
    def __init__(self, session_id=None):
        if session_id is None:
            self.session_id = str(random.random())[2:]
        else:
            self.session_id = session_id


class SocketIOHandler(object):
    def __init__(self, handler):
        self.handler = handler

    def send(self, message, skip_queue=True):
        if skip_queue:
            self.handler._send(self._encode(message))
        else:
            pass

    def wait(self):
        return self._decode(self.handler._wait())

    def _encode(self, message):
        return MSG_FRAME + str(len(message)) + MSG_FRAME + message

    def _decode(self, data):
        messages = []
        #data.encode('utf-8')
        if data is not None:
            while len(data) != 0:
                if messages[0:3] == MSG_FRAME:
                    null, size, data = data.split(MSG_FRAME, 2)
                    size = int(size)

                    frame_type = data[0:3]
                    if frame_type == JSON_FRAME:
                        pass # Do some json parsing of data[3:size]
                    elif frame_type == HFRAME:
                        pass # let the caller process the message?
                    else:
                        messages.append(data[0:size])

                    data = data[size:]
                else:
                    raise Exception("Unsupported frame type")

            return messages
        else:
            return messages


def app(environ, start_response):
    socketio = environ['socketio']
    if environ['PATH_INFO'] == "/test/websocket":
        socketio.send("hai")
        #print socketio.wait()
        start_response("200 OK", [("Content-Type", "text/plain")])
        return ["hoi"]
    if environ['PATH_INFO'].startswith("/test/xhr-polling/"):
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [""]
    else:
        start_response("500 Server Error", [("Content-Type", "text/plain")])
        return ["root"]



server = SocketIOServer(('', 8080), app, handler_class=Handler)
server.serve_forever()

