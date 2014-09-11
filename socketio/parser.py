# coding=utf-8
"""
Parser for socket io
"""
import json
import logging
from pyee import EventEmitter
from socketio.binary import Binary

logger = logging.getLogger(__name__)

# Protocol version
protocol = 4

# Packet type
types = {
    'CONNECT': 0,
    'DISCONNECT': 1,
    'EVENT': 2,
    'ACK': 3,
    'ERROR': 4,
    'BINARY_EVENT': 5,
    'BINARY_ACK': 6,
}

types_list = [
    'CONNECT',
    'DISCONNECT',
    'EVENT',
    'ACK',
    'ERROR',
    'BINARY_EVENT',
    'BINARY_ACK'
]

error_packet = {
    'type': types['ERROR'],
    'data': 'parser error'
}

class Encoder(object):

    @staticmethod
    def encode(obj):
        logger.debug('encoding packet %s' % json.dumps(obj))

        if types['BINARY_EVENT'] == obj['type'] or types['BINARY_ACK'] == obj['type']:
            return Encoder.encode_as_binary(obj)
        else:
            return Encoder.encode_as_string(obj)

    @staticmethod
    def encode_as_string(obj):
        str = ''
        nsp = False

        _type = obj['type']
        # first is type
        str += _type

        # attachments if we have them
        if _type == types['BINARY_EVENT'] or _type == types['BINARY_ACK']:
            str += obj['attachments']
            str += '-'

        # if we have a namespace other than '/'
        # we append it followed by a comma ','
        if 'nsp' in obj and '/' != obj['nsp']:
            nsp = True
            str += obj['nsp']

        # immediately followed by the id
        if 'id' in obj:
            if nsp:
                str += ','
                nsp = False

            str += obj['id']

        # json data
        if 'data' in obj:
            if nsp:
                str += ','
            str += json.dumps(obj['data'])

        logger.debug('encoded object as %s' % str)
        return str

    @staticmethod
    def encode_as_binary(obj):
        """
        Encode packet as buffer
        :param obj:
        :return:
        """

        blobless_data = Binary.remove_blobs(obj)
        deconstrcution = Binary.deconstruct_packet(blobless_data)
        pack = Encoder.encode_as_string(deconstrcution['packet'])
        buffers = [pack] + deconstrcution['buffers']
        return buffers


class Decoder(EventEmitter):

    def __init__(self):
        super(Decoder, self).__init__()
        self.reconstructor = None

    def add(self, obj):
        if type(obj) is str:
            packet = Decoder.decode_string(obj)

            if types['BINARY_EVENT'] == packet['type'] or types['BINARY_ACK'] == packet['type']:
                self.reconstructor = BinaryReconstructor(packet)

                if self.reconstructor.recon_pack['attachments'] == 0:
                    self.emit('decoded', packet)
            else:
                self.emit('decoded', packet)

        elif type(obj) is bytearray or 'base64' in obj:
            if self.reconstructor is None:
                raise ValueError('got binary data when not recontructing a packet')

            packet = self.reconstructor.take_binary_data(obj)

            if packet is not None:
                self.reconstructor = None
                self.emit('decoded', packet)

        else:
            raise ValueError('Unknown type: ' + obj)


    @staticmethod
    def decode_string(string):
        p = {}
        i = 0

        # look up type
        _type = int(string[0])
        p['type'] = _type

        if _type < 0 or _type >= len(types_list):
            return error_packet

        if types['BINARY_EVENT'] == _type or types['BINARY_ACK'] == _type:
            attachment = ''

            i += 1
            while string[i] != '-':
                attachment += string[i]
                i += 1

            p['attachments'] = int(attachment)

        # look up namespace
        if '/' == string[i+1]:
            namespace = ''

            i += 1
            while i:
                c = string[i]

                if ',' == c:
                    break

                namespace += c
                i += 1

                if i + 1 == len(string):
                    break

            p['nsp'] = namespace

        else:
            p['nsp'] = '/'

        # look up id
        n = string[i+1]

        if n != '' and n.isdigit():
            _id = ''

            i += 1
            while i < len(string):
                c = string[i]

                if not c.isdigit():
                    i -= 1
                    break

                _id += c

            p['id'] = _id

        # look up json data
        i += 1
        if i < len(string):
            try:
                p['data'] = json.loads(string[i:])
            except ValueError:
                return error_packet

        logger.debug('decoded %s', string)
        return p

    def destroy(self):
        if self.reconstructor:
            self.reconstructor.finish_reconstruction()


class BinaryReconstructor(object):
    def __init__(self, packet):
        self.recon_pack = packet
        self.buffers = []

    def take_binary_data(self, data):
        self.buffers.append(data)

        if len(self.buffers) == self.recon_pack['attachments']:
            packet = Binary.reconstruct_packet(self.recon_pack, self.buffers)
            self.finish_reconstruction()

            return packet

        return None

    def finish_recontruction(self):
        self.recon_pack = None
        self.buffers = []
