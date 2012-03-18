.. _mixins_module:

:mod:`socketio.mixins`
======================

The source code is shown here since you will probably want to write
your own mixins to do some real job.  The two provided mixins are generally
useful for small projects, but you will probably want to implement some
message-queue aware Mixins:

You find these in the ``socketio.mixins`` package:

.. automodule:: socketio.mixins

.. literalinclude:: ../../socketio/mixins.py
   :pyobject: BroadcastMixin

.. literalinclude:: ../../socketio/mixins.py
   :pyobject: RoomsMixin
