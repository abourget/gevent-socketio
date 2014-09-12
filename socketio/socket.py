# coding=utf-8
from datetime import datetime
from pyee import EventEmitter
from socketio import has_bin
from socketio import parser
import logging

logger = logging.getLogger(__name__)

events = [
    'error',
    'connect',
    'disconnect',
    'newListener',
    'removeListener'
]

flags = [
    'json',
    'volatile',
    'broadcast'
]


class Socket(EventEmitter):

    def __init__(self, namespace, client):
        super(Socket, self).__init__()

        # Underlying engine socket
        self.namespace = namespace
        self.adapter = namespace.adapter
        self.server = namespace.server
        # FIXME where assigned client id?
        self.id = client.id
        # FIXME not able to get request
        self.request = client.request
        self.client = client
        self.engine_socket = client.engine_socket
        self.rooms = []
        self.rooms_send_to = None
        self.flags = {}
        self.acks = {}
        self.connected = True
        self.disconnected = False
        self.handshake = self.build_handshake()

    def build_handshake(self):
        return {
            'headers': self.request.headers,
            'time': str(datetime.now()),
            # FIXME set remote_address in engine_socket
            'address': self.engine_socket.remote_address,
            'xdomain': self.request.headers['origin'],
            # FIXME how to get the schema?
            'secure': self.request.connection.encrypted,
            'url': self.request.url,
            'query': self.request.GET
        }

    def emit(self, event, *args):
        if event in events:
            super(Socket, self).emit(event, *args)

        else:
            packet = {}
            packet['type'] = Parser.EVENT

            if has_bin(args):
                packet['type'] = Parser.BINARY_EVENT

            packet['data'] = args

            # TODO ADD ack callback

            if self.rooms_send_to or 'broadcast' in self.flags:
                self.adapter.broadcast(packet, {
                    'except': [self.id],
                    'rooms': self.rooms_send_to,
                    'flags': self.flags
                })
            else:
                self.packet(packet)

        self.rooms_send_to = None
        self.flags = {}

    def to(self, name):
        self.rooms_send_to = self.rooms_send_to or []

        if name not in self.rooms_send_to:
            self.rooms_send_to.append(name)

        return self

    def send(self, *args):
        self.emit('message', *args)
        return self

    write = send

    def packet(self, p, pre_encoded=False):
        p['nsp'] = self.namespace.name
        self.client.packet(p, pre_encoded)

    def join(self, room, callback=None):
        logger.debug('joining room %s', room)
        if room in self.rooms:
            return self

        def cb(err=None):
            if err:
                return cb and cb(err)
            logger.debug('joined room %s', room)
            self.rooms.append(room)
            callback and callback()

        self.adapter.add(self.id, room)
        return self

    def leave(self, room, callback=None):
        logger.debug('leaving room %s', room)

        def cb(err):
            if err:
                return callback and callback(err)

            logger.debug('left room %s', room)
            self.rooms.remove(room)
            callback and callback()

        self.adapter.remove(self.id, room, cb)
        return self

    def leave_all(self):
        self.adapter.remove_all(self.id)
        self.rooms = []

    def on_connect(self):
        logger.debug('socket connected - writing packet')
        self.join(self.id)
        self.packet({ 'type': parser.CONNECT })
        self.namespace.connected[self.id] = self

    def on_packet(self, packet):
        logger.debug('got packet %s', packet['type'])
