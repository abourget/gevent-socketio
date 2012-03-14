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

Examples
--------

Links to examples

API docs
--------

**Namespaces** are the main interface the developer is going to use.  You mostly 
define your own BaseNamespace derivatives, and gevent-socketio maps the incoming
messages to your methods automatically:

  :ref:`socketio.namespace`

**Mixins** are components you can add to your namespaces, to provided added
functionality.

  :ref:`socketio.mixins`

**Sockets** are the virtual tunnels that are established and abstracted by the
different Transports.  They basically expose socket-like send/receive
functionality to the Namespace objects.  Even when we use long-polling
transports, only one Socket is created per browser.

  :ref:`socketio.virtsocket`

**Packet** is a library that handle the decoding of the messages encoded in the
Socket.IO dialect.  They take dictionaries for encoding, and return decoded
dictionaries also.

  :ref:`socketio.packet`

**Handler** is a lower-level transports handler.  It is responsible for calling
your WSGI application

  :ref:`socketio.handler`

**Transports** are responsible for translating the different fallback mechanisms
to one abstracted Socket, dealing with payload encoding, multi-message
multiplexing and their reverse operation.

  :ref:`socketio.transports`

**Server** is the component used to hook Gevent and its WSGI server to the
WSGI app to be served, while dispatching any Socket.IO related activities to
the `handler` and the `transports`.

  :ref:`socketio.server`

Auto-generated indexes:

* :ref:`genindex`
* :ref:`modindex`


References
----------

Links to the node.js implementation
Links to the Socket.IO specs
Link to other implementations and the different frameworks that implement it.


Credits
-------

PyCon 2012 and the Sprints!



Todo
----

Document the on_methods() and their parameters, how you use them on the
client-side and how they are mapped to the server-side.

How would we attach some informatio to the "socket", where to attach persistent information, when to attach to a namespace, when on the socket.

How to integrate your framework's "session" object (Beaker, memcached, or file-based).  Beware: monsters behind your back.
