# -=- encoding: utf-8 -=-

import json

MSG_TYPES = {
    'disconnect': 0,
    'connect': 1,
    'heartbeat' : 2,
    'message': 3,
    'json': 4,
    'event': 5,
    'ack': 6,
    'error': 7,
    'noop': 8,
    }

ERROR_REASONS = {
    'transport not supported': 0,
    'client not handshaken': 1,
    'unauthorized': 2
    }

ERROR_ADVICES = {
    'reconnect': 0,
    }

class Packet(object):
    # Message types
    DISCONNECT = "0"
    CONNECT = "1"
    HEARTBEAT = "2"
    MESSAGE = "3"
    JSON = "4"
    EVENT = "5"
    ACK = "6"
    ERROR = "7"
    NOOP = "8"

    socketio_packet_attributes = ['type', 'name', 'data', 'endpoint', 'args', 
                                  'ackId', 'reason', 'advice', 'qs', 'id']

    def __init__(self, type=None, name=None, data=None, endpoint=None, 
                 ack_with_data=False, qs=None, args=None,
                 reason=None, advice=None, error=None, id=None):
        """
        Models a packet

        ``type`` - One of the packet types above (MESSAGE, JSON, EVENT, etc..)
        ``name`` - The name used for events
        ``data`` - The actual data, before encoding
        ``endpoint`` - The Namespace's name to send the packet
        ``id`` - The absence of the transport id and session id segments will 
        signal the server this is a new, non-handshaken connection.
        ``ack_with_data`` - If True, return data (should be a sequence) with ack.
        ``reason`` - one of ERROR_* values
        ``advice`` - one of ADVICE_* values
        ``error``- an error message to be displayed
        """
        self.type = type
        self.name = name
        self.endpoint = endpoint
        self.ack_with_data = ack_with_data
        self.data = data
        self.qs = qs # query string
        if self.type == Packet.ACK and not msgid:
            raise ValueError("An ACK packet must have a message 'msgid'")

    @property
    def query(self):
        """Transform the query_string into a dictionary"""
        # TODO: do it
        return {}

    def _encode(self):
        """Return a dictionary with the packet parameters"""
        d = dict()
        for attr in self.socketio_packet_attributes:
            if self.__getattribute__(attr) is not None:
                d[attr] = self.__getattribute__(attr)
        return d

    def encode(self, data):
        """
        Encode an attribute dict into a byte string.
        """
        payload = ''
        type = str(MSG_TYPES[data['type']])
        msg = "" + type
        if type in ['0', '1']:
            # '1::' [path] [query]
            msg += '::' + data['endpoint']
            if 'qs' in data and data['qs'] != '':
                msg += ':' + data['qs']
        
        elif type == '2':
            # heartbeat
            msg += '::'
        
        elif type in ['3','4','5']:
            # '3:' [id ('+')] ':' [endpoint] ':' [data]
            # '4:' [id ('+')] ':' [endpoint] ':' [json]
            # '5:' [id ('+')] ':' [endpoint] ':' [json encoded event]
            # The message id is an incremental integer, required for ACKs. 
            # If the message id is followed by a +, the ACK is not handled by 
            # socket.io, but by the user instead.
            if msg == '3':
                payload = data['data']
            if msg == '4':
                payload = json.dumps(data['data'])
            if msg == '5':
                d = {}
                d['name'] = data['name']
                if data['args'] != []:
                    d['args'] = data['args'] 
                payload = json.dumps(d)
            if 'id' in data:
                msg += ':' + str(data['id'])
                if self.ack_with_data:
                    msg += '+:'
                else:
                    msg += ':'
            else:
                msg += '::'
            msg += data['endpoint'] + ':' + payload
        
        elif type == '6':
            # '6:::' [id] '+' [data]
            msg += ':::' + str(data['ackId'])
            if 'args' in data and data['args'] != []:
                msg += '+' + str(data['args'])
        
        elif type == '7':
            # '7::' [endpoint] ':' [reason] '+' [advice]
            msg += ':::'
            if 'reason' in data and data['reason'] is not '':
                msg += str(ERROR_REASONS[data['reason']])
            if 'advice' in data and data['advice'] is not '':
                msg += '+' + str(ERROR_ADVICES[data['advice']])
            msg += data['endpoint']

        return msg

    @staticmethod
    def decode(data):
        """Decode a rawstr arriving from the channel into a valid Packet object
        """
        # decode the stuff
        #data.encode('utf-8', 'ignore')
        msg_type, msg_id, tail = data.split(":", 2)

        #print "RECEIVED MSG TYPE ", msg_type, data

        if msg_type == "0": # disconnect
            self.socket.kill()
            return {'endpoint': tail, 'type': 'disconnect'}

        elif msg_type == "1": # connect
            self.send_message("1::%s" % tail)
            return {'endpoint': tail, 'type': 'connect'}

        elif msg_type == "2": # heartbeat
            self.socket.heartbeat()
            return None

        msg_endpoint, data = tail.split(":", 1)
        message = {'endpoint': msg_endpoint}

        if msg_type == "3": # message
            message['type'] = 'message'
            message['data'] = data
        elif msg_type == "4": # json msg
            message['type'] = 'json'
            message['data'] = json.loads(data)
        elif msg_type == "5": # event
            #print "EVENT with data", data
            message.update(json.loads(data))

            if "+" in msg_id:
                message['id'] = msg_id
            else:
                pass # TODO send auto ack
            message['type'] = 'event'
        elif msg_type == "6": # ack
            message['type'] = 'ack?'
        elif msg_type == "7": # error
            message['type'] = 'error'
            els = data.split('+', 1)
            message['reason'] = els[0]
            if len(els) == 2:
                message['advice'] = els[1]
        elif msg_type == "8": # noop
            return None
        else:
            raise Exception("Unknown message type: %s" % msg_type)

        return Packet(type, data, endpoint, msgid, ack)
