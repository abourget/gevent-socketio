"""This is just a sample of the protocol we want to implement"""

GLOBAL_NS = None


class RoomsMixin(object):
    def __init__(self, *args, **kwargs):
        super(RoomsMixin).__init__(self, *args, **kwargs)
        if not hasattr(self.socket, 'rooms'):
            self.socket.rooms = set()  # a set of simple strings

    def join(self, room):
        """Lets a user join a room on a specific Namespace."""
        self.socket.rooms.add(self._get_room_name(room))

    def leave(self, room):
        """Lets a user leave a room on a specific Namespace."""
        self.socket.rooms.remove(self._get_room_name(room))

    def _get_room_name(self, room):
        return self.ns_name + '_' + room

    def emit_to_room(self, event, args, room):
        """This is sent to all in the room (in this particular Namespace)"""
        pkt = dict(type="event",
                   name=event,
                   args=args,
                   endpoint=self.ns_name)
        room_name = self._get_room_name(room)
        for sessid, socket in self.socket.server.sockets.iteritems():
            if not hasattr(socket, 'rooms'):
                continue
            if room_name in socket.rooms:
                socket.send_packet(pkt)


class ChatNamespace(BaseNamespace):
    """We're in the /chat namespace"""

    def receive_packet(self, packet):
        """If you override this, NONE of the functions in this class will
        be called.  It is responsible for dispatching to event() (which in turn
        calls on_evname() functions), connect, disconnect, etc..
        """
        pass

    def event(self, packet):
        """Override this function if you want to not dispatch messages
        automatically to "on_event_name" methods.

        If you override this function, none of the on_functions will get
        called.
        """
        data = packet.data
        name = packat.name

    def on_publish(self, data):
        """Called by client-side: chat.emit("publish", {"foo": "bar"});"""
        pass

    def on_new_message(self, data):
        #
        # blah blah..
        #
        with self.broadcast:
            with self.json:
                self.emit(blah)

        self.emit('blah', {"blah": "blah"}, broadcast=True, json=True,
                  room='justin bieber')
        self.emit_json('blah', data={"super": "bob"})

        self.join('blah')
        self.leave('blah')
        self.socket.join('blah')

        self.socket['/chat'].join('this channel')
        if '/chat' in self.socket:
            print "We're connected to '/chat'"

        self.socket[GLOBAL_NS].join('blah')
        self.socket.sessid  # Like node, for hooking back sessions to sockets.

        a = 'thisvalue'

        def callback():
            self.superbob = a
        self.emit('bob_event', {'something': 'blah'}, callback=callback)

    def recv_message(self, msg):
        """This is more of a backwards compatibility hack.  This will be
        called for messages sent with the original send() call on the
        JavaScript side.  This is NOT the 'message' event, which you will
        catch with 'on_message()'.  The data arriving here is a simple string,
        with no other info.

        If you want to use this, you should override this method.
        """
        # This message should be decoded already, according to the flags it was
        # sent with (OR NOT ???)
        pass

    def recv_json(self, data):
        """This is more of a backwards compatibility hack.  This will be
        called for JSON packets sent with the original json() call on the
        JavaScript side.  This is NOT the 'json' event, which you will catch
        with 'on_json()'.  The data arriving here is a python dict, with no
        event name.

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
        Socket.

        In this function, you can do things like authorization, making sure
        someone will have access to these methods.  Otherwise, raise
        AuthorizationError.

        You can also make this socket join a room, and later on leave it by
        calling one of your events (on_leave_this_ns_or_something()), and
        at some point, check with 'blah' in socket.rooms

        join() and leave() would affect the content of 'rooms'
        """
        pass

    def error(self):
        """???"""
        pass


class GlobalNamespace(BaseNamespace):
    def acl(self):
        """If you define this function, you must return all the 'event' names
        that you want your User (the established Socket) to have access to.

        If you do not define this function, the user will have free access
        to all of the on_function() methods.

        Return something like: ['connect', 'public_method']

        You can later modify this list dynamically (inside connect() for
        example) using:

           self.add_acl_event('secure_method')
        """
        return ['connect']

    def on_connect(self, data):
        """Do auth stuff, and other stuff"""
        if auth:
            self.add_acl_event('private_method')
            self.del_acl_event('connect')
        pass

    def on_public_method(self, data):
        """This can be accessed without authentication, on the GLOBAL_NS
        namespace"""
        pass


class BaseNamespace(object):
    def __init__(self, socket, request):
        self.request = request
        self.acl_methods = None  # Be careful: None means OPEN, while an empty
                                 # list means totally closed.
        self.socket = socket
        self.ack_count = 0

    def _get_next_ack(self):
        self.ack_count += 1
        return self.ack_count

    def is_method_allowed(self, acl):
        if self.acl_events is None:
            return True
        else:
            return acl in self.acl_events

    def add_acl_method(self, method_name):
        """Open up one of the """
        if isinstance(self.acl_events, set):
            self.acl_events.add(method_name)
        else:
            self.acl_events = set([method_name])

    def del_acl_method(self, method_name):
        """Ensure the user will not have access to that method."""
        if self.acl_events is None:
            raise ValueError(
                "Trying to delete an ACL method, but none were defined yet! "
                "Or: No ACL restrictions yet, why would you delete one ?")
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

        The ACLs are checked by the `receive_packet` and/or `event` default
        impl. before calling the class's methods. In ACL checks fail, it then
        returns.
        [TODO: INSERT THE CORRECT ANSWER TO THIS QUESTION HERE]
        """
        return None


class GlobalNamespace(BaseNamespace):
    def get_initial_acl(self):
        if self.request.user:
            return ['on_public_method', 'on_private_method']
        return ['on_connect', 'on_public_method']

    def on_connect(self, data):
        """Do auth stuff, and other stuff"""
        if auth:
            self.add_acl_event('private_method')
            self.del_acl_event('connect')
        pass

    def on_public_method(self, data):
        """This can be accessed without authentication, on the GLOBAL_NS
        namespace"""
        pass


def auth_method(handshake_packet):
    """Something"""
    handshake_packet.query
    handshake_packet.method  # POST, GET, OPTIONS
    handshake_packet.

    # do things

    return False
    return True


nmsp_map = {'/chat': ChatNamespace,
            '/home': HomeNamespace,
            GLOBAL_NS: GlobalNamespace}


def view(request):
    pyramid_socketio_manage(request.environ, namespaces=nmsp_map,
                            request=request)


### inside __init__.py for a Pyramid app, using pyramid_socketio integration
def main():

    config = Configurator()
    # These things should configure the SocketIOHandler or Protocol or whatever
    #
    # See options in:
    # https://github.com/LearnBoost/socket.io/blob/master/lib/manager.js
    #
    # Put that in the .ini file.. at the server level, import in the
    # SocketIOServer
    config.set_socketio_transports(['websocket'])
    config.set_socketio_namespace('socket.io')
    config.set_socketio_heartbeats(True, interval=5, timeout=60)
    #config.set_socketio_origins("*:*") ?
