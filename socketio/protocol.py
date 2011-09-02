import gevent
import anyjson as json


class SocketIOProtocol(object):
    """SocketIO protocol specific functions."""

    def __init__(self, handler):
        self.handler = handler
        self.session = None

    def ack(self, msg_id, params):
        self.send("6:::%s%s" % (msg_id, params))

    def send(self, message, destination=None):
        if destination is None:
            dst_client = self.session
        else:
            dst_client = self.handler.server.sessions.get(destination)

        self._write(message, dst_client)

    def send_event(self, name, *args):
        self.send("5:::" + json.dumps({'name': name, 'args': args}))

    def receive(self):
        """Wait for incoming messages."""

        return self.session.get_server_msg()

    def broadcast(self, message, exceptions=None, include_self=False):
        """
        Send messages to all connected clients, except itself and some
        others.
        """

        if exceptions is None:
            exceptions = []

        if not include_self:
            exceptions.append(self.session.session_id)

        for session_id, session in self.handler.server.sessions.iteritems():
            if session_id not in exceptions:
                self._write(message, session)

    def broadcast_event(self, name, *args, **kwargs):
        self.broadcast("5:::" + json.dumps({'name': name, 'args': args}), **kwargs)

    def start_heartbeat(self):
        """Start the heartbeat Greenlet to check connection health."""
        def ping():
            self.session.state = self.session.STATE_CONNECTED

            while self.session.connected:
                gevent.sleep(5.0) # FIXME: make this a setting
                self.send("2::")

        return gevent.spawn(ping)

    def _write(self, message, session=None):
        if session is None:
            raise Exception("No client with that session exists")
        else:
            session.put_client_msg(message)

    def encode(self, message):
        if isinstance(message, basestring):
            encoded_msg = message
        elif isinstance(message, (object, dict)):
            return self.encode(json.dumps(message))
        else:
            raise ValueError("Can't encode message")

        return encoded_msg

    def decode(self, data):
        messages = []
        data.encode('utf-8', 'replace')
        msg_type, msg_id, tail = data.split(":", 2)

        print "RECEVIED MSG TYPE ", msg_type

        if msg_type == "0":
            self.session.kill()
            return None

        elif msg_type == "1":
            self.send("1::%s" % tail)
            return None

        elif msg_type == "2":
            self.session.heartbeat()
            return None

        msg_endpoint, data = tail.split(":", 1)

        if msg_type == "3":
            message = {
                'type': 'message',
                'data': data,
            }
            messages.append(message)
        elif msg_type == 4:
            messages.append(json.loads(data))
        elif msg_type == "5":
            message = json.loads(data)

            if "+" in msg_id:
                message['id'] = msg_id
            else:
                pass # TODO send auto ack
            message['type'] = 'event'
            messages.append(message)
        else:
            raise Exception("Unknown message type: %s" % msg_type)

        return messages[0]
