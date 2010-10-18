from geventsocketio.server import SocketIOServer
from geventsocketio.handler import SocketIOHandler

def app(environ, start_response):
    socketio = environ['socketio']
    if environ['PATH_INFO'].startswith("/normal"):
        start_response("200 OK", [("Content-Type", "text/plain")])
        return ["it works"]
    if environ['PATH_INFO'].startswith("/test"):
        # echo test
        test = socketio.wait()
        socketio.send(test)
    else:
        start_response("500 Server Error", [("Content-Type", "text/plain")])
        return ["root"]



server = SocketIOServer(('', 8080), app, handler_class=SocketIOHandler, resource="test")
server.serve_forever()

