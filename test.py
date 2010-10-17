from geventsocketio.server import SocketIOServer
from geventsocketio.handler import SocketIOHandler

def app(environ, start_response):
    socketio = environ['socketio']
    if environ['PATH_INFO'] == "/test/websocket":
        socketio.send("hai")
        #print socketio.wait()
        start_response("200 OK", [("Content-Type", "text/plain")])
        return ["hoi"]
    if environ['PATH_INFO'].startswith("/test/xhr-polling/"):
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [""]
    else:
        start_response("500 Server Error", [("Content-Type", "text/plain")])
        return ["root"]



server = SocketIOServer(('', 8080), app, handler_class=SocketIOHandler)
server.serve_forever()

