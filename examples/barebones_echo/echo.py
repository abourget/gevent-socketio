from gevent import monkey; monkey.patch_all()

from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace

import htmltag as h

class EchoNamespace(BaseNamespace):

	def recv_disconnect(self):
		self.disconnect(silent=True) # kills all spawned jobs (none, in our case) and removes namespace from socket
		print('Disconnected')

	def on_foo(self, bar, baz):
		print('Got on_foo(bar = "%s", baz = "%s")' % (bar, baz))
		self.emit('echo', bar, baz) # echo it

class Application(object):

	def __call__(self, environ, start_response):
		path = environ['PATH_INFO'].strip('/')

		if not path:
			start_response('200 OK', [('Content-Type', 'text/html')])

			return ['%s%s' % ('<!doctype html>', str(h.html(
					h.head(h.meta(charset = 'UTF-8'), h.title('socketio echo test')),
					h.script(src="/static/jquery-1.6.1.min.js", type="text/javascript"),
					h.script(src="/static/socket.io.js", type="text/javascript"),
					h.script(src="/static/echo.js", type="text/javascript"),
					h.body(
						h.p('''
							This is an echo test for socketio.
							When you enter values for 'bar' and 'baz'
							and push 'emit', they'll be sent over a socket,
							received by the server ('foo()'), and echoed back via
							emitting 'echo' with 'rab' and 'zab'.
							(no HTTP GET or POST is executed!)
							'''),
						h.hr(),
						h.form(
							'bar: ', h.input(type='text', id='bar'), ' ',
							'baz: ', h.input(type='text', id='baz'),
							h.button('Emit', type='submit'),
							id = 'foo'),
						h.hr(),
						h.p(
							# These will get values subbed in via javascript when rab and zab are echoed from server:
							'rab: ', h.span(id = 'rab'), ' ',
							'zab: ', h.span(id = 'zab'))
					)
				)))]

		if path.startswith('static/'):
			try:
				data = open(path).read()
			except Exception:
				return not_found(start_response)

			if path.endswith(".js"):
				content_type = "text/javascript" # we don't have any other types in this simple example, so...
			else:
				return not_found(start_response)

			start_response('200 OK', [('Content-Type', content_type)])
			return [data]

		if path.startswith("socket.io"):
			socketio_manage(environ, {'/echo': EchoNamespace}, {})
		else:
			return not_found(start_response)


def not_found(start_response):
    start_response('404 Not Found', [])
    return ['<h1>Not Found</h1>']


if __name__ == '__main__':
    print 'Listening on port 8080'
    SocketIOServer(('0.0.0.0', 8080), Application(), resource="socket.io", policy_server=False).serve_forever()
