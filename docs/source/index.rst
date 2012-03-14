.. gevent-socketio documentation master file, created by
   sphinx-quickstart on Tue Mar 13 20:43:40 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Gevent-socketio documentation
=============================

.. toctree::
   :maxdepth: 2

Introduction
------------

This is what, real-time web, blah blah blah..

What is allows us to do.  Framework agnostic...

Concepts
--------

Namespace, Socket, fallbacks (links to the Socket.IO docs)

Getting started
---------------

Just copy this and you,re ready

See this doc for different servers integration:

  :ref:`server_integration`

Examples
--------

Links to examples

API docs
--------

**Namespaces** are the main interface the developer is going to use.  You mostly 
define your own BaseNamespace derivatives, and gevent-socketio maps the incoming
messages to your methods automatically:

  :mod:`socketio.namespace`

**Mixins** are components you can add to your namespaces, to provided added
functionality.

  :mod:`socketio.mixins`

**Sockets** are the virtual tunnels that are established and abstracted by the
different Transports.  They basically expose socket-like send/receive
functionality to the Namespace objects.  Even when we use long-polling
transports, only one Socket is created per browser.

  :mod:`socketio.virtsocket`

**Packet** is a library that handle the decoding of the messages encoded in the
Socket.IO dialect.  They take dictionaries for encoding, and return decoded
dictionaries also.

  :mod:`socketio.packet`

**Handler** is a lower-level transports handler.  It is responsible for calling
your WSGI application

  :mod:`socketio.handler`

**Transports** are responsible for translating the different fallback mechanisms
to one abstracted Socket, dealing with payload encoding, multi-message
multiplexing and their reverse operation.

  :mod:`socketio.transports`

**Server** is the component used to hook Gevent and its WSGI server to the
WSGI app to be served, while dispatching any Socket.IO related activities to
the `handler` and the `transports`.

  :mod:`socketio.server`

Auto-generated indexes:

* :ref:`genindex`
* :ref:`modindex`


References
----------

LearnBoost's node.js version is the reference implementation, you can find the
server component at this address:

  https://github.com/learnboost/socket.io

The client JavaScript library's development branch is here:

  https://github.com/LearnBoost/socket.io-client

The specifications to the protocol are somehow in this repository:

  https://github.com/LearnBoost/socket.io-spec

This is the original wow-website:

  http://socket.io

Here is a list of the different frameworks integration to date, although not all
have upgraded to the latest version of gevent-socketio:

  pyramid_socketio: https://github.com/abourget/pyramid_socketio
  django-socketio: https://github.com/stephenmcd/django-socketio

The Flask guys will be working on an integration layer soon.


Credits
-------

**Jeffrey Gellens** for starting and polishing this project over the years.

PyCon 2012 and the Sprints, for bringing this project up to version 0.9 of the protocol.

Contributors:

 * Denis Bilenko
 * Bobby Powers
 * Lon Ingram
 * Eugene Baumstein
 * John Anderson
 * Sébastien Béal
 * Alexandre Bourget



Todo
----

Document the on_methods() and their parameters, how you use them on the
client-side and how they are mapped to the server-side.

How would we attach some informatio to the "socket", where to attach persistent information, when to attach to a namespace, when on the socket.

How to integrate your framework's "session" object (Beaker, memcached, or file-based).  Beware: monsters behind your back.
