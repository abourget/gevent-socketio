import redis
from json import loads
from json import dumps

from socketio.namespace import BaseNamespace
from socketio import socketio_manage


def index(request):
    """ Base view to load our template """
    return {}


class ChatNamespace(BaseNamespace):
    def listener(self):
        r = redis.StrictRedis()
        r = r.pubsub()

        r.subscribe('chat')

        for m in r.listen():
            if m['type'] == 'message':
                data = loads(m['data'])
                self.emit("chat", data)

    def on_subscribe(self, *args, **kwargs):
        self.spawn(self.listener)

    def on_chat(self, msg):
        r = redis.Redis()
        r.publish('chat', dumps(msg))


def socketio_service(request):
    retval = socketio_manage(request.environ,
        {
            '': ChatNamespace,
        }, request=request
    )

    return retval
