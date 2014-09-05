# coding=utf-8
"""
The wsgi handler for Engine, it accepts requests for engine protocol
"""
from __future__ import absolute_import

import copy
import urlparse
import weakref
import gevent
from gevent.pywsgi import WSGIHandler
import sys
from pyee import EventEmitter
from webob import Request, Response
from . import transports
from .socket import Socket


class EngineHandler(WSGIHandler, EventEmitter):
    clients = {}

    handler_types = {
        'websocket': transports.WebsocketTransport,
        'flashsocket': transports.FlashSocketTransport,
        'xhr-polling': transports.XHRPollingTransport,
        'polling': transports.XHRPollingTransport,
        'jsonp-polling': transports.JSONPollingTransport,
    }

    def __init__(self, config, *args, **kwargs):
        """Create a new SocketIOHandler.

        :param config: dict Configuration for timeouts and intervals
          that will go down to the other components, transports, etc..

        """
        self.config = config
        self.request = None
        self.response = None

        super(EngineHandler, self).__init__(*args, **kwargs)
        EventEmitter.__init__(self)

        self.transports = self.handler_types.keys()

        if self.server.transports:
            self.transports = self.server.transports
            if not set(self.transports).issubset(set(self.handler_types)):
                raise ValueError("transports should be elements of: %s" %
                    (self.handler_types.keys()))

        self.out_headers = {}

    def handle_one_response(self):
        try:
            path = self.environ.get('PATH_INFO')

            if not path.lstrip('/').startswith(self.server.resource + '/'):
                return super(EngineHandler, self).handle_one_response()

            # Create a request and a response and attach the handler instance to each of them
            self.request = Request(self.get_environ())
            setattr(self.request, 'handler', weakref.ref(self))

            self.response = Response()
            setattr(self.response, 'handler', weakref.ref(self))

            qs_dict = self.request.GET

            transport = qs_dict.get("transport", None)
            sid = qs_dict.get("sid", None)
            b64 = qs_dict.get("b64", False)

            socket = self.clients.get(sid, None)

            if socket is None:
                self._do_handshake(transport_name=transport, b64=b64)

                self.application = self.response
                self.close_connection = True
                super(EngineHandler, self).handle_one_response()
                return

            if 'Upgrade' in self.request.headers:
                upgrade = self.request.headers['Upgrade']
                raise NotImplementedError()
            else:
                socket.transport.on_handler(self)

            # Check the response which should be filled already, set it as the application callable and do cleanup
            try:
                self.close_connection = True
                self.application = self.response
                super(EngineHandler, self).handle_one_response()
                return
            finally:
                # Clean up circular references so they can be garbage collected.
                if hasattr(self, 'websocket') and self.websocket:
                    if hasattr(self.websocket, 'environ'):
                        del self.websocket.environ
                    del self.websocket
                if self.environ:
                    del self.environ
        finally:
            self.emit("cleanup")

    def _do_handshake(self, transport_name, b64=False):
        if transport_name not in self.handler_types:
            raise ValueError("transport name [%s] not supported" % transport_name)

        options = copy.copy(self.config)
        options['supports_binary'] = not b64

        transport_class = self.handler_types[transport_name]
        transport = transport_class(self, options)
        transport.on_handler(self)

        socket = Socket(transport)
        self.clients[socket.sessid] = socket

        self.out_headers['Set-Cookie'] = 'io=%s' % socket.sessid
        socket.on_open()

    def write_jsonp_result(self, data, wrapper="0"):
        self.start_response("200 OK", [
            ("Content-Type", "application/javascript"),
        ])
        self.result = ['io.j[%s]("%s");' % (wrapper, data)]

    def write_plain_result(self, data):
        self.start_response("200 OK", [
            ("Access-Control-Allow-Origin", self.environ.get('HTTP_ORIGIN', '*')),
            ("Access-Control-Allow-Credentials", "true"),
            ("Access-Control-Allow-Methods", "POST, GET, OPTIONS"),
            ("Access-Control-Max-Age", 3600),
            ("Content-Type", "text/plain"),
        ])
        self.result = [data]
