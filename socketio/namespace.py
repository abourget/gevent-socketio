# -=- encoding: utf-8 -=-
import gevent
import re
import logging
import inspect

log = logging.getLogger(__name__)

# regex to check the event name contains only alpha numerical characters
allowed_event_name_regex = re.compile(r'^[A-Za-z][A-Za-z0-9_ ]*$')


class BaseNamespace(object):
    """The **Namespace** is the primary interface a developer will use
    to create a gevent-socketio-based application.

    You should create your own subclass of this class, optionally using one
    of the :mod:`socketio.mixins` provided (or your own), and define methods
    such as:

    .. code-block:: python
      :linenos:

      def on_my_event(self, my_first_arg, my_second_arg):
          print "This is a packet object", packet
          print "This is a list of the arguments", args

      def on_my_second_event(self, whatever):
          print "This holds the first arg that was passed", data

      def on_third_event(self, packet):
          print "This is the *full* packet", packet
          print "See the BaseNamespace::inspect_and_call() method"

    """

    def __init__(self, environ, ns_name, request=None):
        self.environ = environ
        self.socket = environ['socketio']
        self.request = request
        self.ns_name = ns_name
        self.allowed_methods = None  # be careful, None means all methods
                                     # are allowed while an empty list
                                     # means totally closed.
        self.ack_count = 0
        self.jobs = []

        self.reset_acl()

    def _get_next_ack(self):
        # TODO: this is currently unused, but we'll probably need it
        # to implement the ACK methods.
        self.ack_count += 1
        return self.ack_count

    def is_method_allowed(self, method_name):
        """ACL system: this checks if you have access to that method_name,
        according to the set ACLs"""
        if self.allowed_methods is None:
            return True
        else:
            return method_name in self.allowed_methods

    def add_acl_method(self, method_name):
        """ACL system: make the method_name accessible to the current socket"""

        if isinstance(self.allowed_methods, set):
            self.allowed_methods.add(method_name)
        else:
            self.allowed_methods = set([method_name])

    def del_acl_method(self, method_name):
        """ACL system: ensure the user will not have access to that method."""
        if self.allowed_methods is None:
            raise ValueError("""Trying to delete an ACL method, but none were
            defined yet! Or: No ACL restrictions yet, why would you delete
            one?""")

        self.allowed_methods.remove(method_name)

    def lift_acl_restrictions(self):
        """ACL system: This removes restrictions on the Namespace's methods, so
        that all the on_function(), event(), message() and other automatically
        dispatched methods can be accessed.
        """
        self.allowed_methods = None

    def get_initial_acl(self):
        """ACL system: If you define this function, you must return all the
        'event' names that you want your User (the established virtual Socket)
        to have access to.

        If you do not define this function, the user will have free access
        to all of the on_*() and recv_*() functions, etc.. methods.

        Return something like: ['on_connect', 'on_public_method']

        You can later modify this list dynamically (inside on_connect() for
        example) using:

        .. code-block:: python

           self.add_acl_method('on_secure_method')

        self.request is available in here, if you're already ready to do some
        auth. check.

        The ACLs are checked by the `process_packet` and/or `process_event`
        default implementations, before calling the class's methods.

        **Beware**, return None leaves the namespace completely accessible.
        """
        return None

    def reset_acl(self):
        """Resets ACL to its initial value (calling ``get_initial_acl`` and
        applying that again).
        """
        self.allowed_methods = self.get_initial_acl()

    def process_packet(self, packet):
        """If you override this, NONE of the functions in this class will
        be called.  It is responsible for dispatching to process_event() (which
        in turn calls on_*() and recv_*() methods).

        If the packet arrived here, it is because it belongs to this endpoint.

        For each packet arriving, the only possible path of execution, that is,
        the only methods that *can* be called are the following:

          recv_connect()
          recv_message()
          recv_json()
          recv_error()
          recv_disconnect()
          on_*()

        """
        if packet['type'] == 'event':
            return self.process_event(packet)
        elif packet['type'] == 'message':
            return self.call_method_with_acl('recv_message', packet, packet['data'])
        elif packet['type'] == 'json':
            return self.call_method_with_acl('recv_json', packet, packet['data'])
        elif packet['type'] == 'connect':
            return self.call_method_with_acl('recv_connect', packet)
        elif packet['type'] == 'error':
            return self.call_method_with_acl('recv_error', packet)
        else:
            print "Unprocessed packet", packet
        # TODO: manage the other packet types

    def process_event(self, packet):
        """This function dispatches ``event`` messages to the correct functions.
        Override this function if you want to not dispatch messages
        automatically to "on_event_name" methods.

        If you override this function, none of the on_functions will get called
        by default.

        [MOVE TO DOCUMENTATION' around: recv_message, recv_json and
         process_event]
        To process events that have callbacks on the client side, you must
        define your event with a single parameter: ``packet``.  In this case,
        it will be the full ``packet`` object and you can inspect its ``ack``
        and ``id`` keys to define if and how you reply.  A correct reply to an
        event with a callback would look like this:

        def on_my_callback(self, packet):
            if 'ack' in packet':
                self.emit('go_back', 'param1', id=packet['id'])

        """
        args = pkt['args']
        name = pkt['name']
        if not allowed_event_name_regex.match(name):
            self.error("unallowed_event_name",
                       "name must only contains alpha numerical characters")
            return

        method_name = 'on_' + name.replace(' ', '_')
        # This means the args, passed as a list, will be expanded to
        # the method arg and if you passed a dict, it will be a dict
        # as the first parameter.

        return self.call_method(method_name, packet, *args)

    def call_method_with_acl(self, method_name, packet, *args):
        """You should always use this function to call the methods,
        as it checks if the user is allowed according to the ACLs.
      
        If you override process_packet() or process_event(), you should
        definitely want to use this instead of getattr(self, 'my_method')()
        """
        if not self.is_method_allowed(method_name):
            self.error('method_access_denied',
                       'You do not have access to method "%s"' % method_name)
            return
        
        return self.inspect_and_call(method_name, packet, *args)

    def call_method(self, method_name, packet, *args):
        """This function is used to implement the two behaviors on dispatched
        on_*() and recv_*() method calls.

        The first behavior is:

          If there is only one parameter on the dispatched method and it is
          equal to ``packet``, then pass in the packet as the sole parameter.

        The second is:

          Pass in the arguments as specified by the different ``recv_*()``
          methods args specs, or the ``process_event()`` documentation.

        """
        method = getattr(self, method_name, None)
        if method is None:
            self.error('no_such_method',
                       'The method "%s" was not found' % method_name)
            return

        specs = inspect.getargspec(method)
        func_args = specs.args
        if not len(func_args) or func_args[0] != 'self':
            self.error("invalid_method_args", "The server-side method is invalid, as it doesn't have 'self' as its first argument")
            return
        if len(func_args) == 2 and func_args[1] == 'packet':
            return method(packet)
        else:
            return method(*args)

    def initialize(self, packet):
        """This is fired on the initial creation of a namespace so you may
        handle any setup required for it.
       
        You are also passed the packet that triggered that initialization.
        
        BEWARE, this method is NOT protected by ACLs, so you might want to
        wait for the ``connect`` packet to arrive, or to define your own 
        event. 

        If you override this method, you would probably only initialize the
        variables you're going to use in the rest of the methods with default
        values, but not perform any operation that assumes
        authentication/authorization.
        """
        pass


    def recv_message(self, data):
        """This is more of a backwards compatibility hack. This will be
        called for messages sent with the original send() call on the client
        side. This is NOT the 'message' event, which you will catch with
        'on_message()'. The data arriving here is a simple string, with no
        other info.

        If you want to handle those messages, you should override this method.
        """
        return data

    def recv_json(self, data):
        """This is more of a backwards compatibility hack. This will be
        called for JSON packets sent with the original json() call on the
        JavaScript side. This is NOT the 'json' event, which you will catch
        with 'on_json()'. The data arriving here is a python dict, with no
        event name.

        If you want to handle those messages, you should override this method.
        """
        return data

    def recv_disconnect(self):
        """Override this function if you want to do something when you get a
        *force disconnect* packet.

        By default, this function calls the ``disconnect()`` clean-up function.
        You probably want to call it yourself also, and put your clean-up
        routines in ``disconnect()`` rather than here, because that function
        gets called automatically upon disconnection.  This function is a
        pre-handle for when you get the `disconnect packet`.
        """
        self.disconnect()

    def recv_connect(self):
        """The first time a client connection is open on a Namespace, this gets
        called, and allows you to do boilerplate stuff for the namespace, like
        connecting to rooms, broadcasting events to others, doing authorization
        work, tweaking the ACLs to open up the rest of the namespace (if it
        was closed at the beginning by having get_initial_acl() return only
        ['recv_connect'])

        Also see the different mixins (RoomsMixin, BroadcastMixin).
        """
        pass

    def recv_error(self, packet):
        """Override this function to handle the errors we get from the client.

        You get the full packet in here, since it is not clear what you should
        get otherwise [TODO: change this sentence, this doesn't help :P]
        """
        pass

    def error(self, error_name, error_message, msg_id=None, quiet=False):
        """Use this to use the configured ``error_handler`` yield an
        error message to your application.

        ``error_name`` is a short string, to associate messages to recovery
                       methods
        ``error_message`` is some human-readable text, describing the error
        ``msg_id`` is used to associate with a request
        ``quiet`` specific to error_handlers. The default doesn't send a
                  message to the user, but shows a debug message on the
                  developer console.
        """
        self.socket.error(error_name, error_message, endpoint=self.ns_name,
                          msg_id=msg_id, quiet=quiet)

    def send(self, message, json=False):
        """Use send to send a simple string message.

        If ``json`` is True, the message will be encoded as a JSON object
        on the wire, and decoded on the other side.

        This is mostly for backwards compatibility.  emit() is more fun.
        """
        pkt = dict(type="message", data=message, endpoint=self.ns_name)
        if json:
            pkt['type'] = "json"
        self.socket.send_packet(pkt)

    def emit(self, event, *args, **kwargs):
        """Use this to send a structured event, with a name and arguments, to
        the client.

        By default, it uses this namespace's endpoint. You can send messages on
        other endpoints with ``self.socket['/other_endpoint'].emit()``. Beware
        that the other endpoint might not be initialized yet (if no message has
        been received on that Namespace, or if the Namespace's connect() call
        failed).
        ``callback`` - pass in the callback keyword argument to define a
                       call-back that will be called when the client acks
                       (To be implemented)
        """
        callback = kwargs.pop('callback', None)

        if kwargs:
            raise ValueError("emit() only supports positional argument, to stay compatible with the Socket.IO protocol. You can however pass in a dictionary as the first argument")
        pkt = dict(type="event", name=event, args=args,
                   endpoint=self.ns_name)

        # TODO: implement the callback stuff ??

        self.socket.send_packet(pkt)

    def spawn(self, fn, *args, **kwargs):
        """Spawn a new process, attached to this Namespace.

        It will be monitored by the "watcher" process in the Socket. If the
        socket disconnects, all these greenlets are going to be killed, after
        calling BaseNamespace.disconnect()
        """
        # self.log.debug("Spawning sub-Namespace Greenlet: %s" % fn.__name__)
        new = gevent.spawn(fn, *args, **kwargs)
        self.jobs.append(new)
        return new

    def kill_local_jobs(self):
        """Kills all the jobs spawned with BaseNamespace.spawn() on a namespace
        object.

        This will be called automatically if the ``watcher`` process detects
        that the Socket was closed.
        """
        gevent.killall(self.jobs)
        self.jobs = []
