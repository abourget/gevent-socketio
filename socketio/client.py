# coding=utf-8
"""
Client represents one client, which holds several socketio sockets, and one engineio socket.
"""
from pyee import EventEmitter


class Client(EventEmitter):
    def __init__(self, server, engine_socket):
        super(Client, self).__init__()

        self.server = server
        self.engine_socket = engine_socket
        self.sid = engine_socket.sid
        self.sockets = []
        self.namespaces = {}
        self.connect_buffer = []

        raise NotImplementedError()
