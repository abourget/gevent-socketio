# coding=utf-8
import logging
from pyee import EventEmitter
from socketio.socket import Socket
from engine.socket import Socket as EngineSocket
import socketio.parser as SocketIOParser

logger = logging.getLogger(__name__)


class Namespace(EventEmitter):
    # TODO Add middleware support which able to do auth

    def __init__(self, server, name):
        self.name = name
        self.server = server
        self.sockets = []
        self.connected = {}
        self.ids = 0
        self.acks = {}
        self.rooms = {}
        self.rooms_send_to = None
        self.jobs = []
        super(Namespace, self).__init__()

    def to(self, name):
        if name not in self.rooms_send_to:
            self.rooms_send_to.append(name)

        return self

    def add(self, client, callback=None):
        logger.debug('adding client to namespace %s', self.name)

        socket = Socket(self, client)

        if client.engine_socket.ready_state == EngineSocket.STATE_OPEN:
            self.sockets.append(socket)
            #socket.on_connect()
            if callback:
                callback()

            self.emit('connect', socket)
            self.emit('connection', socket)
        else:
            logger.debug('Client was closed, ignore socket')

        return socket

    def remove(self, socket):
        if socket in self.sockets:
            self.sockets.remove(socket)
        else:
            logger.debug('ignoring remove for %s', socket.id)

    def emit(self, event, *args):
        if event in ['connect', 'connection', 'newListener']:
            self.emit(event, *args)
        else:
            ids = set()
            _type = SocketIOParser.EVENT

            if has_bin(args):
                _type = SocketIOParser.BINARY_EVENT

            packet = {'type': _type, 'data': args, 'nsp': self.name}
            encoded = SocketIOParser.Encoder.encode(packet)

            if self.rooms_send_to:
                for room in self.rooms_send_to:
                    if room not in self.rooms:
                        continue
                    for id in self.rooms[room]:
                        if id in ids:
                            continue
                        socket = self.connected[id]
                        if socket:
                            socket.packet(encoded, pre_encoded=True)
                            ids.add(socket.id)
            else:
                for id, socket in self.connected.items():
                    if socket:
                        socket.packet(encoded, pre_encoded=True)

            self.rooms = None

        return self

    def send(self, *args):
        self.emit('message', *args)

        return self

    write = send

    def get_id(self, increment=False):
        """
        Get id for this namespace
        :param increment:
        :return:
        """
        result = self.ids

        if increment:
            self.ids += 1

        return result


def has_bin(*args):
    for arg in args:
        if type(arg) is bytearray:
            return True

    return False
