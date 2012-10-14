import sys
import traceback

from socket import error

from gevent.pywsgi import WSGIServer

from socketio.handler import SocketIOHandler
from socketio.policyserver import FlashPolicyServer
from socketio.virtsocket import Socket

__all__ = ['SocketIOServer']


class SocketIOServer(WSGIServer):
    """A WSGI Server with a resource that acts like an SocketIO."""

    def __init__(self, *args, **kwargs):
        """
        This is just like the standard WSGIServer __init__, except with a
        few additional ``kwargs``:

        :param resource: The URL which has to be identified as a socket.io request.  Defaults to the /socket.io/ URL.
        :param transports: Optional list of transports to allow. List of
            strings, each string should be one of
            handler.SocketIOHandler.handler_types.
        :param policy_server: Boolean describing whether or not to use the
            Flash policy server.  Default True.
        :param policy_listener : A tuple containing (host, port) for the
            policy server.  This is optional and used only if policy server
            is set to true.  The default value is 0.0.0.0:843
        """
        self.sockets = {}
        if 'namespace' in kwargs:
            print("DEPRECATION WARNING: use resource instead of namespace")
            self.resource = kwargs.pop('namespace', 'socket.io')
        else:
            self.resource = kwargs.pop('resource', 'socket.io')

        self.transports = kwargs.pop('transports', None)

        if kwargs.pop('policy_server', True):
            try:
                address = args[0][0]
            except TypeError:
                address = args[0].address[0]
            policylistener = kwargs.pop('policy_listener', (address, 10843))
            self.policy_server = FlashPolicyServer(policylistener)
        else:
            self.policy_server = None

        kwargs['handler_class'] = SocketIOHandler
        super(SocketIOServer, self).__init__(*args, **kwargs)

    def start_accepting(self):
        if self.policy_server is not None:
            try:
                if not self.policy_server.started:
                    self.policy_server.start()
            except error, ex:
                sys.stderr.write(
                    'FAILED to start flash policy server: %s\n' % (ex, ))
            except Exception:
                traceback.print_exc()
                sys.stderr.write('FAILED to start flash policy server.\n\n')
        super(SocketIOServer, self).start_accepting()

    def stop(self):
        if self.policy_server is not None:
            self.policy_server.stop()
        super(SocketIOServer, self).stop()

    def handle(self, socket, address):
        handler = self.handler_class(socket, address, self)
        handler.handle()

    def get_socket(self, sessid=''):
        """Return an existing or new client Socket."""

        socket = self.sockets.get(sessid)

        if socket is None:
            socket = Socket(self)
            self.sockets[socket.sessid] = socket
        else:
            socket.incr_hits()

        return socket


def serve(app, **kw):
    _quiet = kw.pop('_quiet', False)
    _resource = kw.pop('resource', 'socket.io')
    if not _quiet: # pragma: no cover
        # idempotent if logging has already been set up
        import logging
        logging.basicConfig()

    host = kw.pop('host', '127.0.0.1')
    port = int(kw.pop('port', 6543))

    transports = kw.pop('transports', None)
    if transports:
        transports = [x.strip() for x in transports.split(',')]

    policy_server = kw.pop('policy_server', False)
    if policy_server in (True, 'True', 'true', 'enable', 'yes', 'on', '1'):
        policy_server = True
        policy_listener_host = kw.pop('policy_listener_host', host)
        policy_listener_port = int(kw.pop('policy_listener_port', 10843))
        kw['policy_listener'] = (policy_listener_host, policy_listener_port)
    else:
        policy_server = False

    server = SocketIOServer((host, port),
                            app,
                            resource=_resource,
                            transports=transports,
                            policy_server=policy_server,
                            **kw)
    if not _quiet:
        print('serving on http://%s:%s' % (host, port))
    server.serve_forever()


def serve_paste(app, global_conf, **kw):
    """pserve / paster serve / waitress replacement / integration

    You can pass as parameters:

    transports = websockets, xhr-multipart, xhr-longpolling, etc...
    policy_server = True
    """
    print kw
    serve(app, **kw)
    return 0
