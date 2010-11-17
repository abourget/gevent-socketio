import urllib
import gevent

try:
    import simplejson as json
except ImportError:
    import json


MSG_FRAME = "~m~"
HEARTBEAT_FRAME = "~h~"
JSON_FRAME = "~j~"

class SocketIOProtocol(object):
    def __init__(self, handler):
        self.handler = handler
        self.session = None

    def connected(self):
        return self.session.connected

    def send(self, message, destination=None):
        if destination is None:
            self._write(message, session)
        else:
            dst = self.handler.server.sessions.get(destination)
            self._write(message, dst)

    def recv(self):
        return self.session.get_server_msg()

    def broadcast(self, message, exceptions=None):
        if exceptions is None:
            exceptions = []

        exceptions.append(self.session.session_id)

        for session_id, session in self.handler.server.sessions.iteritems():
            if session_id not in exceptions:
                self._write(message, session)

    def start_heartbeat(self):
        def ping():
            while self.connected():
                gevent.sleep(10)
                hb = HEARTBEAT_FRAME + str(self.session.heartbeats())
                print hb
                self._write(hb, self.session)

        return gevent.spawn(ping)

    def check_heartbeat(self, counter):
        # TODO: check for valid counter value
        print "pong", counter
        # TODO: check if we have a timeout

    def _write(self, message, session=None):
        if session is None:
            raise Exception("No client with that session exists")
        else:
            session.put_client_msg(message)

    def _encode(self, message):
        encoded_msg = ''

        #if isinstance(message, list):
        #    for msg in message:
        #        encoded_msg += self._encode(msg)
        if isinstance(message, basestring):
            encoded_msg += message
        elif isinstance(message, (object, dict)):
            encoded_msg += self._encode(JSON_FRAME + json.dumps(message))

        return MSG_FRAME + str(len(encoded_msg)) + MSG_FRAME + encoded_msg

    def _decode(self, data):
        messages = []
        data.encode('utf-8', 'replace')
        data = urllib.unquote_plus(data)
        if data:
            while len(data) != 0:
                if data[0:3] == MSG_FRAME:
                    null, size, data = data.split(MSG_FRAME, 2)
                    size = int(size)

                    frame_type = data[0:3]
                    if frame_type == JSON_FRAME:
                        messages.append(json.loads(data[0:size]))
                    elif frame_type == HEARTBEAT_FRAME:
                        self.check_heartbeat(data[0:size])
                    else:
                        messages.append(data[0:size])

                    data = data[size:]
                else:
                    raise Exception("Unsupported frame type")

            return messages
        else:
            return messages
