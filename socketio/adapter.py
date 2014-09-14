# coding=utf-8
"""
The fork of socketio-adapter, which keeps track of all the sockets and able to broadcast packets
"""
from pyee import EventEmitter
from socketio import parser


class Adapter(EventEmitter):
    def __init__(self, namespace):
        super(Adapter, self).__init__()

        self.namespace = namespace
        self.rooms = {}
        self.sids = {}
        self.encoder = parser.Encoder

    def add(self, id, room, callback=None):
        self.sids[id] = self.sids.get(id, {})
        self.sids[id][room] = True
        self.rooms[room] = self.rooms.get(room, {})
        self.rooms[room][id] = True

        if callback:
            # CHECK WHETER gevent.sleep(0) needed
            callback()

    def remove(self, id, room, callback=None):
        self.sids[id] = self.sids.get(id, {})
        self.rooms[room] = self.rooms.get(room, {})
        del self.sids[id][room]
        del self.rooms[room][id]

        if not self.rooms[room]:
            del self.rooms[room]

        if callback:
            callback()

    def remove_all(self, id):
        rooms = self.sids.get(id, None)
        if rooms:
            for room, flag in rooms.items():
                if room in rooms:
                    del rooms[room]

                if not self.rooms[room]:
                    del self.rooms[room]

        if id in self.sids:
            del self.sids[id]

    def broadcast(self, packet, options):
        rooms = options.get('rooms', None)
        exceptions = options.get('except', None)
        flags = options.get('flags', None)
        ids = set()

        packet['nsp'] = self.namespace.name
        encoded = parser.Encoder.encode(packet)

        if rooms:
            for room in rooms:
                if room not in self.rooms:
                    continue
                for id in self.rooms[room].keys():
                    if id in ids or id in exceptions:
                        continue
                    socket = self.namespace.connected[id]
                    if socket:
                        socket.packet(encoded, pre_encoded=True)
                        ids.add(socket.id)
        else:
            for id in self.sids.keys():
                if id in exceptions:
                    continue
                socket = self.namespace.connected[id]
                if socket:
                    socket.packet(encoded, pre_encoded=True)
