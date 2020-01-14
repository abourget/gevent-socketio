from socketio.server import SocketIOServer
from pyramid.paster import get_app
from gevent import monkey; monkey.patch_all()

if __name__ == '__main__':

    app = get_app('development.ini')
    print 'Listening on port http://0.0.0.0:8080 and on port 10843 (flash policy server)'

    SocketIOServer(('0.0.0.0', 8080), app,
        resource="socket.io", policy_server=True,
        policy_listener=('0.0.0.0', 10843)).serve_forever()
