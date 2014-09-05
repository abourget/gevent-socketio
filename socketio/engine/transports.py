import json
import urllib
import urlparse

from geventwebsocket import WebSocketError
from gevent.queue import Empty
from pyee import EventEmitter

import logging
import re
from .parser import Parser

logger = logging.getLogger(__name__)


class BaseTransport(EventEmitter):
    """
    Base class for all transports. Mostly wraps handler class functions.

    Life cycle for a transport:
    A transport object lives cross the whole socket session.
    One handler lives for one request, so one transport will survive for
    multiple handler objects.

    """
    name = "Base"

    def __init__(self, handler, config, **kwargs):
        """Base transport class.

        :param config: dict Should contain the config keys, like
          ``heartbeat_interval``, ``heartbeat_timeout`` and
          ``close_timeout``.

        """

        super(BaseTransport, self).__init__()

        self.content_type = ("Content-Type", "text/plain; charset=UTF-8")
        self.headers = [
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Credentials", "true"),
            ("Access-Control-Allow-Methods", "POST, GET, OPTIONS"),
            ("Access-Control-Max-Age", 3600),
        ]

        self.supports_binary = config.pop("supports_binary", True)
        self.ready_state = "opening"

        self.handler = handler
        self.config = config

        self.request = None
        self.writable = False
        self.should_close = False

    def write(self, data=""):
        # Gevent v 0.13
        if hasattr(self.handler, 'response_headers_list'):
            if 'Content-Length' not in self.handler.response_headers_list:
                self.handler.response_headers.append(('Content-Length', len(data)))
                self.handler.response_headers_list.append('Content-Length')
        elif not hasattr(self.handler, 'provided_content_length') or self.handler.provided_content_length is None:
            # Gevent 1.0bX
            l = len(data)
            self.handler.provided_content_length = l
            self.handler.response_headers.append(('Content-Length', l))

        self.handler.write_smart(data)

    def _close(self):
        raise NotImplementedError()

    def close(self):
        self.ready_state = 'closing'
        self._close()

    def _cleanup(self):
        logger.debug('clean up in transport')
        self.handler.remove_listener('cleanup', self._cleanup)
        self.request = None
        self.handler = None

    def on_handler(self, handler):
        self.handler = handler
        self.request = handler.request

        self.handler.on("cleanup", self._cleanup)

    def on_error(self, message, description=None):
        if self.listeners('error'):
            self.emit('error', {
                'type': 'TransportError',
                'description': description
            })
        else:
            logger.debug("Ignored transoport error %s (%s)" % (message, description))

    def on_packet(self, packet):
        self.emit('packet', packet)

    def on_data(self, data):
        self.on_packet(Parser.decode_packet(data))

    def on_close(self):
        self.ready_state = 'closed'
        self.emit('close')


class PollingTransport(BaseTransport):
    name = "polling"

    def __init__(self, *args, **kwargs):
        self.data_request = None
        super(PollingTransport, self).__init__(*args, **kwargs)

    def on_handler(self, handler):
        super(PollingTransport, self).on_handler(handler)

        request = handler.request
        if request.method == 'GET':
            self.on_poll_request(request)
        elif request.method == 'POST':
            self.on_data_request(request)
        else:
            pass

    def _cleanup(self):
        self.request = None
        self.data_request = None
        super(PollingTransport, self)._cleanup()

    def on_poll_request(self, request):
        if self.request is not request:
            logger.debug('request overlap')
            self.on_error('overlap from client')
            self.handler.response.status = 500
            return

        logger.debug('setting request')

        self.request = request
        # TODO set response?

        # TODO setup response clean up logic

        self.writable = True
        self.emit('drain')

        if self.writable and self.should_close:
            logger.debug('triggering empty send to append close packet')
            self.send([{'type': 'noop'}])

    def on_data_request(self, request):
        """
        The client sends a request with data.
        :param request:
        :return:
        """
        if self.data_request is not request:
            self.on_error('data request overlap from client')
            # TODO write 500
            return

        is_binary = 'application/octet-stream' == request.headers['content-type']
        self.data_request = request
        # TODO SET DATA RESPONSE
        # TODO SET UP CLEAN LOGIC

        chunks = bytearray() if is_binary else ''

        chunks += self.data_request.body
        self.emit('data', chunks)
        self.handler.response.status = 200
        self.handler.response.headers = self.handler.request.headers
        self.handler.response.headers.update({
            'Content-Length': 2,
            'Content-Type': 'text/html'
        })
        self.handler.response.body = 'ok'
        return


    def on_data(self, data):
        """
        Processes the incoming data payload
        :param data:
        :return:
        """

        logger.debug('received %s', data)

        for packet in Parser.decode_payload(data):
            if packet['type'] == 'close':
                logger.debug('got xhr close packet')
                # TODO close this
                self.on_close()
                break
            self.on_packet(packet)

    def send(self, packets):
        """
        Encode and Send packets
        :param packets: The packets list
        :return: None
        """
        if self.should_close:
            packets.push({type: 'close'})
            self.on('should_close') # Use event as callback to do the close logic
            self.should_close = False

        encoded = Parser.encode_payload(packets, self.supports_binary)
        self.write(encoded)

    def write(self, data=""):
        logger.debug('writing %s' % data)

        self.do_write(data)
        self.writable = False

    def do_write(self, data):
        raise NotImplementedError()

    def do_close(self):
        logger.debug('closing')

        if self.data_request:
            logger.debug('aborting ongoing data request')
            # self.data_request.abort()

        if self.writable:
            self.send([{'type': 'close'}])

        else:
            logger.debug('transport not writable - buffering orderly close')
            self.should_close = True # TODO SHOULD CLOSE IS A CALLBACK PASSED BY DO_CLOSE


