__version__ = (0, 2, 4)
__all__ = ['SocketIOServer']

from socketio.server import SocketIOServer

import logging
import gevent

log = logging.getLogger(__name__)

def socketio_manage(environ, namespaces, request=None):
    """Main SocketIO management function, call from within your Framework of
    choice's view.

    The ``environ`` variable is the WSGI ``environ``.  It is used to extract the
    Socket object from the underlying server (as the 'socketio' key), and is
    otherwise attached to both the Socket and Namespace objects.

    The ``request`` object is not required, but will probably be useful to pass
    framework-specific things into your Socket and Namespace functions. It will
    simply be attached to the Socket and Namespace object (accessible through
    ``self.request`` in both cases), and it is not accessed in any case by the
    ``gevent-socketio`` library.

    The ``namespaces`` parameter is a dictionary of the namespace string
    representation as key, and the BaseNamespace namespace class descendant as
    a value.  The empty string ('') namespace is the global namespace.  You can
    use Socket.GLOBAL_NS to be more explicit. So it would look like:

      namespaces={'': GlobalNamespace,
                  '/chat': ChatNamespace}

    This function will block the current "view" or "controller" in your
    framework to do the recv/send on the socket, and dispatch incoming messages
    to your namespaces.

    This is a simple example using Pyramid:

      def my_view(request):
          socketio_manage(request.environ, {'': GlobalNamespace}, request)

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
