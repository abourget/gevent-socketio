from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin
from socketio import socketio_manage

def index(request):
    """ Base view to load our template """
    return {}

class ChatNamespace(BaseNamespace, BroadcastMixin):
    def on_chat(self, msg):
        self.broadcast_event('chat', msg)

def socketio_service(request):
    retval = socketio_manage(request.environ,
        {
            '': ChatNamespace,
        }, request=request
    )

    return retval

