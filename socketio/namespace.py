# -=- encoding: utf-8 -=-
import gevent


class BaseNamespace(object):
    def __init__(self, environ, ns_name, request=None):
        self.environ = environ
        self.request = request
        self.ns_name = ns_name
        self.acl_methods = None # be careful, None means OPEN, while an empty
                                # list means totally closed.
        self.socket = socket
        self.ack_count = 0
        self.jobs = []

    def _get_next_ack(self):
        self.ack_count += 1
        return self.ack_count
        
    @property
    def socket(self):
        return self.environ['socketio']

    def is_method_allowed(self, acl):
        if self.acl_events is None:
            return True
        else:
            return acl in self.acl_events

    def add_acl_method(self, method_name):
        """ Make the method_name accessible to the current socket """

        if isinstance(self.acl_events, set):
            self.acl_events.add(method_name)
        else:
            self.acl_events = set([method_name])

    def del_acl_method(self, method_name):
        """ Ensure the user will not have access to that method. """
        if self.acl_events is None:
            raise ValueError("""Trying to delete an ACL method, but none were 
            defined yet! Or: No ACL restrictions yet, why would you delete
            one?""")

        self.acl_events.remove(method_name)

    def lift_acl_restrictions(self):
        """This removes restrictions on the Namespace's methods, so that
        all the on_function(), event(), message() and other automatically
        dispatched methods can be accessed.
        """
        self.acl_events = None

    def get_initial_acl(self):
        """If you define this function, you must return all the 'event' names
        that you want your User (the established virtual Socket) to have access
        to.

        If you do not define this function, the user will have free access
        to all of the on_function(), json(), message(), etc.. methods.

        Return something like: ['on_connect', 'on_public_method']

        You can later modify this list dynamically (inside on_connect() for
        example) using:

           self.add_acl_method('on_secure_method')

        self.request is available in here, if you're already ready to do some
        auth. check.

        The ACLs are checked by the `receive_packet` and/or `event` default impl.
        before calling the class's methods. In ACL checks fail, it then returns
        [TODO: INSERT THE CORRECT ANSWER TO THIS QUESTION HERE]
        """
        return None


    def process_packet(self, packet):
        """If you override this, NONE of the functions in this class will
        be called.  It is responsible for dispatching to event() (which in turn
        calls on_evname() functions), connect, disconnect, etc..

        If the packet arrived here, it is because it belongs to this endpoint.
        """
        # TODO: take the packet, and dispatch it, execute connect(), message(),
        #       json(), event(), and this event will call the on_functions().
        pass

    def event(self, packet):
        """This function dispatches ``event`` messages to the correct functions.

        Override this function if you want to not dispatch messages 
        automatically to "on_event_name" methods.

        If you override this function, none of the on_functions will get called
        by default.
        """
        data = packet.data
        name = packat.name

        # TODO: call the on_ and respect the ACLs


    def spawn(self, fn, *args, **kwargs):
        """Spawn a new process in the context of this request.

        It will be monitored by the "watcher" method
        """

        self.debug("Spawning greenlet: %s" % callable.__name__)
        new = gevent.spawn(fn, *args, **kwargs)
        self.jobs.append(new)

        return new

    def kill(self, recursive=True):
        """Kill the current context, call the `on_disconnect` callbacks.

        To pass control to the parent context, you must pass recursive=False
        *and* return the value returned by this call to kill().

        If recursive is True, then all parent contexts will also be killed,
        calling in the process all the `on_disconnect` callbacks defined by
        each contexts.  This is what happens automatically when the SocketIO
        socket gets disconnected for any reasons.

        """
        self.request = None

        if hasattr(self, 'disconnect'):
            getattr(self, 'disconnect')()

        self.socket.kill()

    def watcher(self, request):
        """Watch if any of the greenlets for a request have died. If so, kill the
        request and the socket.
        """
        # TODO: add that if any of the request.jobs die, kill them all and exit

        gevent.sleep(5.0)

        while True:
            gevent.sleep(1.0)

            if not self.socket.connected:
                gevent.killall(self.jobs)

