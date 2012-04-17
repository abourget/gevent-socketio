.. _packet_module:

:mod:`socketio.packet`
======================

The day to day user doesn't need to use this module directly.

The packets used internally (that might be exposed if you override the
:meth:`~socketio.namespace.BaseNamespace.process_packet` method of
your Namespace) are dictionaries, and are different from one message
type to another.

Internal packet types
---------------------

Here is a list of message types available in the
Socket.IO protocol:

The connect packet
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  {"type": "connect",
   "qs": "",
   "endpoint": "/chat"}

The ``qs`` parameter is a query string you can add to the io.connect('/chat?a=b'); calls on the client side.

The **message** packet, equivalent to Socket.IO version 0.6's string message:

.. code-block:: python

  {"type": "message",
   "data": "this is the sent string",
   "endpoint": "/chat"}

  {"type": "message",
   "data": "some message, but please reply",
   "ack": True,
   "id": 5,
   "endpoint": "/chat"}

This last message includes a **msg_id**, and asks for an ack, which you can
reply to with ``self.ack()``, so that the client-side callback is fired upon
reception.

The json packet
~~~~~~~~~~~~~~~

The **json** packet is like a message, with no name (unlike events) but with
structure JSON data attached.  It is automatically decoded by gevent-socketio.

.. code-block:: python

  {"type": "json",
   "data": {"this": "is a json object"},
   "endpoint": "/chat"}

  {"type": "json",
   "data": {"this": "is a json object", "please": "reply"},
   "ack": True,
   "id": 5,
   "endpoint": "/chat"}

The same ``ack`` mechanics also apply for the ``json`` packet.

The event packet
~~~~~~~~~~~~~~~~

The **event** packet holds a ``name`` and some ``args`` as a list.  They are
taken as a list on the browser side (you can ``socket.emit("event", many,
parameters``) in the browser) and passed in as is.

.. code-block:: python

  {"type": "event",
   "endpoint": "/chat",
   "name": "my_event",
   "args": []}

  {"type": "event",
   "endpoint": "/chat",
   "name": "my_event",
   "ack": True,
   "id": 123,
   "args": [{"my": "object"}, 2, "mystring"]}

The same ack semantics apply here as well.

[INSERT: mark the difference between when YOU create the packet, and when
you receive it, and what you must do with it according to different ack values]

The heartbeat packet
~~~~~~~~~~~~~~~~~~~~

The **heartbeat** packet just marks the connection as alive for another amount
of time.

.. code-block:: python

  {"type": "heartbeat",
   "endpoint": ""}

This packet is for the global namespace (or empty namespace).

Ack mechanics
-------------

The client sends a message of the sort:

.. code-block:: python

  {"type": "message",
   "id": 140,
   "ack": True,
   "endpoint": "/tobi",
   "data": ''}

The 'ack' value is 'true', marking that we want an automatic 'ack' when it
receives the packet.  The Node.js version sends the ack itself, without any
server-side code interaction.  It dispatches the packet only after sending back
an ack, so the ack isn't really a reply.  It's just marking the server received
it, but not if the event/message/json was properly processed.

The automated reply from such a request is:

.. code-block:: python

  {"type": "ack",
   "ackId": 140,
   "endpoint": '',
   "args": []}

Where 'ackId' corresponds to the 'id' of the originating message.  Upon
reception of this 'ack' message, the client then looks in an object if there
is a callback function to call associated with this message id (140).  If so,
runs it, otherwise, drops the packet.

There is a second way to ask for an ack, sending a packet like this:

.. code-block:: python

  {"type": "event",
   "id": 1,
   "ack": "data",
   "endpoint": '',
   "name": 'tobi',
   "args": []}

  {"type": "json",
   "id": 1,
   "ack": "data",
   "endpoint": '',
   "data": {"a": "b"}}

and the same goes for a 'message' packet, which has the 'ack' equal to 'data'.
When the server receives such a packet, it dispatches the corresponding event
(either the named event specified in an 'event' type packet, or 'message' or
'json, if the type is so), and *adds* as a parameter, in addition to the
'args' passed by the event (or 'data' for 'message'/'json'), the ack() function
to call (it encloses the packet 'id' already).  Any number of arguments passed
to that 'ack()' function will be passed on to the client-side, and given as
parameter on the client-side function.

That is the returning 'ack' message, with the data ready to be passed as
arguments to the saved callback on the client side:

.. code-block:: python

  {"type": "ack",
   "ackId": 12,
   "endpoint": '',
   "args": ['woot', 'wa']}

To learn more, see the `test_packet.py <https://github.com/abourget/gevent-socketio/blob/master/tests/test_packet.py>`_ test cases.  It also shows the serialization that happens on the wire.


Other module members
--------------------

.. automodule:: socketio.packet
    :members:
    :undoc-members:
    :show-inheritance:
