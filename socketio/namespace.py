# coding=utf-8
from __future__ import absolute_import
from functools import partial
import logging
from pyee import EventEmitter
from socketio import has_bin
from socketio.adapter import Adapter
from socketio.socket import Socket
from socketio.engine.socket import Socket as EngineSocket
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
        self.adapter = Adapter(self)

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
            socket.on_connect()

            if callback:
                callback(socket)

            self.emit('connect', socket)
            self.emit('connection', socket)
        else:
            logger.debug('Client was closed, ignore socket')

        return socket

    def remove(self, socket):
        if socket in self.sockets:
            self.sockets.remove(socket)
            super(Namespace, self).emit('disconnect', socket)
        else:
            logger.debug('ignoring remove for %s', socket.id)

    def emit(self, event, *args):
        if event in ['connect', 'connection', 'newListener']:
            super(Namespace, self).emit(event, *args)
        else:
            _type = SocketIOParser.EVENT

            if has_bin(args):
                _type = SocketIOParser.BINARY_EVENT

            packet = {'type': _type, 'data': args}
            self.adapter.broadcast(packet, {
                'rooms': self.rooms,
            })
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
