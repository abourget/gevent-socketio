# -=- encoding: utf-8 -=-

import logging
import gevent

log = logging.getLogger(__name__)


class SocketIOError(Exception):
    pass


class SocketIOKeyAssertError(SocketIOError):
    pass


def require_connection(fn):
    def wrapped(ctx, *args, **kwargs):
        io = ctx.io

        if not io.session.connected:
            ctx.kill()
            ctx.debug("not connected on %s: exiting greenlet", fn.__name__)
            raise gevent.GreenletExit()

        return fn(ctx, *args, **kwargs)

    return wrapped


def socketio_receive(context):
    """Manage messages arriving from Socket.IO, dispatch to context handler"""

    while True:
        message = context.socket.receive()

        if message:
            # Skip invalid messages
            if not isinstance(message, dict):
                context.error("bad_request",
                            "Your message needs to be JSON-formatted")
            else:
                # Call msg in context.
                newctx = context(message)

                # Switch context ?
                if newctx:
                    context = newctx

        if not context.socket.connected:
            context.kill()
            return

def socketio_manage(environ, namespaces, request=None):
    """Main SocketIO management function, call from within your Pyramid view.

    Pass it an instance of a SocketIOContext or a derivative that will handle
    messages for a particular context.
    """

    # Run startup if there's one
    for channel, namespace in namespaces.items():

        obj = namespace(environ, channel, request=request)
        obj.spawn(socketio_receive, obj)

    return "done"
