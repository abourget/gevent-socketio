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

    def __init__(self, type, name=None, data=None, endpoint=None, msgid=None,
                 ack_with_data=False, query_string=None, error_reason=None,
                 error_advice=None, error_msg=None):
        """Models a packet

        ``type`` - One of the packet types above (MESSAGE, JSON, EVENT, etc..)
        ``name`` - The name used for the EVENT
        ``data`` - The actual data, before encoding
        ``endpoint`` - the Namespace's name to send the packet
        ``id`` - TODO: TO BE UNDERSTOOD!
        ``ack_with_data`` - If True, return data (should be a sequence) with ack.
        ``error_reason`` - one of ERROR_* values
        ``error_advice`` - one of ADVICE_* values
        ``error_msg``- an error message to be displayed
        """
        self.type = type
        self.name = name
        self.msgid = msgid
        self.endpoint = endpoint
        self.ack_with_data = ack_with_data
        self.data = data
        self.query_string = query_string
        if self.type == Packet.ACK and not msgid:
            raise ValueError("An ACK packet must have a message 'msgid'")

    @property
    def query(self):
        """Transform the query_string into a dictionary"""
        # TODO: do it
        return {}

    def encode(self):
        """Encode this packet into a byte string"""
        data = ''
        type = self.type
        msgid = self.msgid or ''
        endpoint = self.endpoint or ''

        if type == Packet.ACK:
            # TODO: distinguish between the ACK_ID and the PACKET ID!?!
            if self.ack_with_data:
                # TODO: check! in that case, `data` should be a sequence!
                data = msgid + '+' + json.dumps(list(self.data))
                msgid += '+'
        elif type == Packet.EVENT:
            ev = {"name": self.name}
            if self.data:
                ev['args'] = self.data
            data = json.dumps(ev)
        elif type == Packet.MESSAGE and self.data:
            data = self.data
        elif type == Packet.JSON:
            data = json.dumps(self.data)
        elif type == Packet.CONNECT:
            data = self.query_string or ''
        elif type == Packet.ERROR:
            data = self.error_reason or ''
            if self.error_advice:
                data += '+' + self.error_advice

        out = type + ':' + msgid + ':' + endpoint
        if data:
            out += ':' + data
        return out

    @staticmethod
    def decode(data):
        """Decode a rawstr arriving from the channel into a valid Packet object
        """
        # decode the stuff
        #data.encode('utf-8', 'ignore')
        msg_type, msg_id, tail = data.split(":", 2)

        #print "RECEIVED MSG TYPE ", msg_type, data

        if msg_type == "0": # disconnect
            self.socket.kill()
            return {'endpoint': tail, 'type': 'disconnect'}

        elif msg_type == "1": # connect
            self.send_message("1::%s" % tail)
            return {'endpoint': tail, 'type': 'connect'}

        elif msg_type == "2": # heartbeat
            self.socket.heartbeat()
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

        return Packet(type, data, endpoint, msgid, ack)



class SocketIOProtocol(object):
    """SocketIO protocol specific functions."""

    def __init__(self, handler):
        self.handler = handler
        self.socket = None
        self.ack_count = 0

    def ack(self, msg_id, params):
        self.send_message("6:::%s+%s" % (msg_id, json.dumps(params)))

    def emit(self, event, endpoint, *args):
        self.send_message("5::%s:%s" % (endpoint, json.dumps({'name': event,
                                                      'args': args})))

    def send_message(self, message, destination=None):
        if destination is None:
            dst_client = self.socket
        else:
            dst_client = self.handler.server.sockets.get(destination)

        self._write(message, dst_client)

    def send(self, message):
        self.send_message("3:::%s" % message)

    def send_event(self, name, *args):
        self.send_message("5:::" + json.dumps({'name': name, 'args': args}))

    def receive(self):
        """Wait for incoming messages."""

        return self.socket.get_server_msg()

    def broadcast(self, message, exceptions=None, include_self=False):
        """
        Send messages to all connected clients, except itself and some
        others.
        """

        if exceptions is None:
            exceptions = []

        if not include_self:
            exceptions.append(self.socket.sessid)

        for sessid, socket in self.handler.server.sockets.iteritems():
            if sessid not in exceptions:
                self._write(message, socket)

    def broadcast_event(self, name, *args, **kwargs):
        self.broadcast("5:::" + json.dumps({'name': name, 'args': args}), **kwargs)

    def start_heartbeat(self):
        """Start the heartbeat Greenlet to check connection health."""
        def ping():
            self.socket.state = self.socket.STATE_CONNECTED

            while self.socket.connected:
                gevent.sleep(5.0) # FIXME: make this a setting
                self.send_message("2::")

        return gevent.spawn(ping)

    def _write(self, message, socket=None):
        if socket is None:
            raise Exception("No client with that socket exists")
        else:
            socket.put_client_msg(message)

    def encode(self):
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