class XHRPollingTransport(PollingTransport):

    def on_handler(self, handler):
        super(XHRPollingTransport, self).on_handler(handler)

        request = handler.request
        if 'OPTIONS' == request.method:
            self.handler.response.headers = self.handler.request.headers
            self.handler.response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            self.handler.response.status = 200


    def do_write(self, data):
        is_string = type(data) == str
        content_type = 'text/plain; charset=UTF-8' if is_string else 'application/octet-stream'
        content_length = str(len(data))

        headers = {
            'Content-Type': content_type,
            'Content-Length': content_length
        }

        ua = self.request.headers['user-agent']
        if ua and (ua.find(';MSIE') == -1 or ua.find('Trident/') == -1):
            headers['X-XSS-Protection'] = '0'

        self.handler.response.status = 200
        headers = self.merge_headers(self.request, headers)
        self.handler.response.headers = headers
        self.handler.response.body = bytes(data)

    def merge_headers(self, request, headers=None):
        if not headers:
            headers = {}

        if 'origin' in request.headers:
            headers['Access-Control-Allow-Credentials'] = 'true'
            headers['Access-Control-Allow-Origin'] = request.headers['origin']
        else:
            headers['Access-Control-Allow-Origin'] = '*'

        self.emit('headers', headers)
        return headers


class JSONPollingTransport(PollingTransport):
    def __init__(self, request, handler, config):
        super(JSONPollingTransport, self).__init__(handler, config)
        cn = re.sub('[^0-9]', '', self.request.query['j'] or '')
        self.head = '___eio[' + cn + ']('
        self.foot = ');'

    def on_data(self, data):
        data = urlparse.parse_qsl(data)['d']

        if type(data) == str:
            # TODO ESCAPE HANDLING
            super(JSONPollingTransport, self).on_data(data)

    def do_write(self, data):
        js = json.dumps(data)

        args = urlparse.parse_qs(self.handler.environ.get("QUERY_STRING"))
        if "i" in args:
            i = args["i"]
        else:
            i = "0"

        super(JSONPollingTransport, self).write("io.j[%s]('%s');" % (i, data))


class WebsocketTransport(BaseTransport):
    name = 'websocket'

    def do_exchange(self, socket, request_method):
        websocket = self.handler.environ['wsgi.websocket']
        websocket.send("1::")  # 'connect' packet

        def send_into_ws():
            while True:
                message = socket.get_client_msg()

                if message is None:
                    break
                try:
                    websocket.send(message)
                except (WebSocketError, TypeError):
                    # We can't send a message on the socket
                    # it is dead, let the other sockets know
                    socket.disconnect()

        def read_from_ws():
            while True:
                message = websocket.receive()

                if message is None:
                    break
                else:
                    if message is not None:
                        socket.put_server_msg(message)

        socket.spawn(send_into_ws)
        socket.spawn(read_from_ws)


class FlashSocketTransport(WebsocketTransport):
    pass
