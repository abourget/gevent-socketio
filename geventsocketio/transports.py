import gevent


from gevent.pywsgi import WSGIHandler
class XHRPollingTransport(WSGIHandler):
    def __init__(self, handler):
        self.handler = handler

    def handle_get_response(self):

        gevent.sleep(5)
        self.handler.start_response("200 OK", [
            ("Access-Control-Allow-Origin", "*"),
            ("Connection", "close"),
            ("Content-Type", "text/plain; charset=UTF-8"),
            ("Content-Length", 0),
        ])
        self.handler.write("")

    def handle_post_response(self):
        data = self.handler.wsgi_input.readline()
        print "POST data", data
        self.handler.start_response("200 OK", [
            ("Access-Control-Allow-Origin", "*"),
            ("Connection", "close"),
            ("Content-Type", "text/plain; charset=UTF-8"),
            ("Content-Length", 2),
        ])
        self.handler.write("ok")
