from pyramid.view import view_config
import gevent
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import RoomsMixin, BroadcastMixin
from gevent import socket

def index(request):
    """ Base view to load our template """
    return {}



"""
ACK model:

The client sends a message of the sort:

{type: 'message',
 id: 140,
 ack: true,
 endpoint: '/tobi',
 data: ''
}

The 'ack' value is 'true', marking that we want an automatic 'ack' when it
receives the packet.  The Node.js version sends the ack itself, without any
server-side code interaction.  It dispatches the packet only after sending back
an ack, so the ack isn't really a reply.  It's just marking the server received
it, but not if the event/message/json was properly processed.

The automated reply from such a request is:

{type: 'ack',
 ackId: '140',
 endpoint: '',
 args: []
}

Where 'ackId' corresponds to the 'id' of the originating message.  Upon
reception of this 'ack' message, the client then looks in an object if there
is a callback function to call associated with this message id (140).  If so,
runs it, otherwise, drops the packet.

There is a second way to ask for an ack, sending a packet like this:

{type: 'event',
 id: 1,
 ack: 'data',
 endpoint: '',
 name: 'chat',
 args: ['', '']
}

{type: 'json',
 id: 1,
 ack: 'data',
 endpoint: '',
 data: {a: 'b'}
}

.. the same goes for a 'message' packet, which has the 'ack' equal to 'data'.
When the server receives such a packet, it dispatches the corresponding event
(either the named event specified in an 'event' type packet, or 'message' or
'json, if the type is so), and *adds* as a parameter, in addition to the
'args' passed by the event (or 'data' for 'message'/'json'), the ack() function
to call (it encloses the packet 'id' already).  Any number of arguments passed
to that 'ack()' function will be passed on to the client-side, and given as
parameter on the client-side function.

That is the returning 'ack' message, with the data ready to be passed as
arguments to the saved callback on the client side:

{type: 'ack',
 ackId: '12',
 endpoint: '',
 args: ['woot', 'wa']
}

"""


class GlobalIONamespace(BaseNamespace, BroadcastMixin):
    def on_chat(self, *args):
        self.emit("bob", {'hello': 'world'})
        print "Received chat message", args
        self.broadcast_event_not_me('chat', *args)
    
    def recv_connect(self):
        print "CONNNNNNNN"
        self.emit("you_just_connected", {'bravo': 'kid'})
        self.spawn(self.cpu_checker_process)

    def recv_json(self, data):
        self.emit("got_some_json", data)

    def on_bob(self, *args):
        self.broadcast_event('broadcasted', args)
        self.socket['/chat'].emit('bob')

    def cpu_checker_process(self):
        """This will be a greenlet"""
        ret = os.system("cat /proc/cpu/stuff")
        self.emit("cpu_value", ret)

class ChatIONamespace(BaseNamespace, RoomsMixin):
    def on_mymessage(self, msg):
        print "In on_mymessage"
        self.send("little message back")
        self.send({'blah': 'blah'}, json=True)
        for x in xrange(2):
            self.emit("pack", {'the': 'more', 'you': 'can'})

    def on_my_callback(self, packet):
        return (1, 2)

    def on_trigger_server_callback(self, superbob):
        def cb():
            print "OK, WE WERE CALLED BACK BY THE ACK! THANKS :)"
        self.emit('callmeback', 'this is a first param',
                  'this is the last param', callback=cb)

        def cb2(param1, param2):
            print "OK, GOT THOSE VALUES BACK BY CB", param1, param2
        self.emit('callmeback', 'this is a first param',
                  'this is the last param', callback=cb2)

    def on_rtc_invite(self, sdp):
        print "Got an RTC invite, now pushing to others..."
        self.emit_to_room('room1', 'rtc_invite', self.session['nickname'],
                          sdp)
        
    def recv_connect(self):
        self.session['nickname'] = 'guest123'
        self.join('room1')

    def recv_message(self, data):
        print "Received a 'message' with data:", data
        
        
    def on_disconnect_me(self, data):
        print "Disconnecting you buddy", data
        self.disconnect()


nsmap = {'': GlobalIONamespace,
         '/chat': ChatIONamespace}

@view_config(route_name='socket_io')
def socketio_service(request):
    """ The view that will launch the socketio listener """

    socketio_manage(request.environ, namespaces=nsmap, request=request)

    return {}

