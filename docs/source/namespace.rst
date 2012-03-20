.. _namespace_module:

:mod:`socketio.namespace`
=========================

.. automodule:: socketio.namespace

  .. autoclass:: BaseNamespace

     **Namespace initialization**

     You can override this method:

     .. automethod:: initialize


     **Sending data**

     Functions to send data through the socket:

     .. automethod:: emit

     .. automethod:: send

     .. automethod:: error

     .. automethod:: disconnect


     **Dealing with incoming data**

     .. automethod:: process_event

     You should override this method only if you are not satisfied with the
     automatic dispatching to ``on_``-prefixed methods.  You could then
     implement your own dispatch.  See the source code for inspiration.

     .. automethod:: recv_connect

     .. automethod:: recv_message

     .. automethod:: recv_json

     .. automethod:: recv_error

     .. automethod:: recv_disconnect


     **Process management**

     Managing the different callbacks, greenlets and tasks you spawn from
     this namespace:

     .. automethod:: spawn

     .. automethod:: kill_local_jobs


     **ACL system**

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

     .. automethod:: get_initial_acl

     .. automethod:: add_acl_method

     .. automethod:: del_acl_method

     .. automethod:: lift_acl_restrictions

     .. automethod:: reset_acl

     This function is used internally, but can be useful to the developer:
     
     .. automethod:: is_method_allowed


     **Low-level methods**

     Packet dispatching methods. These functions are normally not overriden if
     you are satisfied with the normal dispatch behavior:     

     .. automethod:: process_packet
     
     .. automethod:: call_method_with_acl

     .. automethod:: call_method
