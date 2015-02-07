This is a barebones "echo" example.  It uses no css,
no flash (websocket), no magic javascript, and the
bare minimum in dependencies.

It's intended for one who is getting started, and
wants to understand the skeleton, and minimal lines
of code, to make socketio work.

There are only 2 short, main files: echo.py, and echo.js.
echo.py creates the SocketIOServer and provides a short
class, "Application", which is the basic web app, which
serves the front-page HTML (in-line, since it's short)
and calls socketio_manage() to run the BaseNamespace-
derived socket handler.  SocketIOServer, BaseNamespace,
and socketio_manage() are the only real dependencies,
each with only 1 line of code, really, to make the whole
thing go.

The web page asks a user to type values for bar and baz.
When the "submit" button is pushed, an HTTP transaction
is _not_ performed; rather, the bit of code in echo.js
arrests the process and sends a socketio message, instead,
to foo(bar, baz), which is handled back in echo.py, with
on_foo(self, bar, baz), a function of the BaseNamespace-
derived class.

That's it!  This example depends only on socketio (of
course) and jquery.