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

MSG_VALUES = dict((v,k) for k, v in MSG_TYPES.iteritems())

ERROR_REASONS = {
    'transport not supported': 0,
    'client not handshaken': 1,
    'unauthorized': 2
    }

ERROR_ADVICES = {
    'reconnect': 0,
    }

socketio_packet_attributes = ['type', 'name', 'data', 'endpoint', 'args', 
                              'ackId', 'reason', 'advice', 'qs', 'id']


def encode(data):
    """
    Encode an attribute dict into a byte string.
    """
    
    ack_with_data = True
    payload = ''
#    import pdb; pdb.set_trace()
    type = str(MSG_TYPES[data['type']])
    msg = '' + type
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
            if ack_with_data:
                msg += '+:'
        else:
            msg += '::'
        if payload != '':
            msg += data['endpoint'] + ':' + payload
        else:
            msg += data['endpoint']

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

def decode(raw_data):
    """
    Decode a rawstr packet arriving from the socket 
    into a dict.
    """
    decoded_msg = {}
    split_data = raw_data.split(":", 3)

    msg_type = split_data[0]
    msg_id = split_data[1]
    endpoint = split_data[2]

    data = None

    if len(split_data) > 3:
        data = split_data[3]

    decoded_msg['type'] = MSG_VALUES[int(msg_type)]
    decoded_msg['endpoint'] = None

    if msg_type == "0": # disconnect
        decoded_msg['endpoint'] = endpoint

    elif msg_type == "1": # connect
        decoded_msg['endpoint'] = endpoint
        decoded_msg['qs'] = endpoint

    elif msg_type == "2": # heartbeat
        pass

    elif msg_type == "3": # message
        decoded_msg['data'] = data

    elif msg_type == "4": # json msg
        decoded_msg['data'] = json.loads(data)

    elif msg_type == "5": # event
        #print "EVENT with data", data
        try:
            decoded_msg.update(json.loads(data))
            decoded_msg['endpoint'] = endpoint
        except ValueError, e:
            print("Invalid JSON message", data)

        if "+" in msg_id:
            decoded_msg['id'] = msg_id
        else:
            pass # TODO send auto ack

    elif msg_type == "6": # ack
        # TODO: look-out here..
        tail = data.split('+')[1]
        decoded_msg['ackId'] = tail

    elif msg_type == "7": # error
        els = data.split('+', 1)
        decoded_msg['reason'] = els[0]
        if len(els) == 2:
            decoded_msg['advice'] = els[1]

    elif msg_type == "8": # noop
        return None
    else:
        raise Exception("Unknown message type: %s" % msg_type)

    return decoded_msg
