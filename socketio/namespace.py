# -=- encoding: utf-8 -=-
import gevent
import re
import logging

log = logging.getLogger(__name__)


class BaseNamespace(object):

    _event_name_regex = re.compile(r'^[A-Za-z][A-Za-z0-9_ ]*$')
    """Used to match the event names, so they don't leak bizarre characters"""

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

           self.add_acl_method('on_secure_method')

        self.request is available in here, if you're already ready to do some
        auth. check.

        The ACLs are checked by the `process_packet` and/or `process_event`
        default implementations, before calling the class's methods.
        """
        return None

    def process_packet(self, packet):
        """If you override this, NONE of the functions in this class will
        be called.  It is responsible for dispatching to event() (which in turn
        calls on_evname() functions), connect, disconnect, etc..

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
        # TODO: take the packet, and dispatch it, execute connect(), message(),
        #       json(), event(), and this event will call the on_functions().
        if packet['type'] == 'event':
            return self.process_event(packet)
        elif packet['type'] == 'message':
            return self.call_method('recv_message', packet['data'])
        elif packet['type'] == 'json':
            return self.call_method('recv_json', packet['data'])
        elif packet['type'] == 'connect':
            return self.call_method('recv_connect')
        elif packet['type'] == 'error':
            return self.call_method('recv_error', packet)
        else:
            print "Unprocessed packet", packet
        # TODO: manage the other packet types

    def process_event(self, pkt):
        """This function dispatches ``events`` to the correct callback.

        Override this function if you want to not dispatch messages
        automatically to "on_event_name" methods.

        If you override this function, none of the on_functions will get called
        by default.
        """
        args = pkt['args']
        name = pkt['name']
        if not self._event_name_regex.match(name):
            print "Message ignored, the bastard", name
            return

        method_name = 'on_' + name.replace(' ', '_')
        # This means the args, passed as a list, will be expanded to
        # the method arg and if you passed a dict, it will be a dict
        # as the first parameter.

        return self.call_method(method_name, *args)

    def call_method(self, method_name, *args):
        """You should always use this function to call the methods,
        as it checks if you're allowed according to the set ACLs.

        If you override process_packet() or process_event(), you should
        definitely want to use this instead of getattr(self, 'my_method')()
        """
        if not self.is_method_allowed(method_name):
            self.error('method_access_denied',
                       'You do not have access to method "%s"' % method_name)
            return

        method = getattr(self, method_name, None)
        if method is None:
            self.error('no_such_method',
                       'The method "%s" was not found' % method_name)
            return

        # TODO: warning, it is possible that this call doesn't work because of
        #       the *args, so let's make sure something comes up wen it fails.
        res = method(*args)
        return res

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
