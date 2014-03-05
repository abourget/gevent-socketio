Caution!!!
============

This is an experimental fork of ``gevent-socketio`` that adds support for 
pluggable backends to create and manage the lifecycle of sockets across multiple 
workers and implements a Redis-based version of such a backend.

There are significant changes to the original code and it won't be 
backward-compatible with existing projects. However it should be relatively 
trivial to switch, if you know what you are doing.

Presentation
============

.. image:: https://secure.travis-ci.org/abourget/gevent-socketio.png?branch=master

``gevent-socketio`` is a Python implementation of the Socket.IO
protocol, developed originally for Node.js by LearnBoost and then
ported to other languages.  Socket.IO enables real-time web
communications between a browser and a server, using a WebSocket-like
API.  One aim of this project is to provide a single ``gevent``-based
API that works across the different WSGI-based web frameworks out
there (Pyramid, Pylons, Flask, web2py, Django, etc...).  Only ~3 lines
of code are required to tie-in ``gevent-socketio`` in your framework.
Note: you need to use the ``gevent`` python WSGI server to use
``gevent-socketio``.


Technical overview
==================

Most of the ``gevent-socketio`` implementation is pure Python.  There
is an obvious dependency on ``gevent``, and another on
``gevent-websocket``.  There are integration examples for Pyramid, Flask,
Django and BYOF (bring your own framework!).


Documentation and References
============================

You can read the renderered Sphinx docs at:

* http://readthedocs.org/docs/gevent-socketio/en/latest/

Discussion and questions happen on the mailing list:

* https://groups.google.com/forum/#!forum/gevent-socketio

or in the Github issue tracking:

* https://github.com/abourget/gevent-socketio/issues

You can also contact the maintainer:

* https://twitter.com/#!/bourgetalexndre
* https://plus.google.com/109333785244622657612


Installation
============

You can install with standard Python methods::

   pip install gevent-socketio

or from source::

   git clone git://github.com/abourget/gevent-socketio.git
   cd gevent-socketio
   python setup.py install

For development, run instead of ``install``::

   python setup.py develop

If you want to do all of that in a virtualenv, run::

   virtualenv env
   . env/bin/activate
   python setup.py develop   # or install

