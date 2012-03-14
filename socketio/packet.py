# -=- encoding: utf-8 -=-

import json

MSG_TYPES = {
    'disconnect': 0,
    'connect': 1,
    'heartbeat': 2,
    'message': 3,
    'json': 4,
    'event': 5,
    'ack': 6,
    'error': 7,
    'noop': 8,
    }

MSG_VALUES = dict((v, k) for k, v in MSG_TYPES.iteritems())

ERROR_REASONS = {
    'transport not supported': 0,
    'client not handshaken': 1,
    'unauthorized': 2
    }

REASONS_VALUES = dict((v, k) for k, v in ERROR_REASONS.iteritems())

ERROR_ADVICES = {
    'reconnect': 0,
    }

ADVICES_VALUES = dict((v, k) for k, v in ERROR_ADVICES.iteritems())

socketio_packet_attributes = ['type', 'name', 'data', 'endpoint', 'args',
                              'ackId', 'reason', 'advice', 'qs', 'id']

FRAME_SEPARATOR = u'\ufffd'

def decode_frames(data):
    """Decode socket.io encoded messages. Returns list of packets.

    `data`
        encoded messages

    """
    # Single message - nothing to decode here
    assert isinstance(data, unicode), 'frame is not unicode'

    if not data.startswith(FRAME_SEPARATOR):
        return [data]

    # Multiple messages
    idx = 0
    packets = []

    while data[idx:idx + 1] == FRAME_SEPARATOR:
        idx += 1

        # Grab message length
        len_start = idx
        idx = data.find(FRAME_SEPARATOR, idx)
        msg_len = int(data[len_start:idx])
        idx += 1

        # Grab message
        msg_data = data[idx:idx + msg_len]
        idx += msg_len

        packets.append(msg_data)

    return packets

def encode_frames(packets):
    """Encode list of packets. Expects packets in unicode

    `packets`
        List of packets to encode
    """
    # No packets - return empty string
    if not packets:
        return ''

    # Exactly one packet - don't do any frame encoding
    if len(packets) == 1:
        return packets[0].encode('utf-8')

    # Multiple packets
    frames = u''.join(u'%s%d%s%s' % (FRAME_SEPARATOR, len(p),
                                     FRAME_SEPARATOR, p)
                      for p in packets)

    return frames.encode('utf-8')


def encode(data):
    """
    Encode an attribute dict into a byte string.
    """
    ack_with_data = True
    payload = ''
    msg = str(MSG_TYPES[data['type']])

    if msg in ['0', '1']:
        # '1::' [path] [query]
        msg += '::' + data['endpoint']
        if 'qs' in data and data['qs'] != '':
            msg += ':' + data['qs']

    elif msg == '2':
        # heartbeat
        msg += '::'

    elif msg in ['3', '4', '5']:
        # '3:' [id ('+')] ':' [endpoint] ':' [data]
        # '4:' [id ('+')] ':' [endpoint] ':' [json]
        # '5:' [id ('+')] ':' [endpoint] ':' [json encoded event]
        # The message id is an incremental integer, required for ACKs.
        # If the message id is followed by a +, the ACK is not handled by
        # socket.io, but by the user instead.
        if msg == '3':
            payload = data['data']
        if msg == '4':
            payload = json.dumps(data['data'], separators=(',', ':'))
        if msg == '5':
            d = {}
            d['name'] = data['name']
            if 'args' in data and data['args'] != []:
                d['args'] = data['args']
            payload = json.dumps(d, separators=(',', ':'))
        if 'id' in data:
            msg += ':' + str(data['id'])
            if ack_with_data:
                msg += '+:'
        else:
            msg += '::'
        if 'endpoint' not in data:
            data['endpoint'] = ''
        if payload != '':
            msg += data['endpoint'] + ':' + payload
        else:
            msg += data['endpoint']

    elif msg == '6':
        # '6:::' [id] '+' [data]
        msg += ':::' + str(data['ackId'])
        if 'args' in data and data['args'] != []:
            msg += '+' + json.dumps(data['args'], separators=(',', ':'))

    elif msg == '7':
        # '7::' [endpoint] ':' [reason] '+' [advice]
        msg += ':::'
        if 'reason' in data and data['reason'] != '':
            msg += str(ERROR_REASONS[data['reason']])
        if 'advice' in data and data['advice'] != '':
            msg += '+' + str(ERROR_ADVICES[data['advice']])
        msg += data['endpoint']

    return msg


def decode(rawstr):
    """
    Decode a rawstr packet arriving from the socket into a dict.
    """
    decoded_msg = {}
    split_data = rawstr.split(":", 3)
    msg_type = split_data[0]
    msg_id = split_data[1]
    endpoint = split_data[2]

    data = ''

    if msg_id != '':
        if "+" in msg_id:
            msg_id = msg_id.split('+')[0]
            decoded_msg['id'] = int(msg_id)
            decoded_msg['ack'] = 'data'
        else:
            decoded_msg['id'] = int(msg_id)
            decoded_msg['ack'] = True

    # common to every message
    decoded_msg['type'] = MSG_VALUES[int(msg_type)]
    decoded_msg['endpoint'] = endpoint

    if len(split_data) > 3:
        data = split_data[3]

    if msg_type == "0": # disconnect
        pass

    elif msg_type == "1": # connect
        decoded_msg['qs'] = data

    elif msg_type == "2": # heartbeat
        pass

    elif msg_type == "3": # message
        decoded_msg['data'] = data

    elif msg_type == "4": # json msg
        decoded_msg['data'] = json.loads(data)

    elif msg_type == "5": # event
        try:
            data = json.loads(data)
        except ValueError, e:
            print("Invalid JSON event message", data)

        decoded_msg['name'] = data.pop('name')
        if 'args' in data:
            decoded_msg['args'] = data['args']
        else:
            decoded_msg['args'] = []

    elif msg_type == "6": # ack
        if '+' in data:
            ackId, data = data.split('+')
            decoded_msg['ackId'] = int(ackId)
            decoded_msg['args'] = json.loads(data)
        else:
            decoded_msg['ackId'] = int(data)
            decoded_msg['args'] = []

    elif msg_type == "7": # error
        if '+' in data:
            reason, advice = data.split('+')
            decoded_msg['reason'] = REASONS_VALUES[int(reason)]
            decoded_msg['advice'] = ADVICES_VALUES[int(advice)]
        else:
            decoded_msg['advice'] = ''
            if data != '':
                decoded_msg['reason'] = REASONS_VALUES[int(data)]
            else:
                decoded_msg['reason'] = ''
    elif msg_type == "8": # noop
        return None
    else:
        raise Exception("Unknown message type: %s" % msg_type)

    return decoded_msg
