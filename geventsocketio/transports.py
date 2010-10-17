import gevent


class XHRPollingTransport(object):
    def __init__(self, handler):
        self.handler = handler

    def handle_get_response(self):
        self.handler.start_response("200 OK", [("Access-Control-Allow-Origin", "*"),])

        print "wrote header"

        gevent.sleep(5)
        self.handler.write_more_headers([
            ("Connection", "close"),
            ("Content-Type", "text/plain; charset=UTF-8"),
            ("Content-Length", '0'),
        ])
        self.handler.write("\r\n")
        self.handler.close_connection = True

    def handle_post_response(self):
        #data = self.handler.wsgi_input.readline()
        print "POST data", data
        #self.handler.socketio_connection = False
        self.handler.start_response("200 OK", [("Access-Control-Allow-Origin", "*"),])

        print "wrote header"

        self.handler.write_more_headers([
            ("Connection", "close"),
            ("Content-Type", "text/plain; charset=UTF-8"),
            ("Content-Length", '2'),
        ])
        self.handler.write("\r\nok\r\n")
