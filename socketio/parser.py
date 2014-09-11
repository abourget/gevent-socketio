# coding=utf-8
"""
Parser for socket io
"""
import json
import logging

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
