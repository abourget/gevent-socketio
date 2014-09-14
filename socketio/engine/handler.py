# coding=utf-8
"""
The wsgi handler for Engine, it accepts requests for engine protocol
"""
from __future__ import absolute_import

import gevent
from gevent.pywsgi import WSGIHandler
from pyee import EventEmitter
from webob import Request
from .response import Response
from .socket import Socket
import logging

logger = logging.getLogger(__name__)


class EngineHandler(WSGIHandler, EventEmitter):
    transports = ('polling', 'websocket')
    clients = {}

    def __init__(self, config, *args, **kwargs):
        """Create a new SocketIOHandler.

        :param config: dict Configuration for timeouts and intervals
          that will go down to the other components, transports, etc..

        """
        self.config = config

        super(EngineHandler, self).__init__(*args, **kwargs)
        EventEmitter.__init__(self)

        if self.server.transports:
            self.transports = self.server.transports

    def handle_one_response(self):
        """
        If there is no socket, then do handshake, which creates a virtual socket.
        The socket is the abstraction of transport and parser
        :return:
        """
        request = None

        try:
            path = self.environ.get('PATH_INFO')

            if not path.lstrip('/').startswith(self.server.resource + '/'):
                return super(EngineHandler, self).handle_one_response()

            # Create a request and a response
            request = Request(self.get_environ())
            setattr(request, 'handler', self)
            setattr(request, 'response', Response())

            sid = request.GET.get("sid", None)
            b64 = request.GET.get("b64", False)

            socket = self.clients.get(sid, None)

            if socket is None:
                self._do_handshake(b64=b64, request=request)
            elif 'Upgrade' in request.headers:
                upgrade = request.headers['Upgrade']
                raise NotImplementedError()
            else:
                gevent.spawn(socket.on_request, request)

            # wait till the response ends
            request.response.join()

            self.application = request.response
            super(EngineHandler, self).handle_one_response()
        finally:
            if hasattr(self, 'websocket') and self.websocket:
                if hasattr(self.websocket, 'environ'):
                    del self.websocket.environ
                del self.websocket
            if self.environ:
                del self.environ

    def _do_handshake(self, b64, request):
        transport_name = request.GET.get('transport', None)
        if transport_name not in self.transports:
            raise ValueError("transport name [%s] not supported" % transport_name)

        socket = Socket(request)
        socket.on_request(request)

        self.clients[socket.id] = socket

        request.response.headers['Set-Cookie'] = 'io=%s' % socket.id
        socket.on_open()

        self.emit('connection', socket)
