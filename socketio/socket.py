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
    'new_listener',
    'remove_listener'
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
        self.id = client.id
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
            # 'address': self.engine_socket.remote_address,
            'xdomain': self.request.headers.get('origin', None),
            'secure': self.request.scheme == 'https',
            'url': self.request.url,
            'query': self.request.GET
        }

    def emit(self, event, *args):
        if event in events:
            super(Socket, self).emit(event, *args)

        else:
            packet = {'type': parser.EVENT}

            if has_bin(args):
                packet['type'] = parser.BINARY_EVENT

            packet['data'] = [event] + list(args)

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
        self.packet({'type': parser.CONNECT})
        self.namespace.connected[self.id] = self

    def on_packet(self, packet):
        logger.debug('got packet %s', packet['type'])

        _type = packet['type']

        if _type == parser.EVENT:
            self.on_event(packet)
        elif _type == parser.BINARY_EVENT:
            self.on_event(packet)
        elif _type == parser.ACK:
            self.on_ack(packet)
        elif _type == parser.BINARY_ACK:
            self.on_ack(packet)
        elif _type == parser.DISCONNECT:
            self.on_disconnect()
        elif _type == parser.ERROR:
            self.emit('error', packet["data"])

    def on_event(self, packet):
        packet_data = packet['data'] if 'data' in packet else []

        if 'id' in packet:
            callback = self.ack(packet['id'])
            raise NotImplementedError()

        event = packet_data.pop(0)
        if len(packet_data) == 1:
            packet_data = packet_data[0]

        # Use the EventEmitter's emit to notify all listener
        super(Socket, self).emit(event, packet_data)

    def ack(self, id):
        def cb(data):
            _type = parser.ACK if not has_bin(data) else parser.BINARY_ACK
            self.packet({
                'id': id,
                'type': _type,
                'data': data
            })
        return cb

    def on_ack(self, packet):
        if 'id' not in packet or packet['id'] not in self.acks:
            logger.debug('bad ack %s', packet['id'])
        else:
            _id = packet['id']
            ack = self.acks[_id]
            ack(packet['data'])
            self.acks.pop(_id)

    def on_disconnect(self):
        logger.debug('got disconnect packet')
        self.on_close('client namespace disconnect')

    def on_close(self, reason=None):
        if not self.connected:
            return

        logger.debug('closing socket - reason %s', reason)
        self.leave_all()
        self.namespace.remove(self)
        self.namespace.connected.pop(self.id)
        self.client.remove(self)
        self.connected = False
        self.disconnected = True
        self.emit('disconnect', reason)

    def disconnect(self, close):
        if not self.connected:
            return self

        if close:
            self.client.disconnect()
        else:
            self.packet({
                'type': parser.DISCONNECT
            })
            self.on_close('server namespace disconnect')

        return self

    @property
    def context(self):
        return self.engine_socket.context