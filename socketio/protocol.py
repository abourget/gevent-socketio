import gevent
import anyjson as json

from socketio.packet import Packet

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
