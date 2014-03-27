#!/usr/bin/env python
#coding:utf-8

from gevent import monkey
monkey.patch_all()

import web
from web.contrib.template import render_mako
from web.httpserver import StaticMiddleware

from socketio import server, socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import RoomsMixin, BroadcastMixin


render = render_mako(
    directories=['templates'],
    input_encoding='utf-8',
    output_encoding='utf-8',
)

urls = (
    '/', 'IndexHandler',
    '/socket.io/.*', 'SocketHandler',
)

app = web.application(urls, globals())


class ChatNamespace(BaseNamespace, RoomsMixin, BroadcastMixin):
    def on_nickname(self, nickname):
        self.request['nicknames'].append(nickname)
        self.socket.session['nickname'] = nickname
        self.broadcast_event('announcement', '%s has connected' % nickname)
        self.broadcast_event('nicknames', self.request['nicknames'])
        # Just have them join a default-named room
        self.join('main_room')

    def recv_disconnect(self):
        # Remove nickname from the list.
        nickname = self.socket.session['nickname']
        self.request['nicknames'].remove(nickname)
        self.broadcast_event('announcement', '%s has disconnected' % nickname)
        self.broadcast_event('nicknames', self.request['nicknames'])

        self.disconnect(silent=True)

    def on_user_message(self, msg):
        self.emit_to_room(
            'main_room',
            'msg_to_room',
            self.socket.session['nickname'],
            msg
        )

    def recv_message(self, message):
        print "PING!!!", message


class IndexHandler:
    def GET(self):
        return render.chat()


class SocketHandler:
    def GET(self):
        socketio_manage(web.ctx.environ, {'': ChatNamespace}, request)

request = {
    'nicknames': []
}

application = app.wsgifunc(StaticMiddleware)


if __name__ == "__main__":
    print 'Listening on port 8080 and on port 10843 (flash policy server)'
    server.SocketIOServer(
        ('localhost', 8080),
        application,
        resource="socket.io",
        policy_server=True,
        policy_listener=('0.0.0.0', 10843),
    ).serve_forever()
