==================================
gevent-socketio cross-site example
==================================

This example app demonstrates that you can use socket.io (0.9)
connections from hosts other than the origin host with
gevent-socketio.

To run the example, first install set up your gevent-socketio
development environment, then install the example's requirements
into the same virtualenv by running::

  pip install -r requirements.txt

in this directory. Then in two separate shells, start ``web.py`` and
``sock.py``::

  python web.py

Then in shell two::

  python sock.py

The two servers run on different ports, simulating a common case where
the main web application is running on one host and the socket.io
server is running on a separate host.

When both are running, navigate to http://localhost:8080/ and
follow the directions that appear there to see cross-site socket.io
in action.

socket.io.js 0.8 vs 0.9
-----------------------

Note that socket.io.js 0.8 works with gevent-socketio for cross-origin requests
without any special headers in the handshake phase. But socket.io.js
0.9 makes a change to how it sends the XHR handshake request: it sets
``withCredentials = true``, which requires that the socket.io server
return an ``Access-Control-Allow-Origin`` header that mentions the
origin server.
