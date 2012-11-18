.. _server_integration:

Server integration layers
=========================

As gevent-socketio runs on top of Gevent, you need a Gevent-based
server, to yield the control cooperatively to the Greenlets in there.

gunicorn
--------
If you have a python file that includes a WSGI application, for gunicorn
integration all you have to do is include the :mod:`socketio.sgunicorn`

.. code-block:: bash

    gunicorn --worker-class socketio.sgunicorn.GeventSocketIOWorker module:app


paster / Pyramid's pserve
-------------------------


Through Gunicorn
^^^^^^^^^^^^^^^^

Gunicorn will handle workers for you and has other features.

For paster, you just have to define the configuration like this:

.. code-block:: ini

    [server:main]
    use = egg:gunicorn#main
    host = 0.0.0.0
    port = 6543
    workers = 4
    worker_class = socketio.sgunicorn.GeventSocketIOWorker

Directly through gevent
^^^^^^^^^^^^^^^^^^^^^^^

Straight gevent integration is the simplest and has no dependencies.

In your .ini file:

.. code-block:: ini

  [server:main]
  use = egg:gevent-socketio#paster
  host = 0.0.0.0
  port = 6543
  resource = socket.io
  transports = websocket, xhr-polling, xhr-multipart
  policy_server = True
  policy_listener_host = 0.0.0.0
  policy_listener_port = 10843

``policy_listener_host`` defaults to ``host``,
``policy_listener_port`` defaults to ``10843``, ``transports``
defaults to all transports, ``policy_server`` defaults to ``False`` in
here, ``resource`` defaults to ``socket.io``.

So you can have a slimmed-down version:

.. code-block:: ini

  [server:main]
  use = egg:gevent-socketio#paster
  host = 0.0.0.0
  port = 6543



django runserver
----------------
You can either define a wsgi app and launch it with gunicorn:

``wsgi.py``:

.. code-block:: python

    import django.core.handlers.wsgi
    import os

    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    app = django.core.handlers.wsgi.WSGIHandler()

from commandline:

.. code-block:: bash

    gunicorn --worker-class socketio.sgunicorn.GeventSocketIOWorker wsgi:app


or you can use gevent directly:

``run.py``

.. code-block:: python

    #!/usr/bin/env python
    from gevent import monkey
    from socketio.server import SocketIOServer
    import django.core.handlers.wsgi
    import os
    import sys

    monkey.patch_all()

    try:
        import settings
    except ImportError:
        sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
        sys.exit(1)

    PORT = 9000

    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

    application = django.core.handlers.wsgi.WSGIHandler()

    sys.path.insert(0, os.path.join(settings.PROJECT_ROOT, "apps"))

    if __name__ == '__main__':
        print 'Listening on http://127.0.0.1:%s and on port 10843 (flash policy server)' % PORT
        SocketIOServer(('', PORT), application, resource="socket.io").serve_forever()


Databases
=========

Since gevent is a cooperative concurrency library, no process or
routine or library must block on I/O without yielding control to the
``gevent`` hub, if you want your application to be fast and efficient.
Making these libraries compatible with such a concurrency model is
often called `greening`, in reference to `Green threads
<http://en.wikipedia.org/wiki/Green_threads>`_.



You will need `green`_ databases APIs to gevent to work correctly. See:

 * MySQL:
   * PyMySQL https://github.com/petehunt/PyMySQL/
 * PostgreSQL:
   * psycopg2 http://initd.org/psycopg/docs/advanced.html#index-8
   * psycogreen https://bitbucket.org/dvarrazzo/psycogreen/src



Web server front-ends
=====================

If your web server does not support websockets, you will not be able
to use this transport, although the other transports may
work. However, this would diminish the value of using real-time
communications.

The websocket implementation in the different web servers is getting
better every day, but before investing too much too quickly, you might
want to have a look at your web server's status on the subject.

[INSERT THE STATE OF THE DIFFERENT SERVER IMPLEMENTATIONS SUPPORTING WEBSOCKET
FORWARDING]

nginx status

  [gather references to the latest nginx-websocket integration layers]

Apache

Using HAProxy to load-balance

