from geventsocketio import SocketIOServer

def app(environ, start_response):
    socketio = environ['socketio']

    if environ['PATH_INFO'].startswith("/normal"):
        start_response("200 OK", [("Content-Type", "text/plain")])
        return ["it works"]

    elif environ['PATH_INFO'].startswith("/socket.io/"):
        if socketio.on_connect():
            socketio.send({'buffer': []})
            socketio.broadcast({'announcement': socketio.session.session_id + ' connected'})
        else:
            while socketio.connected():
                inc_msg = socketio.recv()
                if len(inc_msg) == 1:
                    inc_msg = inc_msg[0]
                    message = {'message': [socketio.session.session_id, inc_msg]}
                    socketio.broadcast(message)

            return []
        #else:
        #    start_response("400 Bad Request", [("Content-Type", "text/plain")])
        #    return ['no socketio connection']

    else:
        start_response("200 OK", [("Content-Type", "text/plain")])
        return ["root"]

server = SocketIOServer(('', 8080), app, resource="socket.io")
server.serve_forever()
