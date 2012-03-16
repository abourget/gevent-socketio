.. _server_integration:

Server integration layers
=========================

As gevent-socketio runs on top of Gevent, you need a Gevent-based server, to
yield the control cooperatively to the Greenlets in there.

gunicorn
--------
If you have a python file that includes a WSGI application, for gunicorn
integration all you have to do is include the :mod:`socketio.sgunicorn`

.. code-block:: bash

    gunicorn --worker-class socketio.sgunicorn.GeventSocketIOWorker module:app


paster
------
For paster, you just have to define the configuration like this:

.. code-block:: ini

    [server:main]
    use = egg:gunicorn#main
    host = 0.0.0.0
    port = 6543
    workers = 4
    worker_class = socketio.gunicorn.GeventSocketIOWorker

pyramid's pserve
----------------
Same as paster.

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
    from socketio import SocketIOServer
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
        print 'Listening on http://127.0.0.1:%s and on port 843 (flash policy server)' % PORT
        SocketIOServer(('', PORT), application, namespace="socket.io").serve_forever()


Databases
=========

You will need `green`_ databases APIs to gevent to work correctly. See:

 * pymsysql
 * psycopg2 http://initd.org/psycopg/docs/advanced.html#index-8



Web server front-ends
=====================

[INSERT THE STATE OF THE DIFFERENT SERVER IMPLEMENTATIONS SUPPORTING WEBSOCKET
FORWARDING]

nginx status

  [gather references to the latest nginx-websocket integration layers]

Apache

using HAProxy to load-balance

