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


class SocketIOContext(object):
    def __init__(self, request, in_type="type", out_type="type", debug=False,
                 json_dumps=None, json_loads=None):
        """Called when you create a new context, either by hand or from a
           nested context.

        Arguments:
        * ``request`` - the pyramid request
        * ``in_type`` - the dict. key for message names of incoming messages
        * ``out_type`` - the dict. key for message names, in outgoing message
        * ``debug`` - whether to disable debug logging...
        * ``json_dumps`` - the function to use instead of `json.dumps`
        * ``json_loads`` - the function to use instead of `json.loads`

        On the object you subclass from this one, you should define methods
        using the "msg_message_type" naming convention, where 'message_type'
        is the value for the 'type' key (or whatever was in `in_type`).  This
        is the function that will be called when a message is received to be
        dispatched.
        """
        self.request = request
        self.io = request.environ['socketio']
        if json_dumps:
            self.io.dumps = json_dumps
        if json_loads:
            self.io.loads = json_loads
        self._parent = None
        self._in_type = in_type
        self._out_type = out_type
        self._on_disconnect = []
        self.id = self.io.session.session_id

        if not hasattr(request, 'jobs'):
            request.jobs = []

        # Override self.debug if in production mode
        if not debug:
            self.debug = lambda x: None

    def debug(self, msg):
        print "%s: %s" % (self.id, msg)

    def on_disconnect(self, callback, *args, **kwargs):
        """Append to list of callbacks when the socket is closed, to do some
        clean-up."""
        self._on_disconnect.append((callback, args, kwargs))

    def error(self, code, msg):
        """Used to quickly generate an error message"""
        self.debug("error: %s, %s" % (code, msg))
        self.send({self._out_type: "error", 'error': code, 'msg': msg})

    def msg(self, msg_type, dictobj=None, **kwargs):
        """Send a message of type `msg_type`.  Add keyword arguments for the
        rest of the message.

        If you pass on only the message type and an object, it is
        assumed to be a dictionary to be merged after the message_type,
        and before the keyword assignments.
        """
        self.debug("message: %s, %s" % (msg_type, kwargs))
        out = {self._out_type: msg_type}
        if isinstance(dictobj, dict):
            out.update(dictobj)
        out.update(kwargs)
        self.send(out)

    @require_connection
    def send(self, msg):
        """ Sends a message to the socket """
        self.io.send(msg)

    @require_connection
    def send_event(self, name, msg):
        """ Sends a custom event to the socket """
        self.io.send_event(name, msg)

    @require_connection
    def broadcast(self, msg):
        """ Broadcasts a message to all clients but this one """
        self.io.broadcast(msg)

    @require_connection
    def broadcast_event(self, name, msg):
        """ Broadcasts a custom event to all clients but this one """
        self.io.broadcast_event(name, msg)

    def assert_keys(self, msg, elements):
        """Make sure the elements are inside the message, otherwise send an
        error message and skip the message.
        """
        in_type = self._in_type
        if isinstance(elements, (str, unicode)):
            elements = (elements,)
        for el in elements:
            if el not in msg:
                self.error("bad_request", "Msg type '%s' should include all those keys: %s" % (msg[in_type], elements))
                raise SocketIOKeyAssertError()

    def __call__(self, msg):
        """Parse the message upon reception and dispatch it to the good method.
        """
        in_type = self._in_type
        msg_type = msg[in_type]

        argval = None

        if msg_type == "event":
            msg_type += "_%s" % msg['name']

            if 'args' in msg:
                argval = msg['args']
        else:
            if 'data' in msg:
                argval = msg['data']

        if not hasattr(self, msg_type) or \
                not callable(getattr(self, msg_type)):
            self.error("unknown_command", "Command unknown: %s" % msg[in_type])
            return
        try:
            self.debug("Calling msg type: %s with obj: %s" % (msg_type, msg))
            return getattr(self, msg_type)(argval)
        except SocketIOKeyAssertError, e:
            return None


def socketio_receive(context):
    """Manage messages arriving from Socket.IO, dispatch to context handler"""

    io = context.io
    in_type = context._in_type

    while True:
        message = io.receive()

        if message:
            # Skip invalid messages
            if not isinstance(message, dict):
                context.error("bad_request",
                            "Your message needs to be JSON-formatted")
            elif in_type not in message:
                context.error("bad_request",
                            "You need a 'type' attribute in your message")
            else:
                # Call msg in context.
                newctx = context(message)

                # Switch context ?
                if newctx:
                    context = newctx

        if not io.session.connected:
            context.kill()
            return

def socketio_manage(request, namespaces):
    """Main SocketIO management function, call from within your Pyramid view.

    Pass it an instance of a SocketIOContext or a derivative that will handle
    messages for a particular context.
    """

    # Run startup if there's one
    for channel, namespace in namespaces.items():
        namespace.spawn(socketio_receive, namespace(request))

    return "done"
