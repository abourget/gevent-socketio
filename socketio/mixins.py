"""
These are general-purpose Mixins -- for use with Namespaces -- that are
generally useful for most simple projects, e.g. Rooms, Broadcast.

You'll likely want to create your own Mixins.
"""
class FilterMixin(object):
    def emit_filter(self, sessid, event, *args, **kwargs):
        """Return True if the event should be emitted or False to skip it.
        
        To implement cooperative filtering, i.e. emit only if all ``emit_filter`` calls of all mixin classes return True, the 
        extending classes should return the result of calling ``super(...).emit_filter`` if they are not filtering the event.
        
        Example:
            class Filter(FilterMixin):
                def emit_filter(self, sessid, event, *args, **kwargs):
                    if not self.check(event):
                        return False
                    return super(Filter, self).emit_filter(self, sessid, event, *args, **kwargs)
        """
        try:
            return super(FilterMixin, self).emit_filter(self, sessid, event, *args, **kwargs)
        except AttributeError:#not implemented by any super classes
            return True
    
class RoomsMixin(FilterMixin):

    def join(self, room):
        """Lets a user join a room on a specific Namespace."""
        rooms = self.session.get('rooms', None)
        if rooms is None:
            rooms = set()# a set of simple strings
        rooms.add(self._get_room_name(room))
        self.session['rooms'] = rooms #@todo for now distributed sessions don't detect complex changes
        
    def leave(self, room):
        """Lets a user leave a room on a specific Namespace."""
        rooms = self.session.get('rooms')
        if rooms:
            rooms.remove(self._get_room_name(room))
            self.session['rooms'] = rooms #@todo for now distributed sessions don't detect complex changes

    def _get_room_name(self, room):
        return self.ns_name + '_' + room

    def emit_to_room(self, room, event, *args):
        """This is sent to all in the room (in this particular Namespace)"""
        self.socket.manager.emit_to_endpoint(self.ns_name, self.socket.sessid, event, *args, room = room)
        
    def emit_filter(self, sessid, event, *args, **kwargs):
        room = kwargs.get('room', None)
        if room is not None:
            if self.socket.sessid == sessid or 'rooms' not in self.session:
                return False
            
            room_name = self._get_room_name(room)
            if room_name not in self.session['rooms']:
                return False
        
        return super(RoomsMixin, self).emit_filter(self, sessid, event, *args, **kwargs)

class BroadcastMixin(FilterMixin):
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
        self.socket.manager.emit_to_endpoint(self.ns_name, self.socket.sessid, event, *args)
        
    def broadcast_event_not_me(self, event, *args):
        """
        This is sent to all the sockets in this particular Namespace,
        except itself.
        """
        self.socket.manager.emit_to_endpoint(self.ns_name, self.socket.sessid, event, *args, not_me = True)
        
    def emit_filter(self, sessid, event, *args, **kwargs):
        not_me = kwargs.get('not_me', False)
        if not_me and sessid == self.socket.sessid:
            return False
        return super(BroadcastMixin, self).emit_filter(self, sessid, event, *args, **kwargs)
