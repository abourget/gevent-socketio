MSG_FRAME = "~m~"
HEARTBEAT_FRAME = "~h~"
JSON_FRAME = "~j~"

class SocketIOProtocol(object):
    def __init__(self, handler):
        self.handler = handler

    def send(self, message, skip_queue=True):
        if skip_queue:
            self.handler._send(self._encode(message))
        else:
            pass

    def wait(self):
        return self._decode(self.handler._wait())

    def _encode(self, message):
        return MSG_FRAME + str(len(message)) + MSG_FRAME + message

    def _decode(self, data):
        messages = []
        #data.encode('utf-8')
        if data:
            while len(data) != 0:
                if data[0:3] == MSG_FRAME:
                    null, size, data = data.split(MSG_FRAME, 2)
                    size = int(size)

                    frame_type = data[0:3]
                    if frame_type == JSON_FRAME:
                        pass # Do some json parsing of data[3:size]
                    elif frame_type == HEARTBEAT_FRAME:
                        pass # let the caller process the message?
                    else:
                        messages.append(data[0:size])

                    data = data[size:]
                else:
                    raise Exception("Unsupported frame type")

            return messages
        else:
            return messages
