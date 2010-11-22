from geventsocketio import SocketIOServer

def app(environ, start_response):
    socketio = environ['socketio']

    if environ['PATH_INFO'].startswith("/normal"):
        start_response("200 OK", [("Content-Type", "text/plain")])
        return ["it works"]

    elif environ['PATH_INFO'].startswith("/socket.io/"):
        socketio.send({'buffer': []})
        socketio.broadcast({'announcement': socketio.session.session_id + ' connected'})

        while socketio.connected():
            message = socketio.recv()
            message = {'message': [socketio.session.session_id, message[0]]}
            socketio.broadcast(message)
        return []

    else:
        start_response("200 OK", [("Content-Type", "text/plain")])
        return ["root"]

server = SocketIOServer(('', 8080), app, resource="socket.io")
server.serve_forever()
