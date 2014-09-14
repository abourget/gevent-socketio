import logging
from socketio.adapter import Adapter
from socketio.client import Client
from socketio.namespace import Namespace
from engine.server import Server as EngineServer

__all__ = ['SocketIOServer']

logger = logging.getLogger(__name__)


class SocketIOServer(EngineServer):

    def __init__(self, *args, **kwargs):
        self.namespaces = {}
        self.root_namespace = self.of('/')
        super(SocketIOServer, self).__init__(*args, **kwargs)

    def of(self, name, callback=None):
        if not name.startswith('/'):
            name = '/' + name

        if name not in self.namespaces:
            logger.debug('initializing namespace %s', name)
            namespace = Namespace(self, name)
            self.namespaces[name] = namespace

        if callback:
            self.namespaces[name].on('connect', callback)

        return self.namespaces[name]

    def close(self):
        if '/' in self.namespaces:
            for socket in self.namespaces['/'].sockets:
                socket.on_close()

        super(SocketIOServer, self).close()

    def on_connection(self, engine_socket):
        logger.debug('incoming connection with id %s', engine_socket.id)
        client = Client(self, engine_socket)
        client.connect('/')

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
    serve(app, **kw)
    return 0
