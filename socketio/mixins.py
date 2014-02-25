"""
These are general-purpose Mixins -- for use with Namespaces -- that are
generally useful for most simple projects, e.g. Rooms, Broadcast.

You'll likely want to create your own Mixins.
"""
                
class RoomsMixin(object):
    def initialize(self):
        self.socket.manager.add_endpoint_listener(self.ns_name, 'room_emit', self.room_listener)
        
    def join(self, room):
        """Lets a user join a room on a specific Namespace."""
        rooms = self.session.get('rooms', None)
        if rooms is None:
            rooms = set()# a set of simple strings
        rooms.add(self.make_room_name(room))
        self.session['rooms'] = rooms #@todo for now distributed sessions don't detect complex changes
        
    def leave(self, room):
        """Lets a user leave a room on a specific Namespace."""
        rooms = self.session.get('rooms')
        if rooms:
            rooms.remove(self.make_room_name(room))
            self.session['rooms'] = rooms #@todo for now distributed sessions don't detect complex changes

    def make_room_name(self, room):
        return self.ns_name + '_' + room

    def emit_to_room(self, ns, room, event, *args):
        """This is sent to all in the room (in this particular Namespace)"""
        self.socket.manager.notify_endpoint(self.ns_name, 'room_emit', self.socket.sessid, room, event, *args)     
        
    def room_listener(self, _manager, _endpoint, _event, sender_sessid, room, room_event, *args):
        #@todo This is slow
        rooms = self.session.get('rooms')
        if rooms and self.socket.sessid != sender_sessid:
            room_name = self.make_room_name(room)
            if room_name in rooms:
                self.emit(room_event, *args)   

class BroadcastMixin(object):
    def initialize(self):
        self.socket.manager.add_endpoint_listener(self.ns_name, 'broadcast', self.broadcast_listener)
        
    """Mix in this class with your Namespace to have a broadcast event method.

    Use it like this:
    class MyNamespace(BaseNamespace, BroadcastMixin):
        def on_chatmsg(self, event):
            self.broadcast_event('chatmsg', event)
    """
    def broadcast_event(self, event, *args):
        """
        This is sent to all in the sockets in this particular Namespace,
        including itself.
        """
        self.socket.manager.notify_endpoint(self.ns_name, 'broadcast', self.socket.sessid, event, *args)
        
    def broadcast_event_not_me(self, event, *args):
        """
        This is sent to all the sockets in this particular Namespace,
        except itself.
        """
        self.socket.manager.notify_endpoint(self.ns_name, 'broadcast', self.socket.sessid, event, *args, not_me = True)
        
    def broadcast_listener(self, _manager, _endpoint, _event, sender_sessid, broadcast_event, *args, **kwargs):
        not_me = kwargs.get('not_me', False)
        if not (not_me and sender_sessid == self.socket.sessid):
            self.emit(broadcast_event, *args) 
