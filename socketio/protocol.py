import gevent
import anyjson as json


class Packet(object):
    # Message types
    DISCONNECT = "0"
    CONNECT = "1"
    HEARTBEAT = "2"
    MESSAGE = "3"
    JSON = "4"
    EVENT = "5"
    ACK = "6"
    ERROR = "7"
    NOOP = "8"

    # Error reasons
    ERROR_TRANSPORT_NOT_SUPPORTED = "0"
    ERROR_CLIENT_NOT_HANDSHAKEN = "1"
    ERROR_UNAUTHORIZED = "2"

    # Advices
    ADVICE_RECONNECT = "0"

    def __init__(self, type, name=None, data=None, endpoint=None, id=None,
                 ack=None):
        """Models a packet

        ``type`` - One of the packet types above (MESSAGE, JSON, EVENT, etc..)
        ``name`` - The name used for the EVENT
        ``data`` - The actual data, before encoding
        ``endpoint`` - the Namespace's name to send the packet
        ``id`` - TODO: TO BE UNDERSTOOD!
        ``ack`` - TODO: TO BE UNDERSTOOD!
        """
        self.type = type
        self.name = name
        self.id = id
        self.endpoint = endpoint
        self.ack = ack
        self.data = data

    def encode(self):
        """Encode this packet into a byte string"""
        data = None
        if self.type == Packet.MESSAGE and self.data:
            data = self.data
        if self.type == Packet.EVENT:
            data = {"name": "something"}
        pass

    @staticmethod
    def decode(data):
        """Decode a rawstr arriving from the channel into a valid Packet object
        """
        # decode the stuff
        #data.encode('utf-8', 'ignore')
        msg_type, msg_id, tail = data.split(":", 2)

        #print "RECEIVED MSG TYPE ", msg_type, data

        if msg_type == "0": # disconnect
            self.session.kill()
            return {'endpoint': tail, 'type': 'disconnect'}

        elif msg_type == "1": # connect
            self.send_message("1::%s" % tail)
            return {'endpoint': tail, 'type': 'connect'}

        elif msg_type == "2": # heartbeat
            self.session.heartbeat()
            return None

        msg_endpoint, data = tail.split(":", 1)
        message = {'endpoint': msg_endpoint}

        if msg_type == "3": # message
            message['type'] = 'message'
            message['data'] = data
        elif msg_type == "4": # json msg
            message['type'] = 'json'
            message['data'] = json.loads(data)
        elif msg_type == "5": # event
            #print "EVENT with data", data
            message.update(json.loads(data))

            if "+" in msg_id:
                message['id'] = msg_id
            else:
                pass # TODO send auto ack
            message['type'] = 'event'
        elif msg_type == "6": # ack
            message['type'] = 'ack?'
        elif msg_type == "7": # error
            message['type'] = 'error'
            els = data.split('+', 1)
            message['reason'] = els[0]
            if len(els) == 2:
                message['advice'] = els[1]
        elif msg_type == "8": # noop
            return None
        else:
            raise Exception("Unknown message type: %s" % msg_type)

        return Packet(type, data, endpoint, id, ack)


class SocketIOProtocol(object):
    """SocketIO protocol specific functions."""

    def __init__(self, handler):
        self.handler = handler
        self.session = None

    def ack(self, msg_id, params):
        self.send_message("6:::%s+%s" % (msg_id, json.dumps(params)))

    def emit(self, event, endpoint, *args):
        self.send_message("5::%s:%s" % (endpoint, json.dumps({'name': event,
                                                      'args': args})))

    def send_message(self, message, destination=None):
        if destination is None:
            dst_client = self.session
        else:
            dst_client = self.handler.server.sessions.get(destination)

        self._write(message, dst_client)

    def send(self, message):
        self.send_message("3:::%s" % message)

    def send_event(self, name, *args):
        self.send_message("5:::" + json.dumps({'name': name, 'args': args}))

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
                self.send_message("2::")

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
            return json.dumps(message)
        else:
            raise ValueError("Can't encode message")

        return encoded_msg

    def decode(self, data):
        p = Packet.decode(data)
        return p
