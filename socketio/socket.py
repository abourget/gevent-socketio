# coding=utf-8
from pyee import EventEmitter


class Socket(EventEmitter):

    def __init__(self, namespace, client):
        super(Socket, self).__init__()

        # Underlying engine socket
        self.namespace = namespace
        self.engine_socket = client.engine_socket
