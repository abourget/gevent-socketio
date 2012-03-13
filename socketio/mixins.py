# -=- encoding: utf-8 -=-

"""You will find all sorts of Mixins in here, like implementation of Rooms, or
Broadcast systems.

You can also implement your own.. take a look, it's pretty simple.
"""

class RoomsMixin(object):
    def __init__(self, *args, **kwargs):
        super(RoomsMixin).__init__(self, *args, **kwargs)
        if not hasattr(self.socket, 'rooms'):
            self.socket.rooms = set() # a set of simple strings

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

