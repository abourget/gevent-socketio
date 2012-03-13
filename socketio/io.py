# -=- encoding: utf-8 -=-

import logging
import gevent

log = logging.getLogger(__name__)


class SocketIOError(Exception):
    # TODO: deprecate ?
    pass


class SocketIOKeyAssertError(SocketIOError):
    # TODO: deprecate ?
    pass


def require_connection(fn):
    # TODO: hey, will we need that somewhere ?  that'd be safer, huh ?
    def wrapped(ctx, *args, **kwargs):
        io = ctx.io

        if not io.session.connected:
            ctx.kill()
            ctx.debug("not connected on %s: exiting greenlet", fn.__name__)
            raise gevent.GreenletExit()

        return fn(ctx, *args, **kwargs)

    return wrapped


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
    socket._spawn_reader_loop()

    return "done"
