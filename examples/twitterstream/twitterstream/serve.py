from gevent import monkey; monkey.patch_all()
import gevent
import tweetstream
import getpass

from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace


def broadcast_msg(server, ns_name, event, *args):
    pkt = dict(type="event",
               name=event,
               args=args,
               endpoint=ns_name)

    for sessid, socket in server.sockets.iteritems():
        socket.send_packet(pkt)


def send_tweets(server, user, password):
    stream = tweetstream.SampleStream(user, password)
    for tweet in stream:
        broadcast_msg(server, '/tweets', 'tweet', tweet)


def get_credentials():
    user = raw_input("Twitter username: ")
    password = getpass.getpass("Twitter password: ")
    return (user, password)


class Application(object):
    def __init__(self):
        self.buffer = []

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO'].strip('/') or 'index.html'

        if path.startswith('static/') or path == 'index.html':
            try:
                data = open(path).read()
            except Exception:
                return not_found(start_response)

            if path.endswith(".js"):
                content_type = "text/javascript"
            elif path.endswith(".css"):
                content_type = "text/css"
            elif path.endswith(".swf"):
                content_type = "application/x-shockwave-flash"
            else:
                content_type = "text/html"

            start_response('200 OK', [('Content-Type', content_type)])
            return [data]

        if path.startswith("socket.io"):
            socketio_manage(environ, {'/tweets': BaseNamespace})
        else:
            return not_found(start_response)


def not_found(start_response):
    start_response('404 Not Found', [])
    return ['<h1>Not Found</h1>']


if __name__ == '__main__':
    user, password = get_credentials()
    print 'Listening on port http://0.0.0.0:8080 and on port 10843 (flash policy server)'
    server = SocketIOServer(('0.0.0.0', 8080), Application(),
        resource="socket.io", policy_server=True,
        policy_listener=('0.0.0.0', 10843))
    gevent.spawn(send_tweets, server, user, password)
    server.serve_forever()
