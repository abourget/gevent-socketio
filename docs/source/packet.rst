.. _packet_module:

:mod:`socketio.packet`
======================

The day to day user doesn't need to use this module directly.

The packets used internally (that might be exposed if you override the
``process_packet`` method of your Namespace) are dictionaries, and are different
from a message type to the other.  Here is a list of message types available
in the Socket.IO protocol:

The **connect** packet:

  {"type": "connect",
   "qs": "",
   "endpoint": "/chat"}

The ``qs`` parameter is a query string you can add to the io.connect('/chat?a=b'); calls on the client side.

The **message** packet, equivalent to Socket.IO version 0.6's string message:

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

The **json** packet is like a message, with no name (unlike events) but with
structure JSON data attached.  It is automatically decoded by gevent-socketio.

  {"type": "json",
   "data": {"this": "is a json object"},
   "endpoint": "/chat"}

  {"type": "json",
   "data": {"this": "is a json object", "please": "reply"},
   "ack": True,
   "id": 5,
   "endpoint": "/chat"}

The same ``ack`` mechanics also apply for the ``json`` packet.


The **event** packet holds a ``name`` and some ``args`` as a list.  They are
taken as a list on the browser side (you can ``socket.emit("event", many,
parameters``) in the browser) and passed in as is.

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


The **heartbeat** packet just marks the connection as alive for another amount
of time.

  {"type": "heartbeat",
   "endpoint": ""}

This packet is for the global namespace (or empty namespace).


.. automodule:: socketio.packet
    :members:
    :undoc-members:
    :show-inheritance:
