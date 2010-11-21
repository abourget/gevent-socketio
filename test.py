from geventsocketio import SocketIOServer

def app(environ, start_response):
    socketio = environ['socketio']

    if environ['PATH_INFO'].startswith("/normal"):
        start_response("200 OK", [("Content-Type", "text/plain")])
        return ["it works"]

    elif environ['PATH_INFO'].startswith("/test/"):
        while socketio.connected():
            message = socketio.recv()
            message = [socketio.session.session_id, message]
            socketio.broadcast(message)
        return []

    else:
        start_response("500 Server Error", [("Content-Type", "text/plain")])
        return ["root"]

server = SocketIOServer(('', 8080), app, resource="test")
server.serve_forever()
