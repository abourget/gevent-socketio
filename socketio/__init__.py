__version__ = (0, 2, 4)
__all__ = ['SocketIOServer']

from socketio.server import SocketIOServer

import logging
import gevent

log = logging.getLogger(__name__)

def socketio_manage(environ, namespaces, request=None):
    """Main SocketIO management function, call from within your Framework of
    choice's view.

    The request object is not required, but will probably be useful to pass
    framework-specific things into your Socket and Namespace functions.
    """
    socket = environ['socketio']
    socket._set_environ(environ)
    socket._set_namespaces(namespaces)
    if request:
        socket._set_request(request)
    receiver_loop = socket._spawn_receiver_loop()
    watcher = socket._spawn_watcher()

    gevent.joinall([receiver_loop, watcher])

    # TODO: double check, what happens to the WSGI request here ? it vanishes ?

    return
