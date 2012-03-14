.. _server_integration:

Server integration layers
=========================

As gevent-socketio runs on top of Gevent, you need a Gevent-based server, to
yield the control cooperatively to the Greenlets in there.

gunicorn
--------

paster
------

pyramid's pserve
----------------

django runserver
----------------


Web server front-ends
=====================

[INSERT THE STATE OF THE DIFFERENT SERVER IMPLEMENTATIONS SUPPORTING WEBSOCKET
FORWARDING]

nginx status

  [gather references to the latest nginx-websocket integration layers]

Apache

using HAProxy to load-balance

