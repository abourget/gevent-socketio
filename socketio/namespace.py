# -=- encoding: utf-8 -=-
import gevent
import re

class BaseNamespace(object):

    _event_name_regex = re.compile(r'^[A-Za-z][A-Za-z0-9_ ]*$')
    """Used to match the event names, so they don't leak bizarre characters"""


    def __init__(self, environ, ns_name, request=None):
        self.environ = environ
        self.request = request
        self.ns_name = ns_name
        self.allowed_methods = None # be careful, None means OPEN, while an empty
                                    # list means totally closed.
        self.ack_count = 0
        self.jobs = []

    def debug(*args, **kwargs):
        print "Not implemented"
        
    @property
    def socket(self):
        return self.environ['socketio']

    def _get_next_ack(self):
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
        """ACL system: ensure the user will not have access to that method. """
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
        if packet['type'] == 'event':
            return self.process_event(packet)
        elif packet['type'] == 'message':
            return self.call_method('recv_message', packet['data'])
        elif packet['type'] == 'json':
            return self.call_method('recv_json', packet['data'])
        # TODO: manage the other packet types


    def process_event(self, pkt):
        """This function dispatches ``event`` messages to the correct functions.

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
        # This means the args, passed as a list, will be expanded to Python args
        # and if you passed a dict, it will be a dict as the first parameter.
        return self.call_method(method_name, *args)

    def call_method(self, method_name, *args, **kwargs):
        """You should always use this function to call the methods,
        as it checks if you're allowed according to the set ACLs.
       
        If you override process_packet() or process_event(), you should
        definitely want to use this instead of getattr(self, 'my_method')()
        """
        if not self.is_method_allowed(method_name):
            # TODO: implement the Error handling abstraction.
            #raise SocketIOError("method_not_found", "This method was not found")
            print "HEY! THIS METHOD IS NOT ALLOWED"
            #log.debug("hey.. ")
            return None
        
        method = getattr(self, method_name, None)
        if method is None:
            print "NO SUCH METHOD", method_name
            return
        return method(*args, **kwargs)


    def recv_message(self, msg):
        """This is more of a backwards compatibility hack.  This will be
        called for messages sent with the original send() call on the JavaScript
        side.  This is NOT the 'message' event, which you will catch with
        'on_message()'.  The data arriving here is a simple string, with no other
        info.

        If you want to use this, you should override this method.
        """
        # This message should be decoded already, according to the flags it was
        # sent with (OR NOT ???)
        pass
        
    def recv_json(self, data):
        """This is more of a backwards compatibility hack.  This will be
        called for JSON packets sent with the original json() call on the
        JavaScript side.  This is NOT the 'json' event, which you will catch with
        'on_json()'.  The data arriving here is a python dict, with no event
        name.

        If you want to use this feature, you should override this method.
        """
        pass

    def disconnect(self):
        """This would get called ONLY when the FULL socket gets disconnected,
        as part of a loop through all namespaces, calling disconnect() on the
        way.

        Override this method with clean-up instructions and processes.
        """
        pass

    def connect(self):
        """If you return False here, the Namespace will not be active for that
        Socket.  You *should* return True for anything to succeed in here.

        In this function, you can do things like authorization, making sure
        someone will have access to these methods.  Otherwise, raise
        AuthorizationError.

        You can also make this socket join a room, and later on leave it by 
        calling one of your events (on_leave_this_ns_or_something()), and
        at some point, check with 'blah' in socket.rooms

        join() and leave() would affect the content of 'rooms'
        """
        return True

    def error(self):
        """???"""
        pass


    def emit(self, event, data, broadcast=False, json=False, room=None,
             callback=None):
        pass

    def emit_json(self, *args, **kwargs):
        """This is just a shortcut to self.emit(..., json=True)"""
        kwargs['json'] = True
        self.emit(*args, **kwargs)

    def join(self, room):
        pass

    def leave(self, room):
        pass

    def spawn(self, fn, *args, **kwargs):
        """Spawn a new process, attached to this Namespace.

        It will be monitored by the "watcher" process in the Socket.  If the
        socket disconnects, all these greenlets are going to be killed, after
        calling BaseNamespace.disconnect()
        """
        self.debug("Spawning sub-Namespace Greenlet: %s" % fn.__name__)
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
                    
