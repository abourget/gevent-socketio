import redis
from json import loads
from json import dumps

from chatter4.models import DBSession
from chatter4.models import Chat

from json import loads
from json import dumps

from socketio.namespace import BaseNamespace
from socketio import socketio_manage


def index(request):
    """ Base view to load our template """
    return {}


def get_log(request):
    return [c.serialize() for c in DBSession.query(Chat).all()]


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

        # store the data in the database using sqlalchemy
        chat = Chat(chat_line=msg)
        DBSession.add(chat)
        DBSession.commit()

        # we got a new chat event from the client, send it out to
        # all the listeners
        r.publish('chat', dumps(chat.serialize()))


def socketio_service(request):
    retval = socketio_manage(request.environ,
        {
            '': ChatNamespace,
        }, request=request
    )

    return retval
