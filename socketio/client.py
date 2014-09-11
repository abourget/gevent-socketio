# coding=utf-8
"""
Client represents one client, which holds several socketio sockets, and one engineio socket.
"""
from pyee import EventEmitter
import socketio.parser as Parser
import logging
from engine.socket import Socket as EngineSocket

logger = logging.getLogger(__name__)


class Client(EventEmitter):
    def __init__(self, server, engine_socket):
        super(Client, self).__init__()

        self.server = server
        self.engine_socket = engine_socket
        self.sid = engine_socket.sid
        self.sockets = []
        self.namespace_socket = {}
        self.connect_buffer = []

        self.decoder = Parser.Decoder()
        self.encoder = Parser.Encoder()

    def setup(self):
        """
        Setup event listener
        :return:
        """

        self.decoder.on('decoded', self.on_decoded)
        self.engine_socket.on('data', self.on_data)
        self.engine_socket.on('close', self.on_close)

    def connect(self, name):
        """
        Connect the client to a namespace
        :param name:
        :return:
        """

        logger.debug('connecting to namespace %s', name)

        if name not in self.server.namespaces:
            self.packet({
                'type': Parser.ERROR,
                'data': 'Invalid namespace'
            })
            return

        namespace = self.server.of(name)

        if '/' != name and '/' not in self.namespace_socket:
            self.connect_buffer.append(name)
            return

        def callback():
            self.sockets.append(socket)
            self.namespace_socket[name] = socket

            if '/' == namespace.name and self.connect_buffer:
                for n in self.connect_buffer:
                    self.connect(n)
                self.connect_buffer = []

        socket = namespace.add(self, callback)

    def disconnect(self):
        while self.sockets:
            socket = self.sockets.pop(0)
            socket.disconnect()
        self.close()

    def remove(self, socket):
        try:
            index = self.sockets.index(socket)
            nsp = socket.namespace.name
            del self.sockets[index]
            del self.namespace_socket[nsp]
        except ValueError:
            logger.debug('ignoring remove for %s', socket.id)

    def close(self):
        if self.engine_socket.ready_state == EngineSocket.STATE_OPEN:
            logger.debug('forcing transport close')
            self.engine_socket.close()
            self.on_close('forced server close')

    def packet(self, packet, pre_encoded=False):
        if self.engine_socket.state == EngineSocket.STATE_OPEN:
            logger.debug('writing packet %s', str(packet))

            if not pre_encoded:
                encoded_packets = self.encoder.encode(packet)
            else:
                encoded_packets = packet

            for encoded in encoded_packets:
                self.engine_socket.write(encoded)

    def on_data(self, data):
        self.decoder.add(data)

    def on_decoded(self, packet):
        if Parser.CONNECT == packet['type']:
            self.connect(packet['nsp'])
        else:
            socket = self.namespace_socket[packet['nsp']]

            if socket:
                socket.on_packet(packet)
            else:
                logger.debug('no socket for namespace %s', packet['nsp'])

    def on_close(self, reason):
        self.destroy()

        for socket in self.sockets:
            socket.on_close(reason)

        self.decoder.destroy()

    def destroy(self):
        self.engine_socket.remove_listener('data', self.on_data)
        self.engine_socket.remove_listener('close', self.on_close)
        self.decoder.remove_listener('decoded', self.on_decoded)

