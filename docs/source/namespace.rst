.. _namespace_module:

:mod:`socketio.namespace`
=========================

.. automodule:: socketio.namespace

.. autoclass:: BaseNamespace


Namespace initialization
------------------------

     You can override this method:

     .. automethod:: BaseNamespace.initialize

Event flow
----------

This is an attempt at catching the gotchas of the Socket.IO protocol,
which, for historical reasons, sometimes have weird event flow.

The first function to fire is ``initialize()``, which will be called
only if there is an incoming packet for the Namespace.  A successful
javascript call to ``io.connect()`` **is not** sufficient for
``gevent-socketio`` to trigger the creation of a Namespace object.
Some event has to flow from the client to the server.  The connection
will appear to have succeeded from the client's side, but that is
because ``gevent-socketio`` maintains the virtual socket up and running
before it hits your application.  This is why it is a good pratice to
send a packet (often a ``login``, or ``subscribe`` or ``connect`` JSON
event, with ``io.emit()`` in the browser).

If you're using the GLOBAL_NS, the ``recv_connect()`` will not fire on
your namespace, because when the connection is opened, there is no
such packet sent.  The ``connect`` packet is only sent over (and
explicitly sent) by the javascript client when it tries to communicate
with some "non-global" namespaces.  That is why it is recommended to
always use namespaces, to avoid having a different behavior for your
different namespaces. It also makes things explicit in your
application, when you have something such as ``/chat``, or
``/live_data``.  Before a certain version of Socket.IO, there was only
a global namespace, and so this behavior was kept for backwards
compatibility.

Then flows the normal events, back and forth as described elsewhere (elsewhere??).

Upon disconnection, here is what happens: [INSERT HERE the details
flow of disconnection handling, events fired, physical closing of the
connection and ways to terminate a socket, when is the Namespace
killed, the state of the spawn'd processes for each Namespace and each
virtsocket. This really needs to be done, and I'd appreciate having
people investigate this thoroughly]

There you go :)


Namespace instance properties
-----------------------------

     .. attribute:: BaseNamespace.session

       The :term:`session` is a simple ``dict`` that is created with
       each :class:`~socketio.virtsocket.Socket` instance, and is
       copied to each Namespace created under it.  It is a general
       purpose store for any data you want to associated with an open
       :class:`~socketio.virtsocket.Socket`.

     .. attribute:: BaseNamespace.request

       This is the ``request`` object (or really, any object) that you
       have passed as the ``request`` parameter to the
       :func:`~socketio.socketio_manage` function.

     .. attribute:: BaseNamespace.ns_name

       The name of the namespace, like ``/chat`` or the empty string,
       for the "global" namespace.

     .. attribute:: BaseNamespace.environ

       The ``environ`` WSGI dictionary, as it was received upon
       reception of the **first** request that established the virtual
       Socket.  This will never contain the subsequent ``environ`` for
       the next polling, so beware when using cookie-based sessions
       (like Beaker).

     .. attribute:: BaseNamespace.socket

       A reference to the :class:`~socketio.virtsocket.Socket`
       instance this namespace is attached to.

Sending data
------------

     Functions to send data through the socket:

     .. automethod:: BaseNamespace.emit

     .. automethod:: BaseNamespace.send

     .. automethod:: BaseNamespace.error

     .. automethod:: BaseNamespace.disconnect


Dealing with incoming data
--------------------------

     .. automethod:: BaseNamespace.process_event

     You should override this method only if you are not satisfied with the
     automatic dispatching to ``on_``-prefixed methods.  You could then
     implement your own dispatch.  See the source code for inspiration.

     .. automethod:: BaseNamespace.recv_connect

     .. automethod:: BaseNamespace.recv_message

     .. automethod:: BaseNamespace.recv_json

     .. automethod:: BaseNamespace.recv_error

     .. automethod:: BaseNamespace.recv_disconnect


Process management
------------------

     Managing the different callbacks, greenlets and tasks you spawn from
     this namespace:

     .. automethod:: BaseNamespace.spawn

     .. automethod:: BaseNamespace.kill_local_jobs

ACL system
----------

     The ACL system grants access to the different ``on_*()`` and
     ``recv_*()`` methods of your subclass.

     Developers will normally override :meth:`get_initial_acl` to
     return a list of the functions they want to initially open.
     Usually, it will be an ``on_connect`` event handler, that will
     perform authentication and/or authorization, set some variables
     on the Namespace, and then open up the rest of the Namespace
     using :meth:`lift_acl_restrictions` or more granularly with
     :meth:`add_acl_method` and :meth:`del_acl_method`.  It is also
     possible to check these things inside :meth:`initialize` when,
     for example, you have authenticated a Global Namespace object,
     and you want to re-use those credentials or authentication infos
     in a new Namespace:

     .. code-block:: python

         # GLOBAL_NS = ''

         class MyNamespace(BaseNamespace):
             ...
             def initialize(self):
                 self.my_auth = MyAuthObjet()
                 if self.socket[GLOBAL_NS].my_auth.logged_in == True:
                     self.my_auth.logged_in = True

     The content of the ACL is a list of strings corresponding to the full name
     of the methods defined on your subclass, like: ``"on_my_event"`` or
     ``"recv_json"``.

     .. automethod:: BaseNamespace.get_initial_acl

     .. automethod:: BaseNamespace.add_acl_method

     .. automethod:: BaseNamespace.del_acl_method

     .. automethod:: BaseNamespace.lift_acl_restrictions

     .. automethod:: BaseNamespace.reset_acl

     This function is used internally, but can be useful to the developer:

     .. automethod:: is_method_allowed

Low-level methods
-----------------

     Packet dispatching methods. These functions are normally not overriden if
     you are satisfied with the normal dispatch behavior:

     .. automethod:: BaseNamespace.process_packet

     .. automethod:: BaseNamespace.call_method_with_acl

     .. automethod:: BaseNamespace.call_method
