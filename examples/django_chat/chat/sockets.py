import logging

from socketio.namespace import BaseNamespace
from socketio.mixins import RoomsMixin, BroadcastMixin
from socketio.sdjango import namespace

@namespace('/chat')
class ChatNamespace(BaseNamespace, RoomsMixin, BroadcastMixin):
    nicknames = []

    def initialize(self):
        self.logger = logging.getLogger("socketio.chat")
        self.log("Socketio session started")
        
        
    def log(self, message):
        self.logger.info("[{0}] {1}".format(self.socket.sessid, message))
    
    def on_join(self, room):
        self.join(room)
        return True
        
    def on_nickname(self, nickname):
        self.log('Nickname: {0}'.format(nickname))
        self.session['nickname'] = nickname
        nicknames = self.session.get('nicknames', None)#WTH is 'nicknames'?!! 
        if nicknames is None:
            nicknames = set()
        nicknames.add(nickname)
        self.session['nicknames'] = nicknames
        
        self.broadcast_event('announcement', '%s has connected' % nickname)
        self.broadcast_event('nicknames', list(nicknames))
        return True, nickname

    def recv_disconnect(self):
        # Remove nickname from the list.
        self.log('Disconnected')
        nickname = self.session.get('nickname')
        if nickname:
            nicknames = self.session.get('nicknames', None)
            if nicknames:
                nicknames.remove(nickname)
            self.session['nicknames'] = nicknames
        self.broadcast_event('announcement', '%s has disconnected' % nickname)
        self.broadcast_event('nicknames', list(self.nicknames))
        self.disconnect(silent=True)
        return True

    def on_user_message(self, room, msg):
        self.log('User message: {0}'.format(msg))
        self.emit_to_room(room, 'msg_to_room', self.session['nickname'], msg)
        return True
